/* Author: Vijay Murali */

package pliny_soot;

import java.util.*;
import java.io.*;

import soot.*;

/** Utilities for pliny-soot */
public final class Util {

    private Util() {}

    /** Check if a given package should be avoided */
    public static boolean canExtractSequences(String pack) {
        for (int i = 0; i < Options.avoidPackages.length; i++)
            if (pack.startsWith(Options.avoidPackages[i]))
                return false;
        return true;
    }

    /** Return true (false) if (not) Android method */
    public static boolean isAndroidMethod(SootMethod m) {
        String pack = m.getDeclaringClass().getPackageName();
        return pack.startsWith("android.");
    }

    /** Special signature for data format */
    public static String mySignature(SootMethod m)
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
