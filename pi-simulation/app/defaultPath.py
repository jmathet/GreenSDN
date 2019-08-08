#!/usr/bin/env python

from topoDiscovery import *
from monitoringTools import *
import math
from runElasticTree import *
from deviceList.deviceList_Pi import *


def installDefaultPaths(topo, Ncore, NAgg_p):
    DownPriority = 600
    UpPriority = 500
    k = topo.degree
    density = k/2 # Number of devices in each pod layer

    # EDGE LAYER SWITCHES
    for s in range(len(EDGE_DEVICES)):
        edgeSwitchNbinPod = ((s) % density) +1
        sw = EDGE_DEVICES[s]
        podNb = int(math.ceil((s+1)/float(density)))
        subsubNet = "10." + str(podNb) + "." + str(edgeSwitchNbinPod) + "."
        edgeDensity = HOST_IN_EDGE_DENSITY[s] # Number of hosts connected to the edge swicth s
        #for h in range(1, density+1):
        for h in range(1, edgeDensity+1):
            # Downstream traffic
            host = subsubNet + str(h)
            outPort = topo.hostLocation[host].split("::")[1]
            hostIP = host + "/32"
            postFlowRule_dstIP_outPort(sw, str(hostIP), str(outPort), DownPriority)

            # Upstream Traffic
            host = subsubNet + str(h)
            if (h > NAgg_p[podNb-1]):
                offset = NAgg_p[podNb-1]
            else:
                offset = h
            aggrSwitchID = AGREGATION_DEVICES[(podNb-1)*density + offset-1] 
            outPort = topo.linkPorts[sw + "::" + aggrSwitchID].split("::")[0] 
            hostIP = host + "/32"
            postFlowRule_srcIP_outPort(sw, hostIP, outPort, UpPriority)
    print(">> EDGE LAYER : down and up traffic OK")

    # AGGREGATION LAYER SWITCHES
    c = 0
    for s in range(len(AGREGATION_DEVICES)):
        sw = AGREGATION_DEVICES[s]
        podNb = int(math.ceil((s+1)/float(density)))
        subNet = "10." + str(podNb) + "."
        aggrDensity = HOST_IN_EDGE_DENSITY[s]
        #for i in range(1, density+1): # For each subsubNet in the current pod
        for i in range(1, aggrDensity+1):
            subsubNet = subNet + str(i) + "." # example : 10.1.1.
            subsubNetIP = subsubNet + "0/24" # example : 10.1.1.0/24 

            # Downstream traffic
            edgeSwitchId = topo.hostLocation[subsubNet + "1"].split("::")[0] # Edge Switch ID connected to 10.1.1.0 host network
            outPort = topo.linkPorts[sw + "::" + edgeSwitchId].split("::")[0] # Port between the current Aggr switch and the edge switch required
            postFlowRule_dstIP_outPort(sw, str(subsubNetIP), str(outPort), DownPriority)

            # Upstream traffic
            coreSwicthID = CORE_DEVICES[c]
            outPort = topo.linkPorts[sw + "::" + coreSwicthID].split("::")[0]
            postFlowRule_srcIP_outPort(sw, subsubNetIP, outPort, UpPriority)
            if (c < len(CORE_DEVICES)-1): 
                c += 1
            else:
                c = 0
    print(">> AGGREAGTION LAYER : down and up traffic OK")

    # CORE LAYER SWITCHES
    for s in range(Ncore):
        sw = CORE_DEVICES[s]

        # Downstream traffic
        offset = 0
        if (s == 1):
            offset = 1
        # print(str(s) + " - " + str(offset))
        for pod in range(1, k/2+1):
            subNet = "10." + str(pod) + ".0.0/16"
            aggrSwitchID = AGREGATION_DEVICES[(pod-1)*density + offset] # Aggr swicth connected to the current pod
            outPort = topo.linkPorts[sw + "::" + aggrSwitchID].split("::")[0]
            postFlowRule_dstIP_outPort(sw, str(subNet), str(outPort), DownPriority)

        # Up traffic (internet)

        postFlowRule_dstIP_outPort(sw, "10.0.0.1/32", str(outPort), UpPriority)
        outPort = topo.hostLocation["10.0.0.1"].split("::")[1]
        postFlowRule_internet(sw, str(outPort))
        print("coucou")
    print(">> CORE LAYER : down traffic OK")

if __name__ == "__main__":
    # Initialize Topo Manger, get the latest version of the topology and set default paths
    k=4
    topo = TopoManager(k)
    installDefaultPaths(topo, 2, [2,2])