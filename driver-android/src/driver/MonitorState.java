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

/** State of a particular monitor automaton
 *  For now it's just a wrapper for an Integer */
public class MonitorState {

    private int state;

    public MonitorState(int state) {
        this.state = state;
    }

    public int getState() {
        return state;
    }

    @Override
    public boolean equals(Object o) {
        if (o == null || !(o instanceof MonitorState))
            return false;
        MonitorState ps = (MonitorState) o;
        return this.state == ps.getState();
    }

    @Override
    public int hashCode() {
        return state;
    }

    @Override
    public String toString() {
        return "" + state;
    }
}
