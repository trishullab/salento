/* Author: Vijay Murali */

package pliny_soot.predicates;

import pliny_soot.*;

import soot.Unit;

import soot.jimple.Stmt;
import soot.jimple.InvokeExpr;

import java.util.regex.Pattern;
import java.util.regex.Matcher;

/** A predicate on the arity of a particular API call */
public class ArityPredicate implements Predicate {

    private char op;
    private int arity;

    public ArityPredicate(String s) {
        Pattern regex = Pattern.compile("(=|<|>)(\\d+)");
        Matcher m = regex.matcher(s);

        assert m.matches() : "malformed arity predicate: " + s;
        try {
            op = m.group(1).charAt(0);
            arity = Integer.parseInt(m.group(2));
        } catch(NumberFormatException e) {
            assert false : "invalid arity: " + s;
        }
    }

    public static void apply(Unit ustmt) {
    }

    public boolean enabled(Unit ustmt) {
        Stmt stmt = (Stmt) ustmt;

        if (!stmt.containsInvokeExpr())
            return false;

        InvokeExpr invokeExpr = stmt.getInvokeExpr();
        int argCount = invokeExpr.getArgCount();

        switch (op) {
            case '=': return argCount == arity;
            case '>': return argCount > arity;
            case '<': return argCount < arity;
            default:  return false;
        }
    }
}
