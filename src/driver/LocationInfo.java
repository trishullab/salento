/* Author: Vijay Murali */

package driver;

import soot.*;
import soot.jimple.Stmt;

import soot.tagkit.SourceFileTag;
import soot.tagkit.LineNumberTag;

import com.google.gson.annotations.Expose;
import com.google.gson.annotations.SerializedName;

/** Information about the location of an event */
public class LocationInfo
{
    private SourceFileTag fileTag;
    private LineNumberTag lnTag;

    /* Primitives for Gson */
    @Expose
    @SerializedName("file") 
    private String fileName;
    @Expose
    @SerializedName("line") 
    private Integer lineNum;

    public LocationInfo(Stmt stmt, SootMethod method) {
        this.fileTag = (SourceFileTag) method.getDeclaringClass().getTag("SourceFileTag");
        this.lnTag = (LineNumberTag) (stmt.getTag("LineNumberTag"));

        if (Options.printLocation) {
            this.fileName = getFileName();
            this.lineNum = getLineNumber();
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
        if (!Options.printLocation || fileTag == null || lnTag == null)
            return "";
        else
            return getFileName() + "@" + getLineNumber();
    }
}
