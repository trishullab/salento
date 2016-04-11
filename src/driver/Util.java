/* Author: Vijay Murali */

package driver;

import java.util.*;
import java.io.*;

import soot.*;

/** Utilities for the driver */
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

    /** Check if the current app is interesting (i.e, has at least one class loaded that's of interest to us) */
    public static boolean isRelevantApp() {
        if (Options.relevantTypestates == null)
            return true;
        for (SootClass cls : Scene.v().getClasses())
            if (Options.relevantTypestates.contains(cls.getName()))
                return true;
        return false;
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
        buffer.append(SootMethod.getSubSignature(name, params, returnType));
        buffer.append("\"");

        return buffer.toString().intern();
    }

    /** Read a file into a list of strings */
    public static List<String> readFileToList(File f) throws FileNotFoundException, IOException {
        List<String> lines = new ArrayList<String>();
        BufferedReader br = new BufferedReader(new FileReader(f));
        String line;
        
        while ((line = br.readLine()) != null)
            lines.add(line);

        br.close();
        return lines;
    }
}
