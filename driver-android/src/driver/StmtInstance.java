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

import soot.SootClass;
import soot.jimple.Stmt;

/** A thin wrapper for an instance of a statement along a path with some additional info */
public class StmtInstance {

    private Stmt stmt;
    private SootClass exceptionThrown;

    public StmtInstance (Stmt stmt) {
        this.stmt = stmt;
    }

    public Stmt getStmt() {
        return stmt;
    }

    public boolean isExceptionThrown() {
        return exceptionThrown != null;
    }

    public SootClass getExceptionThrown() {
        return exceptionThrown;
    }

    public void setExceptionThrown(SootClass e) {
        this.exceptionThrown = e;
    }
}
