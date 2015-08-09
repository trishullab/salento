/* The sequence extractor, implemented as a SceneTransformer */
/* Author: Vijay Murali */

package pliny_soot;

import java.util.*;
import soot.*;

import soot.toolkits.graph.UnitGraph;
import soot.toolkits.graph.BriefUnitGraph;

import soot.jimple.Stmt;
import soot.jimple.GotoStmt;
import soot.jimple.InvokeStmt;
import soot.jimple.ReturnStmt;
import soot.jimple.ReturnVoidStmt;

import soot.jimple.toolkits.callgraph.CallGraph;
import soot.jimple.toolkits.callgraph.Edge;

public class SequenceExtractor extends SceneTransformer
{

    // <------------------------------------------------->
    // <---------- configurable options ----------------->
    // <------------------------------------------------->

    // maximum number of sequences from components
    private final int MAX_SEQS = 10000;

    // maximum number of times a choice point can appear along a path
    // (indirectly, unroll loops MAX_CP-1 times), should be at least 2
    // if loop bodies have to be explored at all
    private final int MAX_CP = 2;

    // maximum length of sequence
    private final int MAX_LEN = 1000;

    // search order
    private enum SearchOrder { DFS, RANDOM }
    private SearchOrder search = SearchOrder.DFS;








    // current sequence of API calls extracted
    private Stack<SootMethod> currSequence;

    // sequence of choice points along the current path, used to bound the
    // number of loop unrolls (see MAX_CP)
    private Stack<Unit> currChoicePoints;
    
    // synchronized stacks storing the return Unit to jump to and its
    // corresponding method's CFG respectively, saved and restored during
    // backtracking. NOT storing the sequence of API calls, that's done by 
    // currSequence above.
    private Stack<Unit> invokeStack;
    private Stack<UnitGraph> cfgStack;

    // the current root of component being analyzed
    private SootMethod currRoot;

    // all application methods, used to check if we should add an invocation
    // to the sequence (API) or step into it (application)
    private List<SootMethod> appMethods;

    // number of sequences from each component
    private int numSequences = 0;

    // the call graph
    CallGraph callGraph;

    private Random rng;

    class SequenceExtractorException extends Exception {}

    class SequenceLimitException extends SequenceExtractorException {}

    class SequenceLengthException extends SequenceExtractorException {}

    class MaxChoicePointException extends SequenceExtractorException
    {
        private Stmt offendingChoicePoint;
        public MaxChoicePointException (Stmt stmt)
        {
            this.offendingChoicePoint = stmt;
        }

        public Stmt getChoicePoint()
        {
            return offendingChoicePoint;
        }
    }





    public SequenceExtractor()
    {
        currSequence = new Stack<SootMethod>();
        currChoicePoints = new Stack<Unit>();
        invokeStack = new Stack<Unit>();
        cfgStack = new Stack<UnitGraph>();
        rng = new Random(System.currentTimeMillis());
    }

    protected void internalTransform(String phaseName, Map options)
    {
        System.out.println("Sequence extractor phase: " + phaseName);

        appMethods = EntryPoints.v().methodsOfApplicationClasses();

        callGraph = Scene.v().getCallGraph();
        Set<SootMethod> roots = new HashSet<SootMethod>();

        for (SootMethod m : appMethods)
        {
            if (!callGraph.edgesInto(m).hasNext())
                roots.add(m);
        }

        int totalSequences = 0;
        for (SootMethod rootMethod : roots)
        {
            numSequences = 0;
            System.out.println("# " + mySignature(rootMethod));

            Body body = rootMethod.retrieveActiveBody();
            UnitGraph cfg = new BriefUnitGraph(body);
            Unit head = body.getUnits().getFirst();

            currRoot = rootMethod;
            try {
                extractSequences(head, cfg);
            } catch (SequenceLimitException e) {
                // carry on with the remaining components
            } catch (SequenceLengthException e) {
                System.err.println("too big sequence");
                System.exit(1);
            } catch (MaxChoicePointException e) {
                System.err.println("nobody handled max cp of " + e.getChoicePoint());
                System.exit(1);
            } catch (SequenceExtractorException e) {
                System.err.println("something is wrong.." + e.getMessage());
                System.exit(1);
            }

            totalSequences += numSequences;
            System.out.println("Sub total sequences: " + numSequences);
        }

        System.out.println("Total sequences: " + totalSequences);
    }

    private void extractSequences(Unit stmt, UnitGraph cfg)
        throws SequenceExtractorException
    {
        extractSequences(stmt, cfg, true);
    }

