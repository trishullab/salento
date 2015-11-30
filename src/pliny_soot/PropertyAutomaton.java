/* Author: Vijay Murali */

package pliny_soot;

import pliny_soot.properties.*;

import java.util.*;
import java.io.*;

import soot.Unit;

/** A property automaton */
public abstract class PropertyAutomaton {
    
    /** Read properties from a file and create the automata */
    public static List<PropertyAutomaton> readProperties(File f) throws FileNotFoundException, IOException {
        assert f.exists() : "cannot find properties file " + f;

        BufferedReader br = new BufferedReader(new FileReader(f));
        String line;
        List<PropertyAutomaton> properties = new ArrayList<PropertyAutomaton>();

        while ((line = br.readLine()) != null) {
            String type = line.substring(0, line.indexOf(':'));
            String s = line.substring(line.indexOf(':') +1);

            /* Add new property types here*/
            PropertyAutomaton p = null;
            if (type.equals("Equality"))
                p = new EqualityPropertyAutomaton();
            else
                assert false : "invalid property type " + type;

            p.parse(s);
            properties.add(p);
        }

        return properties;
    }

    /** Parse a line from the properties file */
    public abstract void parse(String s);

    /** Update automaton state given a statement */
    public abstract void apply(Unit stmt);
    
    /** Return the current automaton state */
    public abstract PropertyState getState();
}
