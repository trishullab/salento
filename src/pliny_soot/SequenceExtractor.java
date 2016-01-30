/* Author: Vijay Murali */

package pliny_soot;

import java.util.*;
import java.io.*;
import soot.*;

import soot.toolkits.graph.UnitGraph;
import soot.toolkits.graph.BriefUnitGraph;

import soot.jimple.Stmt;
import soot.jimple.AssignStmt;
import soot.jimple.GotoStmt;
import soot.jimple.InvokeStmt;
import soot.jimple.ReturnStmt;
import soot.jimple.ReturnVoidStmt;
import soot.jimple.ThrowStmt;
import soot.jimple.InvokeExpr;
import soot.jimple.InstanceInvokeExpr;
import soot.jimple.StaticInvokeExpr;

import soot.jimple.toolkits.callgraph.CallGraph;
import soot.jimple.toolkits.callgraph.Edge;

/** The sequence extractor, implemented as a SceneTransformer */
public class SequenceExtractor extends BodyTransformer
{
    /** List of paths explored */
    private List<Path> paths;

    /** List of property automata.
     *  Properties are actually associated only with typestate.
     *  This variable exists just to avoid reading the properties file
     *  each time a typestate is encountered */
    private List<PropertyAutomaton> properties;

    /** Return point stack */
    private Stack<CallContext> returnStack;

    /** All application methods, used to check if we should add an invocation
     * to the sequence (API) or step into it (application) */
    private List<SootMethod> appMethods;

    /** Number of sequences from each typestate object */
    private int numSequences;

    /** Total number of sequences */
    private int totalSequences;

    /** Total number of LOC */
    private int totalLOC;

    /** The output file */
    private PrintStream outfile;

    /** Start time for this method */
    private long startTime;

    /** Methods encountered (for LOC count) */
    private List<SootMethod> methodsAnalyzed;

    private Random rng;

    class SequenceExtractorException extends Exception {}
    class SequenceLengthException extends SequenceExtractorException {}
    class TimeoutException extends SequenceExtractorException {}


    public SequenceExtractor() {
        totalSequences = 0;
        totalLOC = 0;
        paths = new ArrayList<Path>();
        returnStack = new Stack<CallContext>();
        methodsAnalyzed = new ArrayList<SootMethod>();
        properties = new ArrayList<PropertyAutomaton>();
        rng = new Random(System.currentTimeMillis());
        outfile = System.out;
    }

    public void setupOutput(File f) {
        try {
            this.outfile = new PrintStream(f);
        } catch (FileNotFoundException e) {
            System.err.println("Cannot create writable file " + f + ":" + e.getMessage());
            System.exit(1);
        }
    }

    public void setupProperties(File f) {
        try {
            this.properties = PropertyAutomaton.readProperties(f);
        } catch (FileNotFoundException e) {
            System.err.println("Cannot read properties file " + f + ":" + e.getMessage());
            System.exit(1);
        } catch (IOException e) {
            System.err.println("IO Error occurred:" + e.getMessage());
            System.exit(1);
        }
    }

    public void setupTypestates(File f) {
        try {
            Options.myTypestates = Util.readFileToList(f);
        } catch (FileNotFoundException e) {
            System.err.println("Cannot read typestates file " + f + ":" + e.getMessage());
            System.exit(1);
        } catch (IOException e) {
            System.err.println("IO Error occurred:" + e.getMessage());
            System.exit(1);
        }
    }

    @Override
    protected void internalTransform(Body body, String phaseName, Map options) {
        SootMethod method = body.getMethod();

        if (! Util.isAndroidEntryPoint(method))
            return;

        totalLOC += body.getUnits().size();
        appMethods = EntryPoints.v().methodsOfApplicationClasses();
        System.out.println("Extracting sequences from " + Util.mySignature(method));

        numSequences = 0;
        outfile.println("# " + Util.mySignature(method));

        UnitGraph cfg = new BriefUnitGraph(body);
        Unit head = body.getUnits().getFirst();

        for (int i = 0; i < Options.MAX_SEQS; i++) {
            startTime = System.currentTimeMillis() / 1000L;
            Path path = new Path();
            List<TypeStateObject> tos = new ArrayList<TypeStateObject>();
            try {
                extractSequence(head, cfg, path, tos);
            } catch (SequenceLengthException e) {
                System.err.println("too big sequence");
            } catch (TimeoutException e) {
                System.err.println("TIMEOUT");
            } catch (SequenceExtractorException e) {
                System.err.println("uncaught exception");
                System.exit(1);
            } catch (StackOverflowError e) {
                System.err.println("infinite loop"); /* most likely */
                returnStack.clear();
                break;
            }
        }

        if (numSequences > 0) {
            totalSequences += numSequences;
            System.out.println("Sub total sequences: " + numSequences);

            System.out.println("Total sequences: " + totalSequences);
            System.out.println("Total LOC: " + totalLOC);
        }
    }

    private void extractSequence(Unit stmt, UnitGraph cfg, Path path, List<TypeStateObject> tos)
            throws SequenceExtractorException {
        extractSequence(stmt, cfg, path, tos, true);
    }

