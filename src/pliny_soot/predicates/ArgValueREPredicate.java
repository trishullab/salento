/* Author: Vijay Murali */

package pliny_soot.predicates;

import pliny_soot.*;

import soot.Value;

import soot.jimple.Stmt;
import soot.jimple.InvokeExpr;
import soot.jimple.StringConstant;

import java.util.regex.Pattern;
import java.util.regex.Matcher;
import java.util.regex.PatternSyntaxException;

/** A predicate on an (string) argument's form represented as a regular expression */
public class ArgValueREPredicate implements Predicate {

    private int arg;
    private Pattern regexp;
    private boolean enabledOnNegation;

    public ArgValueREPredicate(String s) {
        Pattern regex = Pattern.compile("(!)?\\$(\\d+) \"(.*)\"");
        Matcher m = regex.matcher(s);

        assert m.matches() : "malformed RE predicate: " + s;
        try {
            enabledOnNegation = (m.group(1) != null);
            arg = Integer.parseInt(m.group(2));
            regexp = Pattern.compile(m.group(3));
        } catch(NumberFormatException e) {
            assert false : "invalid argument number: " + s;
        } catch (PatternSyntaxException e) {
            assert false: "invalid pattern syntax: " + s;
        }
    }

    public static void apply(Stmt stmt) {
    }

    public boolean enabled(Stmt stmt) {
        return (enabledOnNegation? ! enabled_aux(stmt) : enabled_aux(stmt));
    }

    private boolean enabled_aux(Stmt stmt) {
        if (!stmt.containsInvokeExpr())
            return false;

        InvokeExpr invokeExpr = stmt.getInvokeExpr();
        int argCount = invokeExpr.getArgCount();

        if (arg > argCount)
            return false;

        Value argVal = invokeExpr.getArg(arg-1);
        if (! (argVal instanceof StringConstant))
            return false;

        String str = ((StringConstant) argVal).value;
        return regexp.matcher(str).matches();
    }
}
