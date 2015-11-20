/* The sequence extractor, implemented as a SceneTransformer */
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

public class SequenceExtractor extends BodyTransformer
{

    // <------------------------------------------------->
    // <---------- configurable options ----------------->
    // <------------------------------------------------->

    // maximum number of sequences from components
    private final int MAX_SEQS = 100;

    // maximum length of sequence
    private final int MAX_LEN = 1000;

    // search order
    private enum SearchOrder { DFS, RANDOM }
    private SearchOrder search = SearchOrder.RANDOM;








    // current sequence of API calls extracted
    private Stack<SootMethod> currSequence;

    // sequence of choice points along the current path with the choice of
    // succ that was made
    class ChoicePoint
    {
        Unit point;
        Unit choice;
        List<Unit> otherChoices;

        public ChoicePoint(Unit point, Unit succ, List<Unit> otherSuccs)
        {
            this.point = point;
            this.choice = succ;
            this.otherChoices = otherSuccs;
        }

        public Unit getChoicePoint() {
            return point;
        }
        public Unit getChoice() {
            return choice;
        }
        public List<Unit> getOtherChoices() {
            return otherChoices;
        }

        public boolean equals(Object o)
        {
            if (this == o) return true;
            if (o == null || o.getClass() != this.getClass()) return false;
            ChoicePoint cp = (ChoicePoint) o;
            return this.point == cp.getChoicePoint();
        }

        public int hashCode()
        {
            return this.point.hashCode();
        }
    }
    private Stack<ChoicePoint> currChoicePoints;
    
    // all application methods, used to check if we should add an invocation
    // to the sequence (API) or step into it (application)
    private List<SootMethod> appMethods;

    // number of sequences from each component
    private int numSequences = 0;

    // total number of sequences
    private static int totalSequences = 0;

    // total number of LOC
    private static int totalLOC = 0;

    // the output file
    PrintStream outfile;

    // start time for this method
    private long startTime;

    private Random rng;

    class SequenceExtractorException extends Exception {}

    class SequenceLimitException extends SequenceExtractorException {}

    class SequenceLengthException extends SequenceExtractorException {}

    class TimeoutException extends SequenceExtractorException {}






    public SequenceExtractor()
    {
        currSequence = new Stack<SootMethod>();
        currChoicePoints = new Stack<ChoicePoint>();
        rng = new Random(System.currentTimeMillis());
        outfile = System.out;
    }

    public SequenceExtractor(File f)
    {
        this();

        try {
            this.outfile = new PrintStream(f);
        } catch (FileNotFoundException e) {
            System.err.println("Cannot create writable file " + f + ":" + e.getMessage());
            System.exit(1);
        }
    }

    protected void internalTransform(Body body, String phaseName, Map options)
    {
        SootMethod rootMethod = body.getMethod();
        String packageName = rootMethod.getDeclaringClass().getPackageName();
        if (packageName.startsWith("android.") || packageName.startsWith("com.google."))
            return;

        int LOC = body.getUnits().size();
        System.out.println("Sequence extractor phase: " + phaseName + ". Analyzing method " +
                mySignature(rootMethod) + ". #instructions: " + LOC);
        totalLOC += LOC;

        appMethods = EntryPoints.v().methodsOfApplicationClasses();

        numSequences = 0;
        outfile.println("# " + mySignature(rootMethod));

        UnitGraph cfg = new BriefUnitGraph(body);
        Unit head = body.getUnits().getFirst();

        startTime = System.currentTimeMillis() / 1000L;

        try {
            extractSequences(head, cfg);
        } catch (SequenceLimitException e) {
            System.err.println("sequence limit (" + MAX_SEQS + ") reached");
        } catch (SequenceLengthException e) {
            System.err.println("too big sequence");
        } catch (TimeoutException e) {
            System.err.println("TIMEOUT");
        } catch (SequenceExtractorException e) {
            System.err.println("something is wrong.." + e.getMessage());
            System.exit(1);
        }

        totalSequences += numSequences;
        System.out.println("Sub total sequences: " + numSequences);

        System.out.println("Total sequences: " + totalSequences);
        System.out.println("Total LOC: " + totalLOC);
    }

    private void extractSequences(Unit stmt, UnitGraph cfg)
        throws SequenceExtractorException
    {
        extractSequences(stmt, cfg, true);
    }

