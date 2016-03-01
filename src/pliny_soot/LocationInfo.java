/* Author: Vijay Murali */

package pliny_soot;

import soot.*;
import soot.jimple.Stmt;

import soot.tagkit.SourceFileTag;
import soot.tagkit.LineNumberTag;

/** Information about the location of an event */
public class LocationInfo
{
    private SourceFileTag fileTag;
    private LineNumberTag lnTag;

    public LocationInfo(Stmt stmt, SootMethod method) {
        this.fileTag = (SourceFileTag) method.getDeclaringClass().getTag("SourceFileTag");
        this.lnTag = (LineNumberTag) (stmt.getTag("LineNumberTag"));
    }

    public String getFileName() {
        return fileTag.getSourceFile();
    }

    public int getLineNumber() {
        return lnTag.getLineNumber();
    }

    @Override
    public String toString() {
        if (!Options.printLocation || fileTag == null || lnTag == null)
            return "";
        else
            return getFileName() + "@" + getLineNumber();
    }
}
