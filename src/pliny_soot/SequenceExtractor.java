/* Author: Vijay Murali */

package pliny_soot;

import java.util.*;
import java.io.*;
import soot.*;

import soot.toolkits.graph.UnitGraph;
import soot.toolkits.graph.BriefUnitGraph;

import soot.jimple.Stmt;
import soot.jimple.GotoStmt;
import soot.jimple.InvokeStmt;
import soot.jimple.ReturnStmt;
import soot.jimple.ReturnVoidStmt;
import soot.jimple.ThrowStmt;
import soot.jimple.InvokeExpr;
import soot.jimple.InstanceInvokeExpr;

import soot.jimple.toolkits.callgraph.CallGraph;
import soot.jimple.toolkits.callgraph.Edge;

/** The sequence extractor, implemented as a SceneTransformer */
public class SequenceExtractor extends BodyTransformer
{
    /** List of paths explored */
    private List<Path> paths;

    /** List of property automata */
    private List<PropertyAutomaton> properties;

    /** Call stack */
    private Stack<CallContext> callStack;

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
        callStack = new Stack<CallContext>();
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
            Sequence seq = new Sequence();
            Path path = new Path();
            try {
                extractSequence(head, cfg, seq, path);
            } catch (SequenceLengthException e) {
                System.err.println("too big sequence");
            } catch (TimeoutException e) {
                System.err.println("TIMEOUT");
            } catch (SequenceExtractorException e) {
                System.err.println("uncaught exception");
                System.exit(1);
            } catch (StackOverflowError e) {
                System.err.println("infinite loop"); /* most likely */
                callStack.clear();
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

    private void extractSequence(Unit stmt, UnitGraph cfg, Sequence seq, Path path)
            throws SequenceExtractorException {
        extractSequence(stmt, cfg, seq, path, true);
    }

    private void extractSequence(Unit ustmt, UnitGraph cfg, Sequence seq, Path path, boolean invokeCheck)
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

        /* Update all property automata for this stmt */
        PropertyAutomaton.apply(stmt);
        for (PropertyAutomaton p : properties)
            p.post(stmt);

        if (invokeCheck && stmt.containsInvokeExpr()) {
            handleInvoke(stmt, cfg, seq, path); /* mutually recursive */
            return;
        }

        List<Unit> succs = cfg.getSuccsOf(stmt);

        if (isReturnOrThrow(stmt)) {
            assert succs.size() == 0 : "more than one succ for return or throw";
            if (callStack.empty())
                handleTerminal(seq, path);
            else {
                CallContext context = callStack.pop();
                extractSequence(context.getStmt(), context.getCfg(), seq, path, false);
            }

            return;
        }

        assert succs.size() > 0 : "empty succs list when stmt is not a return or throw";
        Unit succ = succs.get(rng.nextInt(succs.size())); /* pick a random successor */
        assert succ != null : "succ is null";
        if (succs.size() > 1) /* record choice point along path */
            path.addChoicePoint(succ);
        extractSequence(succ, cfg, seq, path);
    }

    private void handleInvoke(Stmt stmt, UnitGraph cfg, Sequence seq, Path path)
            throws SequenceExtractorException {
        InvokeExpr invokeExpr = stmt.getInvokeExpr();
        SootMethod callee = invokeExpr.getMethod();

        if (Util.isAndroidMethod(callee)) {
            handleInvokeAndroid(invokeExpr, seq);
            extractSequence(stmt, cfg, seq, path, false);
        }
        else if (appMethods.contains(callee)) { /* step into callee */
            Body body = callee.retrieveActiveBody();
            UnitGraph calleeCfg = new BriefUnitGraph(body);
            Unit head = body.getUnits().getFirst();

            callStack.push(new CallContext(stmt, cfg));
            if (! methodsAnalyzed.contains(callee)) {
                methodsAnalyzed.add(callee);
                totalLOC += body.getUnits().size();
            }
            extractSequence(head, calleeCfg, seq, path);
        }
        else /* step over */
            extractSequence(stmt, cfg, seq, path, false);
    }

    private void handleTerminal(Sequence seq, Path path) throws SequenceExtractorException {
        if (seq.count() == 0)
            return;
        if (paths.contains(path))
            return;
        paths.add(path);

        numSequences += seq.count();
        seq.print(outfile);
    }

    private void handleInvokeAndroid(InvokeExpr invokeExpr, Sequence seq) {
        if (! (invokeExpr instanceof InstanceInvokeExpr)) /* don't include static methods */
            return;

        InstanceInvokeExpr inst = (InstanceInvokeExpr) invokeExpr;
        TypeStateObject t = new TypeStateObject(inst.getBase());

        List<PropertyState> ps = new ArrayList<PropertyState>();
        for (PropertyAutomaton p : properties)
            ps.add(p.getState());

        Event e = new Event(invokeExpr.getMethod(), ps);

        if (seq.containsTypeStateObject(t))
            seq.addEvent(t, e);

        else if (t.isMyTypeState()) {
            seq.addTypeStateObject(t);
            seq.addEvent(t, e);
        }
    }

    private boolean isReturnOrThrow(Stmt stmt) {
        return stmt instanceof ReturnStmt || stmt instanceof ReturnVoidStmt|| stmt instanceof ThrowStmt;
    }

    public void addPropertyAutomaton(PropertyAutomaton p) {
        properties.add(p);
    }
}
