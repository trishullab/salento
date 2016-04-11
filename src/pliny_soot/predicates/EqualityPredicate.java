/* Author: Vijay Murali */

package pliny_soot.predicates;

import pliny_soot.*;

import soot.jimple.Stmt;

import java.util.regex.Pattern;
import java.util.regex.Matcher;

/** An equality (or disequality) predicate */
public class EqualityPredicate implements Predicate {

    private int lArg;
    private int rArg;
    private boolean equal;
    private String method;

    public EqualityPredicate(String s) {
        Pattern regex = Pattern.compile("\\$(\\d+)(=|!=)\\$(\\d+)_(.*)");
        Matcher m = regex.matcher(s);

        assert m.matches() : "malformed equality predicate: " + s;
        try {
            lArg = Integer.parseInt(m.group(1));
            rArg = Integer.parseInt(m.group(3));
            equal = m.group(2).equals("=");
            method = m.group(4);
        } catch(NumberFormatException e) {
            assert false : "invalid argument number: " + s;
        }
    }

    public static void apply(Stmt stmt) {
    }

    public boolean enabled(StmtInstance stmtIns) {
        return false;
    }
}
