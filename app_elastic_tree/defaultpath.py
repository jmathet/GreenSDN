from topo_discovery import *
from monitoringTools import *


def installDefaultPaths(topo):
    density = k/2 # Number of devices connected to 1 edge switch

    # EDGE LAYER SWITCHES
    for host in topo.hostLocation:
        # Downstream traffic
        switchId = topo.hostLocation[host].split("::")[0]
        portId = topo.hostLocation[host].split("::")[1]
        # print(host)
        # print(switchId)
        # print(portId)
        hostIP = host + "/32"
        postFlowRule_dstIP_outPort(switchId, str(hostIP), str(portId))

    #TODO: Upstream traffic

    # AGGREGATION LAYER SWITCHES
    for sw in AGREGATION_DEVICES:
        
    
    
def main():
    # Initialize Topo Manger and get the latest version of the topology
    topo = TopoManager()
    installDefaultPaths(topo)

    return 0

if __name__ == "__main__":
    main()