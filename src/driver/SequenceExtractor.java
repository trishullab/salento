/* Author: Vijay Murali */

package driver;

import java.util.*;
import java.io.*;
import soot.*;

import soot.toolkits.graph.UnitGraph;
import soot.toolkits.graph.BriefUnitGraph;
import soot.toolkits.graph.TrapUnitGraph;

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

import com.google.gson.*;
import com.google.gson.annotations.Expose;

/** The sequence extractor, implemented as a SceneTransformer */
public class SequenceExtractor extends BodyTransformer
{
    /** List of paths explored */
    private List<Path> paths;

    /** List of monitor automata.
     *  Monitors are actually associated only with typestate.
     *  This variable exists just to avoid reading the monitors file
     *  each time a typestate is encountered */
    private List<Monitor> monitors;

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

    /** List of sequences */
    @Expose
    private List<History> data;

    private Random rng;

    class SequenceExtractorException extends Exception {}
    class SequenceLengthException extends SequenceExtractorException {}
    class TimeoutException extends SequenceExtractorException {}

    /** Gson serializer */
    private Gson gson;

    public SequenceExtractor() {
        totalSequences = 0;
        totalLOC = 0;
        paths = new ArrayList<Path>();
        returnStack = new Stack<CallContext>();
        methodsAnalyzed = new ArrayList<SootMethod>();
        monitors = new ArrayList<Monitor>();
        rng = new Random(System.currentTimeMillis());
        outfile = System.out;
        data = new ArrayList<History>();
        gson = new GsonBuilder().setPrettyPrinting().
            excludeFieldsWithoutExposeAnnotation().create();
    }

    public void setupOutput(File f) {
        try {
            this.outfile = new PrintStream(f);
        } catch (FileNotFoundException e) {
            System.err.println("Cannot create writable file " + f + ":" + e.getMessage());
            System.exit(1);
        }
    }

    public void setupMonitors(File f) {
        try {
            this.monitors = Monitor.readMonitors(f);
        } catch (FileNotFoundException e) {
            System.err.println("Cannot read monitors file " + f + ":" + e.getMessage());
            System.exit(1);
        } catch (IOException e) {
            System.err.println("IO Error occurred:" + e.getMessage());
            System.exit(1);
        }
    }

    public void setupTypestates(File f) {
        try {
            Options.relevantTypestates = Util.readFileToList(f);
        } catch (FileNotFoundException e) {
            System.err.println("Cannot read typestates file " + f + ":" + e.getMessage());
            System.exit(1);
        } catch (IOException e) {
            System.err.println("IO Error occurred:" + e.getMessage());
            System.exit(1);
        }
    }

    /** Include anything that needs to be done before beginning soot */
    public void begin() {

    }

    /** Include anything that needs to be done after soot ends */
    public void end() {
        if (Options.printJSON)
            outfile.println(gson.toJson(this));
    }

