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
