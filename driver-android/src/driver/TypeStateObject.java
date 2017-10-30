/* Author: Vijay Murali */

package driver;

import java.util.List;
import java.util.Arrays;

import soot.Scene;
import soot.SootClass;
import soot.SootMethod;
import soot.Type;
import soot.RefType;
import soot.Value;

/** A typestate object on which some API call operation(s) was performed */
public class TypeStateObject {

    /** The object of this typstate */
    private Value object;

    /** List of monitors associated with this typestate */
    private List<Monitor> monitors;

    /** History of events associated with this typestate */
    private History history;

    public TypeStateObject(Value object, List<Monitor> monitors) {
        this.object = object;
        this.monitors = monitors;
        history = new History();
        assert object.getType() instanceof RefType : "TypeStateObject created without any reference!";
    }

    public Value getObject() {
        return object;
    }

    public List<Monitor> getMonitors() {
        return monitors;
    }

    public History getHistory() {
        return history;
    }

    /** Check if this is a valid typestate.
     * Include in here any condition that indicates that the sequences
     * collected on this typestate may be invalid
     * (example - object was not allocated before it was used). If the
     * typestate is not valid, the sequences will be discarded.
     * We're giving the benefit of doubt to the app, assuming that the
     * imprecision in our static collection of sequences is to blame. */
    public boolean hasValidHistory() {
        if (! Options.validateSequences)
            return true;

        SootMethod firstCall = history.getEvents().get(0).getSigma();
        if (!firstCall.isConstructor() && !firstCall.isStatic())
            return false;

        return true;
    }

    /** Check if this TypeStateObject is of a type we're interested in */
    public boolean isRelevant() {
        if (Options.relevantTypestates == null)
            return true;
        SootClass c = ((RefType) object.getType()).getSootClass();
        for (String cls : Options.relevantTypestates)
            if (c.getName().equals(cls))
                return true;
        return false;
    }

    /** Return the first relevant class that comes up in this object's inheritance hierarchy */
    public SootClass getRelevantAncestor() {
        SootClass c = ((RefType) object.getType()).getSootClass();
        if (Options.relevantTypestates == null) { /* interested in all typestates? get the first non-app class */
            while (Scene.v().getApplicationClasses().contains(c))
                c = c.getSuperclass();
        }
        return c;
    }

    @Override
    public String toString() {
        return object.toString();
    }

    @Override
    public boolean equals(Object o) {
        if (o == null || ! (o instanceof TypeStateObject)) return false;
        if (this == o) return true;

        TypeStateObject t = (TypeStateObject) o;
        return object.equivTo(t.getObject());
    }

    @Override
    public int hashCode() {
        return object.equivHashCode();
    }
}