    @Override
    protected void internalTransform(Body body, String phaseName, Map options) {
        if (! Util.isRelevantApp()) {
            System.out.println("Irrelevant app");
            System.exit(1);
        }

        SootMethod method = body.getMethod();
        String clsName = method.getDeclaringClass().getName();
        if (clsName.startsWith("android.") || clsName.startsWith("com.google."))
            return;

        if (Options.obeyAndroidEntryPoints && ! Util.isAndroidEntryPoint(method))
            return;

        totalLOC += body.getUnits().size();
        appMethods = EntryPoints.v().methodsOfApplicationClasses();
        System.out.println("Extracting sequences from " + Util.mySignature(method));

        numSequences = 0;
        //outfile.println("# " + Util.mySignature(method));

        UnitGraph cfg = generateUnitGraph(body);
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

        /* Update global info for monitors */
        Monitor.apply(stmt);

        if (invokeCheck && stmt.containsInvokeExpr()) {
            handleInvoke(stmt, cfg, path, tos); /* mutually recursive */
            return;
        }

        List<Unit> succs = cfg.getSuccsOf(stmt);

        if (isReturn(stmt) || (stmt instanceof ThrowStmt && succs.size() == 0)) {
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
        if (succs.size() > 1) { /* record choice point along path, and add branch event to all histories */
            path.addChoicePoint(succ);
            if (Options.printBranches) {
                Integer numBranches = succs.size();
                for (TypeStateObject t : tos)
                    t.getHistory().addEvent(new Event(numBranches));
            }
        }
        extractSequence(succ, cfg, path, tos);
    }

    private void handleInvoke(Stmt stmt, UnitGraph cfg, Path path, List<TypeStateObject> tos)
            throws SequenceExtractorException {
        InvokeExpr invokeExpr = stmt.getInvokeExpr();
        SootMethod callee = invokeExpr.getMethod();
        Stmt succ;

        if ((succ = handleInvokeRelevant(stmt, cfg, path, tos)) != null) {
            extractSequence(succ, cfg, path, tos);
        }
        else if (Options.interprocedural && appMethods.contains(callee)) { /* step into callee */
            Body body = callee.retrieveActiveBody();
            UnitGraph calleeCfg = generateUnitGraph(body);
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
        if (Options.uniquePaths) {
            if (paths.contains(path))
                return;
            paths.add(path);
        }

        numSequences += tos.size();
        for (TypeStateObject t : tos)
            if (t.hasValidHistory())
                if (Options.printJSON) // save to print later
                    data.add(t.getHistory());
                else
                    outfile.println(t.getHistory());
    }

    /* handles a relevant (API call) invocation and if successful, returns the successor statement
     * to be executed, typically the next stmt or possibly a handler stmt in case of exception */
    private Stmt handleInvokeRelevant(Stmt stmt, UnitGraph cfg, Path path, List<TypeStateObject> tos) {
        InvokeExpr invokeExpr = stmt.getInvokeExpr();
        SootMethod currMethod = cfg.getBody().getMethod();

        Value v;
        if (invokeExpr instanceof InstanceInvokeExpr
                && ((InstanceInvokeExpr) invokeExpr).getBase().getType() instanceof RefType) {
            v = ((InstanceInvokeExpr) invokeExpr).getBase();
            if (invokeExpr.getMethod().isConstructor())
                finalizePreviousHistory(tos, v);
        }
        else if (invokeExpr instanceof StaticInvokeExpr && stmt instanceof AssignStmt
                    && ((AssignStmt) stmt).getLeftOp().getType() instanceof RefType) {
            v = ((AssignStmt) stmt).getLeftOp();
            finalizePreviousHistory(tos, v);
        }
        else
            return null; /* don't include static methods that don't return anything stored to an object */
        
        TypeStateObject t = null;
        for (TypeStateObject t1 : tos)
            if (!t1.getHistory().isFinalized() && t1.getObject().equals(v)) {
                t = t1;
                break;
            }

        if (t == null) { /* first time encountering this typestate */
            t = new TypeStateObject(v, getMonitorsClone());
            if (! t.isRelevant())
                return null;
            tos.add(t);
        }


        /* choose the next successor, and check... */
        List<Unit> succs = cfg.getSuccsOf(stmt);
        assert succs.size() > 0 : "empty succs list when choosing next succ";
        Unit succ = succs.get(rng.nextInt(succs.size())); /* pick a random successor */
        assert succ != null : "succ is null";
        if (succs.size() > 1) /* record choice point along path */
            path.addChoicePoint(succ);

        /* ...if successor is the handler for a trap */
        SootClass exceptionThrown = null;
        for (Trap trap : cfg.getBody().getTraps())
            if (succ == trap.getHandlerUnit()) {
                exceptionThrown = trap.getException();
                break;
            }

        /* create the StmtInstance and gather monitor states */
        StmtInstance stmtIns = new StmtInstance(stmt);
        stmtIns.setExceptionThrown(exceptionThrown);

        List<MonitorState> ps = new ArrayList<MonitorState>();
        for (Monitor p : t.getMonitors()) {
            p.post(stmtIns);
            ps.add(p.getState());
        }

        /* record location info */
        LocationInfo location = new LocationInfo(stmt, currMethod);

        /* Finally, create the event!! */
        Event e = new Event(invokeExpr.getMethod(), ps, location);
        t.getHistory().addEvent(e);

        return (Stmt) succ;
    }

    private boolean isReturn(Stmt stmt) {
        return stmt instanceof ReturnStmt || stmt instanceof ReturnVoidStmt;
    }

    /** Find a non-finalized typestate object (default/init: all objects in tos) representing v in tos,
     * and if any, finalize its history so that no new events can be added to it */
    private void finalizePreviousHistory(List<TypeStateObject> tos, Value v) {
        for (TypeStateObject t1 : tos)
            if (!t1.getHistory().isFinalized() && t1.getObject().equals(v)) {
                t1.getHistory().finalize();
                return;
            }
    }

    /** Returns a clone of the monitors -- does not clone transitions since they are fixed */
    private List<Monitor> getMonitorsClone() {
        List<Monitor> ps = new ArrayList<Monitor>();
        for (Monitor p : monitors) {
            Monitor pClone = new Monitor(p.getTransitions());
            ps.add(pClone);
        }
        return ps;
    }

    private UnitGraph generateUnitGraph(Body body) {
        if (Options.unitGraph.equals("brief"))
            return new BriefUnitGraph(body);
        else if (Options.unitGraph.equals("trap"))
            return new TrapUnitGraph(body);
        return null;
    }
}
