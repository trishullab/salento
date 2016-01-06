/* Author: Vijay Murali */

package pliny_soot;

import java.util.List;
import java.util.Arrays;

import soot.SootClass;
import soot.Type;
import soot.RefType;
import soot.Value;

/** A typestate object on which some API call operation(s) was performed */
public class TypeStateObject {

    /** The object of this typstate */
    private Value object;

    /** List of property automata associated with this typestate */
    private List<PropertyAutomaton> properties;

    /** History of events associated with this typestate */
    private History history;

    public TypeStateObject(Value object, List<PropertyAutomaton> properties) {
        this.object = object;
        this.properties = properties;
        history = new History();
    }

    public Value getObject() {
        return object;
    }

    public List<PropertyAutomaton> getProperties() {
        return properties;
    }

    public History getHistory() {
        return history;
    }

    /** Get the SootClass of this TypeStateObject */
    public SootClass getSootClass() {
        Type t = object.getType();
        assert t instanceof RefType : t + " is not a reference type";
        RefType rt = (RefType) t;
        return rt.getSootClass();
    }

    /** Check if this TypeStateObject is of a type we're interested in */
    public boolean isMyTypeState() {
        if (Options.myTypestates == null)
            return true;
        Type t = object.getType();
        if (! (t instanceof RefType))
            return false;
        RefType rt = (RefType) t;
        SootClass c = rt.getSootClass();
        for (String cls : Options.myTypestates)
            if (c.getName().equals(cls) || Util.isDescendant(c, cls))
                return true;
        return false;
    }

    /** Return the first Android class that comes up in this object's inheritance hierarchy */
    public SootClass getYoungestAndroidParent() {
        SootClass c = getSootClass();
        while (! Util.isAndroidClass(c))
            c = c.getSuperclass();
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
