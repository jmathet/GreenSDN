import requests
from datetime import datetime
import time
import math
import sys

from monitoringTools import *


def getFlowStat(k, r):
    # r : link rate paraneter (to set the desired average link utilisation)
    density = k/2
    
    listLAgg_down_p = [] # Number of down links required to suport the down-traffic (where the pod number p is the list index)
    listLAgg_up_p = [] # Number of down links required to suport the up-traffic (where the pod number p is the list index)
    NAgg_p = [] # Minimum number of active aggregation switches reauired to support traffic (where the pod number p is the list index)
    
    for p in range(0,k): # For each pod
        listLEdge_up_p_e = [] # Number of links for edge swicth e in pod p (where 2*p+e is the list index)
        for j in range(0,density): # For each edge switch in the pod p 
            rateUP = []
            rateDOWN = []
            for i in range(0, density): # For each aggregation switch connected to the edge switch Ej in the pod p
                flowStat = getFlowStatFromDevice(EDGE_DEVICES[density*p+j], str(i+1)) #TODO: recuperer le port de la topology
                rateUP_i = flowStat["loads"][0]["rate"] # rate between edge Ej and aggreation Ai of the pod p in the up direction
                rateUP.append(rateUP_i)
                rateDOWN_i = flowStat["loads"][1]["rate"] # rate between edge Ej and aggreation Ai of the pod p in the down direction 
                rateDOWN.append(rateDOWN_i)
                print(rateDOWN_i)

            LEdge_up_p_e = (sum(rateUP)) # total rate up in ? TODO: ajouter math.ceil
            LEdge_down_p_e = (sum(rateDOWN)) # total rate down in ? TODO: ajouter math.ceil
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
                url = FLOWSSTAT_URL + "?device=" + AGREGATION_DEVICES[density*p+j] + "&port=" + str(i+1) #TODO: recuperer le port de la topology
                flowStat = getJsonData(url)
                #print(json.dumps(flowStat, indent=4, sort_keys=True)) # TODO: a supprimer
                rateUP_i = flowStat["loads"][0]["rate"] # Rate between aggregation switch Aj of the pod p in the up direction and Ci 
                rateUP.append(rateUP_i)
                rateDOWN_i = flowStat["loads"][1]["rate"] # Rate between aggregation switch Aj of the pod p in the down direction and Ci 
                rateDOWN.append(rateDOWN_i)

            LAgg_up_p = LAgg_up_p + sum(rateUP) # total rate up in ?
            LAgg_down_p = LAgg_down_p + sum(rateDOWN) # total rate down in ?

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
        [NCore, NAgg_p] = getFlowStat(k, 1)
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