/* Author: Vijay Murali */

package driver;

import java.util.List;
import java.util.ArrayList;

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

    /* Static list of statements that serves as a map from stmt -> index */
    private static List<Stmt> stmtLocationMap = new ArrayList<Stmt>();

    private Stmt stmt;

    public LocationInfo(Stmt stmt, SootMethod method) {
        this.stmt = stmt;
        this.fileTag = (SourceFileTag) method.getDeclaringClass().getTag("SourceFileTag");
        this.lnTag = (LineNumberTag) (stmt.getTag("LineNumberTag"));

        if (Options.printLocation) {
            if (fileTag != null && lnTag != null) {
                this.fileName = getFileName();
                this.lineNum = getLineNumber();
            }
            else
                if (! stmtLocationMap.contains(stmt))
                    stmtLocationMap.add(stmt);
        }
    }

    public String getFileName() {
        return fileTag.getSourceFile();
    }

    public Integer getLineNumber() {
        return new Integer(lnTag.getLineNumber());
    }

    @Override
    public String toString() {
        if (!Options.printLocation)
            return "";
        else if (fileTag != null && lnTag != null)
            return getFileName() + "@" + getLineNumber();
        else return "LOC" + stmtLocationMap.indexOf(stmt);
    }
}
