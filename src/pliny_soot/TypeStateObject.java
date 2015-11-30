/* Author: Vijay Murali */

package pliny_soot;

import java.util.Arrays;

import soot.SootClass;
import soot.Type;
import soot.RefType;
import soot.Value;

/** A thin wrapper for a soot Value with additional operations */
public class TypeStateObject {

    private Value object;

    public TypeStateObject(Value object) {
        this.object = object;
    }

    public Value getObject() {
        return object;
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
        Type t = object.getType();
        if (! (t instanceof RefType))
            return false;
        RefType rt = (RefType) t;
        SootClass c = rt.getSootClass();
        for (String cls : Arrays.asList(Options.myTypeStates))
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
