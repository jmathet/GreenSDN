#!/usr/bin/env python

import requests
from datetime import datetime
import time
import math
import sys
import numpy as np

from monitoringTools import *
from topoDiscovery import *


def getFlowStat(topo, r):
    # topo : topology get from ONOS
    # r : link rate paraneter (to set the desired average link utilisation)
    k = topo.degree
    density = k/2

    EDGE_DEVICES = topo.EDGE_DEVICES
    AGREGATION_DEVICES = topo.AGGREGATION_DEVICES
    CORE_DEVICES = topo.CORE_DEVICES
    
    listLAgg_down_p = [] # Number of down links required to suport the down-traffic (where the pod number p is the list index)
    listLAgg_up_p = [] # Number of down links required to suport the up-traffic (where the pod number p is the list index)
    NAgg_p = [] # Minimum number of active aggregation switches required to support traffic in the pod (where the pod number p is the list index)
    matrixLAgg_up_p_c = np.zeros((k,density)) # 
    matrixLAgg_down_p_c = np.zeros((k,density))
    allFlowStat = getAllFlowStat() # Get snapshot of the current traffic in the network

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

                rateUP_i = flowStatUP["rate"] # Rate between edge Ej and aggreation Ai of the pod p in the up direction
                rateUP.append(rateUP_i)

                rateDOWN_i = flowStatDOWN["rate"] # Rate between edge Ej and aggreation Ai of the pod p in the down direction 
                rateDOWN.append(rateDOWN_i)

                
                print("flowStatUP   E-A = " + str(rateUP_i*(8e-9)*2) + " " + str(flowStatUP["valid"]) + " " + str(flowStatUP["time"]))
                print("flowStatDOWN E-A = " + str(rateDOWN_i*(8e-9)*2) + " " + str(flowStatDOWN["valid"]) + " " + str(flowStatDOWN["time"]))
                    
            LEdge_up_p_e = math.ceil(sum(rateUP)*(8e-9)*2/r) # Total rate up in Gbits/sec 
            LEdge_down_p_e = math.ceil(sum(rateDOWN)*(8e-9)*2/r) # Total rate down in Gbits/sec
            listLEdge_up_p_e.append(LEdge_up_p_e)

            LEdge_p_e = max(LEdge_up_p_e,LEdge_down_p_e,1)
            # print("Number of links needs between the edge swicth " + str(density*p+j +1) + " and the aggregation layer")
            # print("LEdge_up_p_e = " + str(LEdge_up_p_e) + " Gbits/sec")
            # print("LEdge_down_p_e = " + str(LEdge_down_p_e) + " Gbits/sec")
            # print("LEdge_p_e = " + str(LEdge_p_e) + " (1 Gbits/sec links)")
        NAgg_up_p = max(listLEdge_up_p_e)
        print("\n[POD" + str(p+1) + "] " + "Minimum number of aggregation switches (to satisfy UP traffic) = " + str(NAgg_up_p))

        LAgg_up_p = 0.0

        for j in range(0,density): # For each aggregation switch in the pod p 
            rateUP = []
            rateDOWN = []
            for i in range(0, density): # For each core switch connected to the aggregation switch Aj of the pod p
                x = density*p+j
                aggrSwitchID = AGREGATION_DEVICES[x]
                coreSwitchID = CORE_DEVICES[(x%density)*density +i]

                srcPort = topo.linkPorts[aggrSwitchID + "::" + coreSwitchID].split("::")[0] 
                destPort = topo.linkPorts[aggrSwitchID + "::" + coreSwitchID].split("::")[1] 

                flowStatUP = getFlowStatLink(allFlowStat, aggrSwitchID, srcPort) 
                flowStatDOWN = getFlowStatLink(allFlowStat, coreSwitchID, destPort) 
                print(aggrSwitchID)
                print(srcPort)
                print(coreSwitchID)
                print(destPort)
                rateUP_i = flowStatUP["rate"] # Rate between aggregation switch Aj of the pod p in the up direction and Ci 
                rateUP.append(rateUP_i)
                
                print("flowStatUP   A-C = " + str(rateUP_i*(8e-9)*2) + " " + str(flowStatUP["valid"]) + " " + str(flowStatUP["time"]))
                print("flowStatDOWN A-C = " + str(rateDOWN_i*(8e-9)*2) + " " + str(flowStatDOWN["valid"]) + " " + str(flowStatDOWN["time"]))


                rateDOWN_i = flowStatDOWN["rate"] # Rate between aggregation switch Aj of the pod p in the down direction and Ci 
                rateDOWN.append(rateDOWN_i)

                # if flowStatUP["valid"]==False:
                #     print("ERROR flowStatUP A-C")
                # if flowStatDOWN["valid"]==False:
                #     print("ERROR flowStatDOWN A-C")

            LAgg_up_p = LAgg_up_p + sum(rateUP)*(8e-9)*2 # Total rate up in Gbits/sec
            
            matrixLAgg_up_p_c[p][j] = int(math.ceil(sum(rateUP)*(8e-9)*2/r)) # Total rate up in Gbits/sec
            matrixLAgg_down_p_c[p][j] = int(math.ceil(sum(rateDOWN)*(8e-9)*2/r)) # Total rate down in Gbits/sec

        # listLAgg_up_p.append(int(math.ceil(LAgg_up_p)))
        # LAgg_p = max(math.ceil(LAgg_up_p),math.ceil(LAgg_down_p),1) 
        NAgg_down_p = math.ceil(sum(matrixLAgg_down_p_c[p,:])/(k/2))
        NAgg_p.append(int(max(NAgg_up_p,NAgg_down_p,1)))

        # print("Number of links needs between aggregation swicthes of the pod " + str(p+1) + " and the core layer")
        print("LAgg_up_p = " + str(LAgg_up_p) + " Gbits/sec")
        # print("LAgg_down_p = " + str(LAgg_down_p) + " Gbits/sec")
        # print("LAgg_p = " + str(LAgg_p) + " (1 Gbits/sec links)")
        # print("******************************NEXT POD********************************************")
    
    # Minimum of core switches to satisfy the demand  in each core group
    NCore_c = np.max(matrixLAgg_up_p_c, axis=0) # Maxiumum of each column of the matrix 
    NCore_c = NCore_c.astype(int)

    if NCore_c[0]==0:
        NCore_c[0]=1 # MSPT

    # To avoid error because stats are wrong
    for NCore in NCore_c:
        if(NCore > k):
            NCore = k

    print("\nNAgg_p = " + str(NAgg_p))
    print("Ncore_c = ")
    print(NCore_c)

    f = open('text.out', 'wb')
    f.write("Ncore_c\n")
    for i in range(len(NCore_c)):
        f.write("%i\n" % (NCore_c[i]))
    f.write("Nagg_p\n")
    for i in range(len(NAgg_p)):
        f.write("%i\n" % (NAgg_p[i]))
    f.close()


    return NCore_c, NAgg_p


if __name__ == "__main__":
    if (len(sys.argv) != 2):
        print("Usage : python flowMeasure.py k")
    else: 
        k = int(sys.argv[1])
        if k==4:
            from deviceList.deviceList_k4 import *
        if k==8:
            from deviceList.deviceList_k8 import *

        topo = TopoManager(k)
        [NCore_c, NAgg_p] = getFlowStat(topo, 1)

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