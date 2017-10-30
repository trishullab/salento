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

import soot.Unit;

/** Path of choice points used for SequenceExtractor */
public class Path
{
    private List<Unit> choicePoints;

    public Path() {
        choicePoints = new ArrayList<Unit>();
    }

    public void addChoicePoint(Unit u) {
        choicePoints.add(u);
    }

    public void clear() {
        choicePoints.clear();
    }

    public List<Unit> getChoicePoints() {
        return choicePoints;
    }

    public int size() {
        return choicePoints.size();
    }

    @Override
    public String toString() {
        return choicePoints.toString();
    }

    @Override
    public boolean equals(Object o) {
        if (o == null || ! (o instanceof Path)) return false;
        if (o == this) return true;
        
        Path p = (Path) o;
        List<Unit> cp = p.getChoicePoints();
        if (cp.size() != choicePoints.size()) return false;

        for (int i = 0; i < choicePoints.size(); i++)
            if (choicePoints.get(i) != cp.get(i))
                return false;
        return true;
    }

    @Override
    public int hashCode() {
        return choicePoints.size();
    }
}
