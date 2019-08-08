#!/usr/bin/env python

from topoDiscovery import *
from defaultPath import *
from flowMeasure import *

import time


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
    
    
    installDefaultPaths(topo, k, [2,2,2,2])

    time.sleep(5)

    while(1):
        topo = TopoManager(k, CORE_DEVICES, AGREGATION_DEVICES, EDGE_DEVICES)
        [NCore, NAgg_p] = getFlowStat(topo, 1)
        installDefaultPaths(topo, NCore, NAgg_p)


        time.sleep(10) # Wait 10 sec
