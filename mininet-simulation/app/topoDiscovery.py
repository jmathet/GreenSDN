#!/usr/bin/env python

import matplotlib.pyplot as plt
import networkx as nx
from monitoringTools import *
import logging
import sys

class TopoManager(object):
    def __init__(self, k, CORE_DEVICES, AGREGATION_DEVICES, EDGE_DEVICES):
        self.degree = k # Fat-tree degree
        self.G = nx.Graph()
        self.pos = None
        self.hosts = []
        self.devices = []
        self.linkPorts = {} # Stores Link Ports - use : linkPorts[srcDeviceId::dstDeviceId] = srcPort::dstPort
        self.hostLocation = {} # Stores Host Switch Ports
        self.deviceId_to_chassisId = {} # id is 'of:00000000000000a1', chassisID is 'a1'
        self.AGGREGATION_DEVICES = AGREGATION_DEVICES
        self.CORE_DEVICES = CORE_DEVICES
        self.EDGE_DEVICES = EDGE_DEVICES

        self.retrieve_topo_from_ONOS()

    def retrieve_topo_from_ONOS(self):
        
        ## Get devices list
        reply = getJsonData(CONTROLLER_URL + "/devices")
        if 'devices' not in reply:
            return
        for dev in reply['devices']:
            self.deviceId_to_chassisId[dev['id']] = dev['chassisId']
            self.G.add_node(dev['id'], type='device')
            self.devices.append(dev['id'])

        ## Get links list
        reply = getJsonData(CONTROLLER_URL + "/links")
        if 'links' not in reply:
            return
        for link in reply['links']:
            srcDevice = link['src']['device']
            srcPort = link['src']['port']
            dstDevice = link['dst']['device']
            dstPort = link['dst']['port']
            if 'annotations' in link and 'bandwidth' in link['annotations']: # FIXME: Utility of this bandwith
                    bw = int(link['annotations']['bandwidth']) * 1e6
            else:
                bw = DEFAULT_CAPACITY
            self.G.add_edge(srcDevice, dstDevice, **{'bandwidth': bw})

            srcToDst = srcDevice + b'::' + dstDevice 
            self.linkPorts[srcToDst] = srcPort + b'::' + dstPort

        ## Get hosts list
        reply = getJsonData(CONTROLLER_URL + "/hosts")
        if 'hosts' not in reply:
            return
        for host in reply['hosts']:
            self.G.add_node(host['id'], type='host')
            for location in host['locations']:
                self.G.add_edge(host['id'], location['elementId'],  **{'bandwidth': DEFAULT_ACCESS_CAPACITY})
                ip = host['ipAddresses'][0]
                switchId = location['elementId'] # Get swictth connected
                self.hostLocation[ip] = switchId + b'::' + location['port']
            self.hosts.append(host['id'])
            
        self.pos = nx.fruchterman_reingold_layout(self.G)

    def draw_topo(self, block=True):
        plt.figure()
        nx.draw_networkx_nodes(self.G, self.pos, nodelist=self.hosts, node_shape='o', node_color='w')
        nx.draw_networkx_nodes(self.G, self.pos, nodelist=self.CORE_DEVICES, node_shape='s', node_color='b')
        nx.draw_networkx_nodes(self.G, self.pos, nodelist=self.AGGREGATION_DEVICES, node_shape='s', node_color='g')
        nx.draw_networkx_nodes(self.G, self.pos, nodelist=self.EDGE_DEVICES, node_shape='s', node_color='k')
        nx.draw_networkx_labels(self.G.subgraph(self.hosts), self.pos, font_color='k')
        nx.draw_networkx_labels(self.G.subgraph(self.devices), self.pos, font_color='w',
                                labels=self.deviceId_to_chassisId)
        nx.draw_networkx_edges(self.G, self.pos)
        plt.show(block=block)

if __name__ == "__main__":
    # Initialize Topo Manger and get the latest version of the topology
    if (len(sys.argv) != 2):
        print("Usage : python topo_discovery.py k")
    else: 
        k = int(int(sys.argv[1]))
        if k==4:
            from deviceList.deviceList_k4 import *
        if k==8:
            from deviceList.deviceList_k8 import *

        topoManager = TopoManager(k, CORE_DEVICES, AGREGATION_DEVICES, EDGE_DEVICES)
        
        print(topoManager.degree)
        # Print some usefull information
        print("\n Host location mapping\n")
        print(json.dumps(topoManager.hostLocation, indent=4, sort_keys=True))
        print("\n Link port mapping\n")
        print("length = " + str(len(topoManager.linkPorts)))
        print(json.dumps(topoManager.linkPorts, indent=4, sort_keys=True))

        # Draw the topology
        topoManager.draw_topo()