    private void extractSequences(Unit ustmt, UnitGraph cfg, boolean invokeCheck)
        throws SequenceExtractorException
    {
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

        if  (stmt instanceof ReturnStmt || stmt instanceof ReturnVoidStmt)
        {
            assert succs.size() == 0;
            if (invokeStack.size() == 0) // terminal
            {
                assert cfgStack.size() == 0;
                handleTerminal();
            }
            else
                extractSequences(invokeStack.pop(), cfgStack.pop());
            return;
        }

        assert succs.size() > 0;

        if (succs.size() == 1) // no choice point
        {
            if (stmt instanceof GotoStmt)
                handleGoto(stmt, cfg);
            else
                extractSequences(succs.get(0), cfg);
        }
        else
        {
            // If we have reached the maximum number of times this choice point
            // is allowed along a path, throw exception! In case of normal loops, 
            // this will bound the number of unrolls. In case of infinite loops,
            // this will not produce a sequence, as is to be expected.
            if (countChoicePointOccurrence(stmt) == MAX_CP) {
                throw new MaxChoicePointException(stmt);
            }

            // save the invoke stack at this point
            Stack<Unit> invokeStackAtThisPoint = (Stack<Unit>) invokeStack.clone();
            Stack<UnitGraph> cfgStackAtThisPoint = (Stack<UnitGraph>) cfgStack.clone();

            List<Unit> mySuccs = new ArrayList<Unit>(succs);

            if (search == SearchOrder.RANDOM)
                Collections.shuffle(mySuccs, rng);

            for (Unit succ : mySuccs)
            {
                currChoicePoints.push(stmt);

                // restore the invoke stack before making a new choice of succ
                invokeStack = (Stack<Unit>) invokeStackAtThisPoint.clone();
                cfgStack = (Stack<UnitGraph>) cfgStackAtThisPoint.clone();

                try {
                    extractSequences(succ, cfg);
                } catch (MaxChoicePointException e) {
                    Stmt offendingChoicePoint = e.getChoicePoint();

                    // keep throwing if this stmt didn't start the original throw
                    if (offendingChoicePoint != stmt)
                        throw e;
                } finally {
                    // code here should always be exectued after extractSequences
                    // returns, regardless of exception
                    currChoicePoints.pop();
                }
            }
        }
    }

    // treating goto statements exactly like a choice point (but one that makes
    // no choice), in order to detect while(true) loops
    private void handleGoto(Stmt stmt, UnitGraph cfg)
        throws SequenceExtractorException
    {
        if (countChoicePointOccurrence(stmt) == MAX_CP)
            throw new MaxChoicePointException(stmt);
        
        currChoicePoints.push(stmt);
        try {
            extractSequences(cfg.getSuccsOf(stmt).get(0), cfg);
        } catch (MaxChoicePointException e) {
            Stmt offendingChoicePoint = e.getChoicePoint();
            if (offendingChoicePoint != stmt)
                throw e;
        } finally {
            currChoicePoints.pop();
        }
    }

    private void handleInvoke(Stmt stmt, UnitGraph cfg) 
        throws SequenceExtractorException
    {
        // save the invoke stack
        Stack<Unit> invokeStackAtThisPoint = (Stack<Unit>) invokeStack.clone();
        Stack<UnitGraph> cfgStackAtThisPoint = (Stack<UnitGraph>) cfgStack.clone();

        SootMethod callee = stmt.getInvokeExpr().getMethod();

        // callee is an application method
        if (appMethods.contains(callee))
        {
            // get a set of potential callees from the call graph
            SootMethod caller = cfg.getBody().getMethod();
            Set<SootMethod> potentialCallees = new HashSet<SootMethod>();
            Iterator<Edge> edgesOut = callGraph.edgesOutOf(caller);

            while (edgesOut.hasNext())
            {
                Edge e = edgesOut.next();
                if (e.srcStmt() == stmt)
                    potentialCallees.add(e.tgt());
            }

            // conservatively extract sequences from each potential callee
            for (SootMethod potentialCallee : potentialCallees)
            {
                // restore the invoke stack before doing it
                invokeStack = (Stack<Unit>) invokeStackAtThisPoint.clone();
                cfgStack = (Stack<UnitGraph>) cfgStackAtThisPoint.clone();

                handleInvokeCallee(potentialCallee, stmt, cfg);
            }
        }
        else // otherwise it's just an API call
        {
            invokeStack = (Stack<Unit>) invokeStackAtThisPoint.clone();
            cfgStack = (Stack<UnitGraph>) cfgStackAtThisPoint.clone();

            handleInvokeCallee(callee, stmt, cfg);
        }
    }

    private void handleInvokeCallee(SootMethod callee, Stmt stmt, UnitGraph cfg) 
        throws SequenceExtractorException
    {
        if (!appMethods.contains(callee)) { // not an application method
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
        else // otherwise step into the application method
        {
            Body body = callee.retrieveActiveBody();
            UnitGraph calleeCfg = new BriefUnitGraph(body);
            Unit head = body.getUnits().getFirst();

            List<Unit> succs = cfg.getSuccsOf(stmt);
            assert succs.size() <= 1;
            if (succs.size() == 1)
            {
                invokeStack.push(succs.get(0));
                cfgStack.push(cfg);
            }

            try {
                extractSequences(head, calleeCfg);
            } finally {
                // put whatever code to be executed after extractSequences here
            }
        }
    }

    private int countChoicePointOccurrence(Unit cpstmt)
    {
        int cnt = 0;
        for (Unit stmt : currChoicePoints)
            if (stmt == cpstmt)
                cnt++;
        return cnt;
    }

    private void handleTerminal() 
        throws SequenceExtractorException
    {
        if (currSequence.size() == 0 || currSequence.size() == 1)
            return;

        for (SootMethod m : currSequence)
            System.out.print(mySignature(m) + " ");
        System.out.println();
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
