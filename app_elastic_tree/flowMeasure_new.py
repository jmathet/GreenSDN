import requests
from datetime import datetime
import time
import math
import sys

from monitoringTools import *
from topo_discovery import *


def getFlowStat(topo, r):
    # topo : topology get from ONOS
    # r : link rate paraneter (to set the desired average link utilisation)
    k = topo.degree
    density = k/2
    
    listLAgg_down_p = [] # Number of down links required to suport the down-traffic (where the pod number p is the list index)
    listLAgg_up_p = [] # Number of down links required to suport the up-traffic (where the pod number p is the list index)
    NAgg_p = [] # Minimum number of active aggregation switches reauired to support traffic (where the pod number p is the list index)
    
    allFlowStat = getAllFlowStat()

    for p in range(0,k): # For each pod
        listLEdge_up_p_e = [] # Number of links for edge swicth e in pod p (where 2*p+e is the list index)
        for j in range(0,density): # For each edge switch in the pod p 
            rateUP = []
            rateDOWN = []
            for i in range(0, density): # For each aggregation switch connected to the edge switch Ej in the pod p
                edgeSitchID = EDGE_DEVICES[density*p+j]
                aggrSwitchID = AGREGATION_DEVICES[density*p +i]
                srcPort = topo.linkPorts[edgeSitchID + "::" + aggrSwitchID].split("::")[0] 
                destPort = topo.linkPorts[edgeSitchID + "::" + aggrSwitchID].split("::")[1] 
                flowStatUP = getFlowStatLink(allFlowStat, edgeSitchID, srcPort) 
                flowStatDOWN = getFlowStatLink(allFlowStat, aggrSwitchID, destPort) 
                rateUP_i = flowStatUP["rate"] # rate between edge Ej and aggreation Ai of the pod p in the up direction
                rateUP.append(rateUP_i)
                rateDOWN_i = flowStatDOWN["rate"] # rate between edge Ej and aggreation Ai of the pod p in the down direction 
                rateDOWN.append(rateDOWN_i)

            LEdge_up_p_e = (sum(rateUP))/(2.0**20)*8*2 # total rate up in ? TODO: ajouter math.ceil
            LEdge_down_p_e = (sum(rateDOWN))/(2.0**20)*8*2 # total rate down in ? TODO: ajouter math.ceil
            listLEdge_up_p_e.append(LEdge_up_p_e)

            LEdge_p_e = max(LEdge_up_p_e,LEdge_down_p_e,1)
            # FIXME: update units
            print("Number of links needs between the edge swicth " + str(density*p+j +1) + " and the aggregation layer")
            print("LEdge_up_p_e = " + str(LEdge_up_p_e) + " ?bits/sec")
            print("LEdge_down_p_e = " + str(LEdge_down_p_e) + " ?bits/sec")
            print("LEdge_p_e = " + str(LEdge_p_e) + " (1 ?bits/sec links)")
        
        NAgg_up_p = max(listLEdge_up_p_e)
        print("[POD " + str(p+1) + " ] " + "Minimum number of aggregation switches (to satisfy up traffic) = " + str(NAgg_up_p))

        
        LAgg_up_p = 0
        LAgg_down_p = 0
        for j in range(0,density): # For each aggregation switch in the pod p 
            rateUP = []
            rateDOWN = []
            for i in range(0, density): # For each edge switch connected to the aggregation switch Aj of the pod p
                x = density*p+j
                aggrSwitchID = AGREGATION_DEVICES[x]
                coreSwitchID = CORE_DEVICES[(x%density)*density +i]
                #print("\n" + str(x+1) + " - " + str((x%density)*density +i+1))
                
                srcPort = topo.linkPorts[aggrSwitchID + "::" + coreSwitchID].split("::")[0] 
                destPort = topo.linkPorts[aggrSwitchID + "::" + coreSwitchID].split("::")[1] 
                flowStatUP = getFlowStatLink(allFlowStat, aggrSwitchID, srcPort) 
                flowStatDOWN = getFlowStatLink(allFlowStat, coreSwitchID, destPort) 
                rateUP_i = flowStatUP["rate"] # Rate between aggregation switch Aj of the pod p in the up direction and Ci 
                rateUP.append(rateUP_i)
                rateDOWN_i = flowStatDOWN["rate"] # Rate between aggregation switch Aj of the pod p in the down direction and Ci 
                rateDOWN.append(rateDOWN_i)

            LAgg_up_p = LAgg_up_p + sum(rateUP)/(2.0**20)*8*2 # total rate up in ?
            LAgg_down_p = LAgg_down_p + sum(rateDOWN)/(2.0**20)*8*2 # total rate down in ?

        listLAgg_up_p.append(LAgg_up_p)


        LAgg_p = max((LAgg_up_p),(LAgg_down_p),1) # TODO: ajouter math.ceil *2     
        NAgg_down_p = (LAgg_down_p/(k/2)) # TODO: ajouter math.ceil
        NAgg_p.append(max(NAgg_up_p,NAgg_down_p,1))
        # FIXME: update units
        print("Number of links needs between aggregation swicthes of the pod " + str(p+1) + " and the core layer")
        print("LAgg_up_p = " + str(LAgg_up_p) + " ?bits/sec")
        print("LAgg_down_p = " + str(LAgg_down_p) + " ?bits/sec")
        print("LAgg_p = " + str(LAgg_p) + " (1 ?bits/sec links)")
        print("******************************NEXT POD********************************************")
    
    NCore = (max(NAgg_p)) # Minimum of core switches to satisfy the demand TODO: ajouter math.ceil

    print("NAgg_p = " + str(NAgg_p))
    print("Ncore = " + str(NCore))

    return [NCore, NAgg_p]





if __name__ == "__main__":
    if (len(sys.argv) != 2):
        print("Usage : python flowMeasure.py k")
    else: 
        k = int(sys.argv[1])
        if k==4:
            from deviceList_k4 import *
        if k==8:
            from deviceList_k8 import *

        topo = TopoManager(k)
        [NCore, NAgg_p] = getFlowStat(topo, 1)

        print("Ncore = " + str(NCore))
        print("NAgg_p = " + str(NAgg_p))

    #print(json.dumps(r, indent=4, sort_keys=True))
    '''
    boolean flag = False
    delta = 0
    while (flag && delta < 600) {
        send = send(PORTSTAT_URL,  )
        print send
        time.sleep(0.7)
        delta += 1
    }
    '''