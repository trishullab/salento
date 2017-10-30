/*
Copyright 2017 Rice University

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/
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
