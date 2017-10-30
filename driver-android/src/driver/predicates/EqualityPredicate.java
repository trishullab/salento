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

import java.util.regex.Pattern;
import java.util.regex.Matcher;

/** An equality (or disequality) predicate */
public class EqualityPredicate implements Predicate {

    private int lArg;
    private int rArg;
    private boolean equal;
    private String method;

    public EqualityPredicate(String s) {
        Pattern regex = Pattern.compile("\\$(\\d+)(=|!=)\\$(\\d+)_(.*)");
        Matcher m = regex.matcher(s);

        assert m.matches() : "malformed equality predicate: " + s;
        try {
            lArg = Integer.parseInt(m.group(1));
            rArg = Integer.parseInt(m.group(3));
            equal = m.group(2).equals("=");
            method = m.group(4);
        } catch(NumberFormatException e) {
            assert false : "invalid argument number: " + s;
        }
    }

    public static void apply(Stmt stmt) {
    }

    public boolean enabled(StmtInstance stmtIns) {
        return false;
    }
}
