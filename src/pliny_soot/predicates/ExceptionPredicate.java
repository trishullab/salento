/* Author: Vijay Murali */

package pliny_soot.predicates;

import pliny_soot.*;

import soot.SootClass;

import soot.jimple.Stmt;

import java.util.regex.Pattern;
import java.util.regex.Matcher;

/** A predicate that enables/disables if a particular exception is thrown */
public class ExceptionPredicate implements Predicate {

    private String exceptionClassName;
    private boolean enabledOnNegation;

    public ExceptionPredicate(String s) {
        Pattern regex = Pattern.compile("(!)?(.*)");
        Matcher m = regex.matcher(s);

        assert m.matches() : "malformed exception predicate: " + s;
        enabledOnNegation = (m.group(1) != null);
        exceptionClassName = m.group(2);
    }

    public static void apply(Stmt stmt) {
    }

    public boolean enabled(StmtInstance stmtIns) {
        return (enabledOnNegation? ! enabled_aux(stmtIns) : enabled_aux(stmtIns));
    }

    private boolean enabled_aux(StmtInstance stmtIns) {
        if (! stmtIns.isExceptionThrown())
            return false;

        SootClass e = stmtIns.getExceptionThrown();
        return e.getName().equals(exceptionClassName);
    }
}
