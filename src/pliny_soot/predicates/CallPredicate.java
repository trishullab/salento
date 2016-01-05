/* Author: Vijay Murali */

package pliny_soot.predicates;

import pliny_soot.*;

import soot.Unit;

/** A predicate that enables/disables on a particular API call */
public class CallPredicate extends Predicate {

    private String method;

    public CallPredicate(String method) {
        this.method = method;
    }

    public static void apply(Unit stmt) {
    }

    @Override
    public boolean enabled(Unit stmt) {
        return false;
    }
}
