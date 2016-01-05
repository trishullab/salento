/* Author: Vijay Murali */

package pliny_soot.predicates;

import pliny_soot.*;

import soot.Unit;

import java.util.regex.Pattern;
import java.util.regex.Matcher;

/** A predicate on the arity of a particular API call */
public class ArityPredicate extends Predicate {

    private String op;
    private int arity;

    public ArityPredicate(String s) {
        Pattern regex = Pattern.compile("(=|<|>)(\\d+)");
        Matcher m = regex.matcher(s);

        assert m.matches() : "malformed arity predicate: " + s;
        try {
            op = m.group(1);
            arity = Integer.parseInt(m.group(2));
        } catch(NumberFormatException e) {
            assert false : "invalid arity: " + s;
        }
    }

    public static void apply(Unit stmt) {
    }

    @Override
    public boolean enabled(Unit stmt) {
        return false;
    }
}
