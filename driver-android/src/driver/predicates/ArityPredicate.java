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

import soot.jimple.Stmt;
import soot.jimple.InvokeExpr;

import java.util.regex.Pattern;
import java.util.regex.Matcher;

/** A predicate on the arity of a particular API call */
public class ArityPredicate implements Predicate {

    private char op;
    private int arity;

    public ArityPredicate(String s) {
        Pattern regex = Pattern.compile("(=|<|>)(\\d+)");
        Matcher m = regex.matcher(s);

        assert m.matches() : "malformed arity predicate: " + s;
        try {
            op = m.group(1).charAt(0);
            arity = Integer.parseInt(m.group(2));
        } catch(NumberFormatException e) {
            assert false : "invalid arity: " + s;
        }
    }

    public static void apply(Stmt stmt) {
    }

    public boolean enabled(StmtInstance stmtIns) {
        Stmt stmt = stmtIns.getStmt();
        if (!stmt.containsInvokeExpr())
            return false;

        InvokeExpr invokeExpr = stmt.getInvokeExpr();
        int argCount = invokeExpr.getArgCount();

        switch (op) {
            case '=': return argCount == arity;
            case '>': return argCount > arity;
            case '<': return argCount < arity;
            default:  return false;
        }
    }
}
