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

import soot.jimple.Stmt;

/** A transition in a monitor */
public class Transition {

    private MonitorState from;
    private MonitorState to;
    private Predicate predicate;

    public Transition(MonitorState from, MonitorState to, Predicate predicate) {
        this.from = from;
        this.to = to;
        this.predicate = predicate;

        assert predicate != null : "invalid predicate in trans " + from + "->" + to;
    }

    public MonitorState from() {
        return from;
    }

    public MonitorState to() {
        return to;
    }

    public boolean enabled(StmtInstance stmt) {
        return predicate.enabled(stmt);
    }
}
