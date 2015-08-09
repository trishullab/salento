/* Main driver for soot */
/* Author: Vijay Murali */

package pliny_soot;

import java.util.*;
import soot.*;

import soot.options.Options;


public class Driver {

    String[] args;

    public Driver(String[] args)
    {
        this.args = args;
    }

    public static void main(String[] args)
    {
        System.out.println("Driver started");
        new Driver(args).runDriver();
    }

    public void runDriver()
    {
        Options.v().set_src_prec(Options.src_prec_class);
        Options.v().set_output_format(Options.output_format_class);

        Scene.v().addBasicClass("java.io.PrintStream",SootClass.SIGNATURES);
        Scene.v().addBasicClass("java.lang.System",SootClass.SIGNATURES);
        Scene.v().addBasicClass("java.lang.Thread",SootClass.SIGNATURES);
        Scene.v().addBasicClass("java.lang.ThreadGroup",SootClass.SIGNATURES);
        Scene.v().addBasicClass("java.lang.ClassLoader",SootClass.SIGNATURES);
        Scene.v().addBasicClass("java.lang.ref.Finalizer",SootClass.SIGNATURES);

        Pack wjtp = PackManager.v().getPack("wjtp");
        wjtp.add(new Transform("wjtp.sequence_extractor", new SequenceExtractor()));
        soot.Main.main(args);
    }
}
