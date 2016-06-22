/* Author: Vijay Murali */

package driver;

import java.util.*;
import java.io.File;
import soot.*;

import soot.options.Options;


/** Main driver for soot */
public class Driver {

    String[] args;

    public Driver(String[] args) {
        this.args = args;
    }

    public static void main(String[] args) {
        System.out.println("Driver started");
        new Driver(args).runDriver();
    }

    public void runDriver() {
        Options.v().set_src_prec(Options.src_prec_apk);
        Options.v().set_output_format(Options.output_format_dex);

        Scene.v().addBasicClass("java.io.PrintStream",SootClass.SIGNATURES);
        Scene.v().addBasicClass("java.lang.System",SootClass.SIGNATURES);
        Scene.v().addBasicClass("java.lang.Thread",SootClass.SIGNATURES);
        Scene.v().addBasicClass("java.lang.ThreadGroup",SootClass.SIGNATURES);
        Scene.v().addBasicClass("java.lang.ClassLoader",SootClass.SIGNATURES);
        Scene.v().addBasicClass("java.lang.ref.Finalizer",SootClass.SIGNATURES);

        Pack jtp = PackManager.v().getPack("jtp");
        
        SequenceExtractor seqExt = new SequenceExtractor();

        ArrayList<String> argsList = new ArrayList<String>(Arrays.asList(args));
        if (argsList.contains("-outfile")) {
            String arg = argsList.remove(argsList.indexOf("-outfile")+1);
            seqExt.setupOutput(new File(arg));
            argsList.remove("-outfile");
        }
        if (argsList.contains("-typestates-file")) {
            String arg = argsList.remove(argsList.indexOf("-typestates-file")+1);
            seqExt.setupTypestates(new File(arg));
            argsList.remove("-typestates-file");
        }
        if (argsList.contains("-monitors-file")) {
            String arg = argsList.remove(argsList.indexOf("-monitors-file")+1);
            seqExt.setupMonitors(new File(arg));
            argsList.remove("-monitors-file");
        }
        if (argsList.contains("-unit-graph")) {
            String arg = argsList.remove(argsList.indexOf("-unit-graph")+1);
            assert arg.equals("brief") || arg.equals("trap") : "invalid argument to -unit-graph";
            driver.Options.unitGraph = arg;
            argsList.remove("-unit-graph");
        }
        if (argsList.contains("-unique-paths")) {
            String arg = argsList.remove(argsList.indexOf("-unique-paths")+1);
            assert arg.equals("y") || arg.equals("n") : "invalid argument to -unique-paths";
            driver.Options.uniquePaths = arg.equals("y");
            argsList.remove("-unique-paths");
        }
        if (argsList.contains("-obey-android-entry-points")) {
            String arg = argsList.remove(argsList.indexOf("-obey-android-entry-points")+1);
            assert arg.equals("y") || arg.equals("n") : "invalid argument to -obey-android-entry-points";
            driver.Options.obeyAndroidEntryPoints = arg.equals("y");
            argsList.remove("-obey-android-entry-points");
        }
        if (argsList.contains("-validate-sequences")) {
            String arg = argsList.remove(argsList.indexOf("-validate-sequences")+1);
            assert arg.equals("y") || arg.equals("n") : "invalid argument to -validate-sequences";
            driver.Options.validateSequences = arg.equals("y");
            argsList.remove("-validate-sequences");
        }
        if (argsList.contains("-print-branches")) {
            driver.Options.printBranches = true;
            argsList.remove("-print-branches");
        }
        if (argsList.contains("-print-location")) {
            driver.Options.printLocation = true;
            argsList.remove("-print-location");
        }
        if (argsList.contains("-print-sequence-startend")) {
            driver.Options.printSequenceStartEnd = true;
            argsList.remove("-print-sequence-startend");
        }
        if (argsList.contains("-print-JSON")) {
            driver.Options.printJSON = true;
            argsList.remove("-print-JSON");
        }


        seqExt.begin();
        jtp.add(new Transform("jtp.sequence_extractor", seqExt));
        soot.Main.main(argsList.toArray(new String[0]));
        seqExt.end();
    }
}
