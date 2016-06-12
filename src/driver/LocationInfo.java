/* Author: Vijay Murali */

package driver;

import soot.*;
import soot.jimple.Stmt;

import soot.tagkit.SourceFileTag;
import soot.tagkit.LineNumberTag;

/** Information about the location of an event */
public class LocationInfo
{
    private SourceFileTag fileTag;
    private LineNumberTag lnTag;

    private String fileName;
    private Integer lineNum;

    public LocationInfo(Stmt stmt, SootMethod method) {
        this.fileTag = (SourceFileTag) method.getDeclaringClass().getTag("SourceFileTag");
        this.lnTag = (LineNumberTag) (stmt.getTag("LineNumberTag"));

        this.fileName = getFileName();
        this.lineNum = getLineNumber();
    }

    public String getFileName() {
        return fileTag.getSourceFile();
    }

    public Integer getLineNumber() {
        return new Integer(lnTag.getLineNumber());
    }

    @Override
    public String toString() {
        if (!Options.printLocation || fileTag == null || lnTag == null)
            return "";
        else
            return getFileName() + "@" + getLineNumber();
    }
}
