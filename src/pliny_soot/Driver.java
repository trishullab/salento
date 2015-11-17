/* Main driver for soot */
/* Author: Vijay Murali */

package pliny_soot;

import java.util.*;
import java.io.File;
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
        Options.v().set_src_prec(Options.src_prec_apk);
        Options.v().set_output_format(Options.output_format_dex);

        Scene.v().addBasicClass("java.io.PrintStream",SootClass.SIGNATURES);
        Scene.v().addBasicClass("java.lang.System",SootClass.SIGNATURES);
        Scene.v().addBasicClass("java.lang.Thread",SootClass.SIGNATURES);
        Scene.v().addBasicClass("java.lang.ThreadGroup",SootClass.SIGNATURES);
        Scene.v().addBasicClass("java.lang.ClassLoader",SootClass.SIGNATURES);
        Scene.v().addBasicClass("java.lang.ref.Finalizer",SootClass.SIGNATURES);

        Pack jtp = PackManager.v().getPack("jtp");
        
        SequenceExtractor seqExt;

        // Java - making you convert an array to a list
        ArrayList<String> argsList = new ArrayList<String>(Arrays.asList(args));
        if (argsList.contains("-pliny-soot-outfile"))
        {
            String outfile = argsList.remove(argsList.indexOf("-pliny-soot-outfile")+1);
            seqExt = new SequenceExtractor(new File(outfile));
            argsList.remove("-pliny-soot-outfile");
        }
        else
            seqExt = new SequenceExtractor();

        jtp.add(new Transform("jtp.sequence_extractor", seqExt));
        soot.Main.main(argsList.toArray(new String[0]));
    }
}
