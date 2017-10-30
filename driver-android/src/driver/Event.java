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

import com.google.gson.annotations.Expose;
import com.google.gson.annotations.SerializedName;

/** A pair of API call and list of monitor states */
public class Event
{
    private SootMethod sigma;
    private List<MonitorState> monitorStates;
    private LocationInfo location;

    /* Primitives for Gson */
    @Expose
    @SerializedName("call") 
    private String sigma_;
    @Expose
    @SerializedName("states") 
    private List<Integer> monitorStates_;
    @Expose
    @SerializedName("branches")
    private Integer numBranches;
    @Expose
    @SerializedName("location")
    private String location_;

    /* Branch event - only record number of branches */
    public Event(Integer numBranches) {
        this.numBranches = numBranches;
    }

    /* Call event - record call, states and location */
    public Event(SootMethod sigma, List<MonitorState> monitorStates, LocationInfo location) {
        this.sigma = sigma;
        this.monitorStates = monitorStates;
        if (Options.printLocation) {
            this.location = location;
            this.location_ = location.toString();
        }

        this.sigma_ = Util.mySignature(sigma);
        this.monitorStates_ = new ArrayList<Integer>();
        for (MonitorState s : monitorStates)
            this.monitorStates_.add(s.getState());
    }

    public Integer getNumBranches() {
        return numBranches;
    }

    public SootMethod getSigma() {
        return sigma;
    }

    public List<MonitorState> getMonitorStates() {
        return monitorStates;
    }

    public LocationInfo getLocationInfo() {
        return location;
    }

    @Override
    public String toString() {
        String s;
        if (numBranches != null)
            s = numBranches.toString();
        else {
            s = Util.mySignature(sigma) + "[";
            for (MonitorState ps : monitorStates)
                s += ps.toString() + ",";
            if (s.charAt(s.length() - 1) == ',')
                s = s.substring(0, s.length() - 1);
            s += "][" + (location != null? location : "") + "]";
        }
        return s;
    }
}
