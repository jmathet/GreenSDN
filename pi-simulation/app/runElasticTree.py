#!/usr/bin/env python

from topoDiscovery import *
from defaultPath import *
from flowMeasure import *
from deviceList.deviceList_Pi import *
from powerControl import *

import time


if __name__ == "__main__":
    # Initialize Topo Manger, get the latest version of the topology and set default paths
    k=4
    topo = TopoManager(k)
    
    
    installDefaultPaths(topo, k, [2,2,2,2])

    time.sleep(5)

    while(1):
        [NCore, NAgg_p] = getFlowStat(topo, 1)
        powerControl(NCore, NAgg_p)
        time.sleep(30) # Wait 10 sec
        installDefaultPaths(topo, NCore, NAgg_p)

        

        time.sleep(30) # Wait 20 sec
