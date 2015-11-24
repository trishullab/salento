/* Author: Vijay Murali */

package pliny_soot;

/** Configurable options for pliny-soot */
public final class Options
{
    private Options() { }

    /** Maximum number of sequences from components */
    public static final int MAX_SEQS = 100;

    /** maximum length of sequence */
    public static final int MAX_LEN = 1000;

    /** Should not extract sequences from these packages */
    public static String[] avoidPackages =
        {
            "android.",
            "com.google.",
            "java.",
        };
}
