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

import soot.Value;

import soot.jimple.Stmt;
import soot.jimple.InvokeExpr;
import soot.jimple.StringConstant;

import java.util.regex.Pattern;
import java.util.regex.Matcher;
import java.util.regex.PatternSyntaxException;

/** A predicate on an (string) argument's form represented as a regular expression */
public class ArgValueREPredicate implements Predicate {

    private int arg;
    private Pattern regexp;
    private boolean enabledOnNegation;

    public ArgValueREPredicate(String s) {
        Pattern regex = Pattern.compile("(!)?\\$(\\d+) \"(.*)\"");
        Matcher m = regex.matcher(s);

        assert m.matches() : "malformed RE predicate: " + s;
        try {
            enabledOnNegation = (m.group(1) != null);
            arg = Integer.parseInt(m.group(2));
            regexp = Pattern.compile(m.group(3));
        } catch(NumberFormatException e) {
            assert false : "invalid argument number: " + s;
        } catch (PatternSyntaxException e) {
            assert false: "invalid pattern syntax: " + s;
        }
    }

    public static void apply(Stmt stmt) {
    }

    public boolean enabled(StmtInstance stmtIns) {
        Stmt stmt = stmtIns.getStmt();
        return (enabledOnNegation? ! enabled_aux(stmt) : enabled_aux(stmt));
    }

    private boolean enabled_aux(Stmt stmt) {
        if (!stmt.containsInvokeExpr())
            return false;

        InvokeExpr invokeExpr = stmt.getInvokeExpr();
        int argCount = invokeExpr.getArgCount();

        if (arg > argCount)
            return false;

        Value argVal = invokeExpr.getArg(arg-1);
        if (! (argVal instanceof StringConstant))
            return false;

        String str = ((StringConstant) argVal).value;
        return regexp.matcher(str).matches();
    }
}
