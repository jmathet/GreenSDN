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
            flowStat1 = getFlowStatFromDevice(EDGE_DEVICES[2*p+j], "1")
            flowStat2 = getFlowStatFromDevice(EDGE_DEVICES[2*p+j], "2")

            rate1_up = flowStat1["loads"][0]["rate"] # rate between edge j and a1 of the pod p in the up direction
            rate2_up = flowStat2["loads"][0]["rate"] # rate between edge j and a2 of the pod p in the up direction
            rate1_down = flowStat1["loads"][1]["rate"] # rate between edge j and a1 of the pod p in the down direction 
            rate2_down = flowStat2["loads"][1]["rate"] # rate between edge j and a2 of the pod p in the down direction

            LEdge_up_p_e = math.ceil((rate1_up + rate2_up)*8*10**(-9)) # total rate up in Gbits/sec
            LEdge_down_p_e = math.ceil((rate1_down + rate2_down)*8*10**(-9)) # total rate down in Gbits/sec

            listLEdge_up_p_e.append(LEdge_up_p_e)

            LEdge_p_e = max(LEdge_up_p_e/r,LEdge_down_p_e/r,1) # 1GBytes links

            print("Number of links needs between the edge swicth " + str(2*p+j) + " and the aggregation layer")
            print("LEdge_up_p_e = " + str(LEdge_up_p_e) + " Gbits/sec")
            print("LEdge_down_p_e = " + str(LEdge_down_p_e) + " Gbits/sec")
            print("LEdge_p_e = " + str(LEdge_p_e) + " (1 Gbits/sec links)")
        
        NAgg_up_p = max(listLEdge_up_p_e)
        print("[POD " + str(p) + " ] " + "Minimum number of aggregation switches (to satisfy up traffic) " + str(NAgg_up_p))

        
        LAgg_up_p = 0
        LAgg_down_p = 0
        for j in range(0,2): # For each aggregation switch in the pod p 
            url1 = FLOWSSTAT_URL + "?device=" + AGREGATION_DEVICES[2*p+j] + "&port=1"
            url2 = FLOWSSTAT_URL + "?device=" + AGREGATION_DEVICES[2*p+j] + "&port=2"

            flowStat1 = getJsonData(url1)
            flowStat2 = getJsonData(url2)

            rate1_up = flowStat1["loads"][0]["rate"] # rate between aggregation switch j and c1 of the pod p in the up direction
            rate2_up = flowStat2["loads"][0]["rate"] # rate between aggregation switch j and c2 of the pod p in the up direction
            rate1_down = flowStat1["loads"][1]["rate"] # rate between aggregation switch j and c1 of the pod p in the down direction 
            rate2_down = flowStat2["loads"][1]["rate"] # rate between aggregation switch j and c2 of the pod p in the down direction

            LAgg_up_p = LAgg_up_p + (rate1_up + rate2_up)*8*10**(-9) # total rate up in Gbits/sec
            LAgg_down_p = LAgg_down_p + (rate1_down + rate2_down)*8*10**(-9) # total rate down in Gbits/sec

        listLAgg_up_p.append(LAgg_up_p)
        LAgg_p = max(math.ceil(LAgg_up_p/r),math.ceil(LAgg_down_p/r),1) # 1GBytes links
       
        NAgg_down_p = math.ceil(LAgg_down_p/(k/2))
        NAgg_p.append(max(NAgg_up_p,NAgg_down_p,1))

        print("Number of links needs between aggregation swicthes of the pod " + str(p) + " and the core layer")
        print("LAgg_up_p = " + str(LAgg_up_p) + " Gbits/sec")
        print("LAgg_down_p = " + str(LAgg_down_p) + " Gbits/sec")
        print("LAgg_p = " + str(LAgg_p) + " (1 Gbits/sec links)")
        print("******************************NEXT POD********************************************")
    
    NCore = math.ceil(max(NAgg_p)) # Minimum of core switches to satisfy the demand

    print("NAgg_p = " + str(NAgg_p))
    print("Ncore = " + str(NCore))

    return [NCore, NAgg_p]


if __name__ == "__main__":
    print("DEPRESIATED : please not use it")
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