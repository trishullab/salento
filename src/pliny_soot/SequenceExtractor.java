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

import soot.jimple.toolkits.callgraph.CallGraph;
import soot.jimple.toolkits.callgraph.Edge;

/** The sequence extractor, implemented as a SceneTransformer */
public class SequenceExtractor extends BodyTransformer
{
    /** List of paths explored */
    private List<Path> paths;

    /** Call stack */
    private Stack<CallContext> callStack;

    /** All application methods, used to check if we should add an invocation
     * to the sequence (API) or step into it (application) */
    private List<SootMethod> appMethods;

    /** Number of sequences from each component */
    private int numSequences;

    /** Total number of sequences */
    private int totalSequences;

    /** Total number of LOC */
    private int totalLOC;

    /** The output file */
    PrintStream outfile;

    /** Start time for this method */
    private long startTime;

    private Random rng;

    class SequenceExtractorException extends Exception {}

    class SequenceLengthException extends SequenceExtractorException {}

    class TimeoutException extends SequenceExtractorException {}


    public SequenceExtractor() {
        totalSequences = 0;
        totalLOC = 0;
        paths = new ArrayList<Path>();
        callStack = new Stack<CallContext>();
        rng = new Random(System.currentTimeMillis());
        outfile = System.out;
    }

    public SequenceExtractor(File f) {
        this();

        try {
            this.outfile = new PrintStream(f);
        } catch (FileNotFoundException e) {
            System.err.println("Cannot create writable file " + f + ":" + e.getMessage());
            System.exit(1);
        }
    }

    protected void internalTransform(Body body, String phaseName, Map options) {
        SootMethod method = body.getMethod();
        if (! Util.isAndroidEntryPoint(method))
            return;

        appMethods = EntryPoints.v().methodsOfApplicationClasses();
        int LOC = body.getUnits().size();
        totalLOC += LOC;

        System.out.println("Extracting sequences from " + Util.mySignature(method));
        System.out.println("#instructions: " + LOC);

        numSequences = 0;
        outfile.println("# " + Util.mySignature(method));

        UnitGraph cfg = new BriefUnitGraph(body);
        Unit head = body.getUnits().getFirst();

        for (int i = 0; i < Options.MAX_SEQS; i++) {
            startTime = System.currentTimeMillis() / 1000L;
            try {
                extractSequence(head, cfg, new History(), new Path());
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

        totalSequences += numSequences;
        System.out.println("Sub total sequences: " + numSequences);

        System.out.println("Total sequences: " + totalSequences);
        System.out.println("Total LOC: " + totalLOC);
    }

    private void extractSequence(Unit stmt, UnitGraph cfg, History his, Path path)
            throws SequenceExtractorException {
        extractSequence(stmt, cfg, his, path, true);
    }

    private void extractSequence(Unit ustmt, UnitGraph cfg, History his, Path path, boolean invokeCheck)
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

        if (invokeCheck && stmt.containsInvokeExpr()) {
            handleInvoke(stmt, cfg, his, path); /* mutually recursive */
            return;
        }

        List<Unit> succs = cfg.getSuccsOf(stmt);

        if (isReturnOrThrow(stmt)) {
            assert succs.size() == 0 : "more than one succ for return or throw";
            if (callStack.empty())
                handleTerminal(his, path);
            else {
                CallContext context = callStack.pop();
                extractSequence(context.getStmt(), context.getCfg(), his, path, false);
            }

            return;
        }

        assert succs.size() > 0 : "empty succs list when stmt is not a return or throw";
        Unit succ = succs.get(rng.nextInt(succs.size())); /* pick a random successor */
        assert succ != null : "succ is null";
        if (succs.size() > 1) /* record choice point along path */
            path.addChoicePoint(succ);
        extractSequence(succ, cfg, his, path);
    }

    private void handleInvoke(Stmt stmt, UnitGraph cfg, History his, Path path)
            throws SequenceExtractorException {
        SootMethod callee = stmt.getInvokeExpr().getMethod();

        if (Util.isAndroidMethod(callee)) { /* add an event to history */
            if (his.size() >= Options.MAX_LEN) {
                throw new SequenceLengthException();
            }

            Event e = new Event(callee, null);
            his.addEvent(e);

            extractSequence(stmt, cfg, his, path, false);
        }
        else if (appMethods.contains(callee)) { /* step into callee */
            Body body = callee.retrieveActiveBody();
            UnitGraph calleeCfg = new BriefUnitGraph(body);
            Unit head = body.getUnits().getFirst();

            callStack.push(new CallContext(stmt, cfg));
            extractSequence(head, calleeCfg, his, path);
        }
        else /* not an Android method or application method, step over */
            extractSequence(stmt, cfg, his, path, false);
    }

    private void handleTerminal(History his, Path path) throws SequenceExtractorException {
        if (his.size() <= 1)
            return;

        if (paths.contains(path))
            return;
        paths.add(path);

        his.print(outfile);
        outfile.println();
        System.out.println("<seq of size " + his.size() + ">");
        numSequences++;
    }

    private boolean isReturnOrThrow(Stmt stmt) {
        return stmt instanceof ReturnStmt || stmt instanceof ReturnVoidStmt|| stmt instanceof ThrowStmt;
    }
}
