#!/usr/bin/env python

from topoDiscovery import *
from defaultPath import *
from flowMeasure import *
from monitoringTools import *

import time

# def turnOffCoreSwitches(k, NCore):
#     totalCore = (k/2)**2   
#     while(totalCore > NCore):
#         removeLinksOfDevice(totalCore, 1)
#         totalCore -=1

# def turnOnCoreSwitches(k, NCore):
#     totalCore = 1  
#     while(totalCore < NCore):
#         addLinksOfDevice(totalCore, 1)
#         totalCore +=1

# def turnOnAggrSwicthes

if __name__ == "__main__":
    # Initialize Topo Manger, get the latest version of the topology and set default paths
    if (len(sys.argv) != 2):
        print("Usage : python main.py k")
    else: 
        # Initialize Topo Manger and get the latest version of the topology
        k = int(sys.argv[1]) # Get fat-tree degree from args
        if k==4:
            from deviceList.deviceList_k4 import *
        if k==8:
            from deviceList.deviceList_k8 import *

    topo = TopoManager(k, CORE_DEVICES, AGREGATION_DEVICES, EDGE_DEVICES)
    
    # previousNCore = k
    # previousNAgg_p = [2,2,2,2]
    # installDefaultPaths(topo, k, [2,2,2,2])

    # time.sleep(5)

    # while(1):
        # topo = TopoManager(k, CORE_DEVICES, AGREGATION_DEVICES, EDGE_DEVICES)
        # [NCore, NAgg_p] = getFlowStat(topo, 1.0)
        # if (previousNCore>NCore or previousNAgg_p>NAgg_p):
        #     if previousNCore>NCore:
        #         turnOffCoreSwitches(k, NCore)
        #     if previousNAgg_p>NAgg_p:
        #         # turn off aggr
        #         d
        #     installDefaultPaths(topo, NCore, NAgg_p)  
            
        # if (previousNCore<NCore or previousNAgg_p<NAgg_p):
        #     # TODO: turn on
        #     if previousNCore<NCore:
        #         turnOnCoreSwitches(k, NCore)
        #     if previousNAgg_p<NAgg_p:

        #     time.sleep(1)
        # installDefaultPaths(topo, NCore, NAgg_p)

        # time.sleep(10) # Wait 10 sec


    [NCore, NAgg_p] = getFlowStat(topo, 1.0)
    installDefaultPaths(topo, NCore, NAgg_p)