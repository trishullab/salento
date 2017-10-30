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

package driver.predicates;

import driver.*;

import soot.jimple.Stmt;
import soot.SootMethod;

import soot.jimple.Stmt;
import soot.jimple.InvokeExpr;

/** A predicate that enables/disables on a particular API call */
public class CallPredicate implements Predicate {

    private String method;

    public CallPredicate(String method) {
        this.method = method;
    }

    public static void apply(Stmt stmt) {
    }

    public boolean enabled(StmtInstance stmtIns) {
        Stmt stmt = stmtIns.getStmt();
        if (!stmt.containsInvokeExpr())
            return false;

        InvokeExpr invokeExpr = stmt.getInvokeExpr();
        SootMethod callee = invokeExpr.getMethod();

        return Util.mySignature(callee).equals(method);
    }
}