    private void extractSequences(Unit ustmt, UnitGraph cfg, boolean invokeCheck)
        throws SequenceExtractorException
    {
        // some misbehaving case
        if (numSequences == 0 && System.currentTimeMillis() / 1000L - startTime > 5)
            throw new TimeoutException();

        Stmt stmt;
        try {
            // since we are in jimple this cast should be safe
            stmt = (Stmt) ustmt;
        } catch (ClassCastException e) {
            System.err.println(e.getMessage());
            throw e;
        }

        if (invokeCheck && stmt.containsInvokeExpr())
        {
            handleInvoke(stmt, cfg); // mutually recursive
            return;
        }

        List<Unit> succs = cfg.getSuccsOf(stmt);

        if  (stmt instanceof ReturnStmt || stmt instanceof ReturnVoidStmt
                || stmt instanceof ThrowStmt)
        {
            assert succs.size() == 0 : "more than one succ for return";
            handleTerminal();
            return;
        }

        assert succs.size() > 0 : "empty succs list for " + stmt + " when stmt is not a return";

        if (succs.size() == 1) // no choice point
        {
            if (stmt instanceof GotoStmt)
                handleGoto(stmt, cfg);
            else
                extractSequences(succs.get(0), cfg);
        }
        else
        {
            Unit succ;
            List<Unit> choices;
            int idx = getLastChoicePoint(stmt);
            if (idx != -1) // already made a choice, now make one of the other choices
                choices = currChoicePoints.get(idx).getOtherChoices();
            else
                choices = succs;

            if (choices.size() == 0)
                return;

            List<Unit> choices_arr = new ArrayList<Unit>(choices);
            if (search == SearchOrder.RANDOM)
                Collections.shuffle(choices_arr, rng);

            while (choices_arr.size() > 0)
            {
                succ = choices_arr.remove(0); // mutates the list

                assert succ != null : "succ is null";

                currChoicePoints.push(new ChoicePoint(stmt, succ, new ArrayList<Unit>(choices_arr)));
                extractSequences(succ, cfg);
                currChoicePoints.pop();
            }
        }
    }

    // treating goto statements exactly like a choice point (but one that makes
    // no choice), in order to detect while(true) loops
    private void handleGoto(Stmt stmt, UnitGraph cfg)
        throws SequenceExtractorException
    {
        int idx = getLastChoicePoint(stmt);
        if (idx != -1) // already encountered this goto, don't expand it again
            return;

        Unit succ = cfg.getSuccsOf(stmt).get(0);
        currChoicePoints.push(new ChoicePoint(stmt, succ, null));
        extractSequences(succ, cfg);
        currChoicePoints.pop();
    }

    private void handleInvoke(Stmt stmt, UnitGraph cfg) 
        throws SequenceExtractorException
    {
        SootMethod callee = stmt.getInvokeExpr().getMethod();

        if (isAndroidMethod(callee)) { // not an application method
            if (currSequence.size() == MAX_LEN) {
                throw new SequenceLengthException();
            }

            currSequence.push(callee);

            try {
                // recurse so that we can pop from the sequence during...
                extractSequences(stmt, cfg, false);
            } finally {
                // ...backtracking
                currSequence.pop();
            }
        }
        else // otherwise step over the statement
        {
            extractSequences(stmt, cfg, false);
        }
    }

    private boolean isAndroidMethod(SootMethod m)
    {
        SootClass cl = m.getDeclaringClass();
        return Scene.v().quotedNameOf(cl.getName()).startsWith("android");
    }

    private int getLastChoicePoint(Stmt stmt)
    {
        for (int i = currChoicePoints.size() - 1; i >= 0; i--)
            if (currChoicePoints.get(i).getChoicePoint() == stmt)
                return i;
        return -1;
    }

    private void handleTerminal() 
        throws SequenceExtractorException
    {
        if (currSequence.size() == 0 || currSequence.size() == 1)
            return;

        for (SootMethod m : currSequence)
            outfile.print(mySignature(m) + " ");
        outfile.println();
        System.out.println("<seq of size " + currSequence.size() + ">");
        numSequences++;

        if (numSequences == MAX_SEQS)
            throw new SequenceLimitException();
    }

    private String mySignature(SootMethod m)
    {
        SootClass cl = m.getDeclaringClass();
        String name = m.getName();
        List params = m.getParameterTypes();
        Type returnType = m.getReturnType();

        StringBuffer buffer = new StringBuffer();
        buffer.append("\"" + Scene.v().quotedNameOf(cl.getName()) + ": ");
        buffer.append(m.getSubSignature(name, params, returnType));
        buffer.append("\"");

        return buffer.toString().intern();
    }
}
