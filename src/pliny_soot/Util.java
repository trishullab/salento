/* Author: Vijay Murali */

package pliny_soot;

import java.util.*;
import java.io.*;

import soot.*;

/** Utilities for pliny-soot */
public final class Util {

    private Util() {}

    /** Check if m is (overriding) an Android entry point */
    public static boolean isAndroidEntryPoint(SootMethod m) {
        for (String entryPoint : Arrays.asList(Options.androidEntryPoints)) {
            String cls = entryPoint.substring(0, entryPoint.lastIndexOf('.'));
            String mth = entryPoint.substring(entryPoint.lastIndexOf('.')+1);

            SootClass c = m.getDeclaringClass();

            if (isDescendant(c, cls) && m.getName().equals(mth))
                return true;
        }
        return false;
    }

    /** Check if c is a descendant of cls */
    public static boolean isDescendant(SootClass c, String cls) {
        while (c.hasSuperclass()) {
            c = c.getSuperclass();
            if (c.getName().equals(cls))
                return true;
        }
        return false;
    }

    /** Check if a class c is Android */
    public static boolean isAndroidClass(SootClass c) {
        return c.getPackageName().startsWith("android.");
    }

    /** Check if m is an Android package method */
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