    private void extractSequence(Unit ustmt, UnitGraph cfg, Path path, List<TypeStateObject> tos, 
            boolean invokeCheck)
        throws SequenceExtractorException {
        /* misbehaving cases */
        if (System.currentTimeMillis() / 1000L - startTime > 5)
            throw new TimeoutException();

        Stmt stmt;
        try {
            /* since we are in jimple this cast should be safe */
            stmt = (Stmt) ustmt;
        } catch (ClassCastException e) {
            System.err.println(e.getMessage());
            throw e;
        }

        /* Update global info for properties */
        PropertyAutomaton.apply(stmt);

        if (invokeCheck && stmt.containsInvokeExpr()) {
            handleInvoke(stmt, cfg, path, tos); /* mutually recursive */
            return;
        }

        List<Unit> succs = cfg.getSuccsOf(stmt);

        if (isReturnOrThrow(stmt)) {
            assert succs.size() == 0 : "more than one succ for return or throw";
            if (returnStack.empty())
                handleTerminal(path, tos);
            else {
                CallContext context = returnStack.pop();
                extractSequence(context.getStmt(), context.getCfg(), path, tos, false);
            }

            return;
        }

        assert succs.size() > 0 : "empty succs list when stmt is not a return or throw";
        Unit succ = succs.get(rng.nextInt(succs.size())); /* pick a random successor */
        assert succ != null : "succ is null";
        if (succs.size() > 1) /* record choice point along path */
            path.addChoicePoint(succ);
        extractSequence(succ, cfg, path, tos);
    }

    private void handleInvoke(Stmt stmt, UnitGraph cfg, Path path, List<TypeStateObject> tos)
            throws SequenceExtractorException {
        InvokeExpr invokeExpr = stmt.getInvokeExpr();
        SootMethod callee = invokeExpr.getMethod();

        if (Util.isAndroidMethod(callee)) {
            handleInvokeAndroid(stmt, tos, cfg.getBody().getMethod());
            extractSequence(stmt, cfg, path, tos, false);
        }
        else if (appMethods.contains(callee)) { /* step into callee */
            Body body = callee.retrieveActiveBody();
            UnitGraph calleeCfg = new BriefUnitGraph(body);
            Unit head = body.getUnits().getFirst();

            returnStack.push(new CallContext(stmt, cfg));
            if (! methodsAnalyzed.contains(callee)) {
                methodsAnalyzed.add(callee);
                totalLOC += body.getUnits().size();
            }
            extractSequence(head, calleeCfg, path, tos);
        }
        else /* step over */
            extractSequence(stmt, cfg, path, tos, false);
    }

    private void handleTerminal(Path path, List<TypeStateObject> tos) throws SequenceExtractorException {
        if (paths.contains(path))
            return;
        paths.add(path);

        numSequences += tos.size();
        for (TypeStateObject t : tos)
            if (t.isValidTypeState())
                outfile.println(t.getYoungestNonAppParent() + "#" + t.getHistory());
    }

    private void handleInvokeAndroid(Stmt stmt, List<TypeStateObject> tos, SootMethod currMethod) {
        InvokeExpr invokeExpr = stmt.getInvokeExpr();

        Value v;
        if (invokeExpr instanceof InstanceInvokeExpr)
            v = ((InstanceInvokeExpr) invokeExpr).getBase();
        else if (invokeExpr instanceof StaticInvokeExpr && stmt instanceof AssignStmt
                    && ((AssignStmt) stmt).getLeftOp().getType() instanceof RefType)
            v = ((AssignStmt) stmt).getLeftOp();
        else
            return; /* don't include static methods that don't return anything stored to an object */
        
        TypeStateObject t = null;
        for (TypeStateObject t1 : tos)
            if (t1.getObject().equals(v)) {
                t = t1;
                break;
            }

        if (t == null) { /* first time encountering this typestate */
            t = new TypeStateObject(v, getPropertiesClone());
            if (!t.isMyTypeState())
                return;
            tos.add(t);
        }

        List<PropertyState> ps = new ArrayList<PropertyState>();
        for (PropertyAutomaton p : t.getProperties()) {
            p.post(stmt);
            ps.add(p.getState());
        }

        LocationInfo location = new LocationInfo(stmt, currMethod);

        Event e = new Event(invokeExpr.getMethod(), ps, location);
        t.getHistory().addEvent(e);
    }

    private boolean isReturnOrThrow(Stmt stmt) {
        return stmt instanceof ReturnStmt || stmt instanceof ReturnVoidStmt|| stmt instanceof ThrowStmt;
    }

    /** Returns a clone of the properties -- does not clone transitions since they are fixed */
    private List<PropertyAutomaton> getPropertiesClone() {
        List<PropertyAutomaton> ps = new ArrayList<PropertyAutomaton>();
        for (PropertyAutomaton p : properties) {
            PropertyAutomaton pClone = new PropertyAutomaton(p.getTransitions());
            ps.add(pClone);
        }
        return ps;
    }
}
