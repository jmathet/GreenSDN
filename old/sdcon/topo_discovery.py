#
# Title:        SDCon
# Description:  Integrated Control Platform for Software-Defined Clouds
# Licence:      GPL - http://www.gnu.org/copyleft/gpl.html
#
# Copyright (c) 2018, The University of Melbourne, Australia
#
import networkx
import requests
import json
from requests.auth import HTTPBasicAuth
from collections import defaultdict
from monitoringTools import *
import network_defpath
from sdcon_config import SDCNodeIdType
import matplotlib.pyplot as plt

#For debugging: <ODL_CONTROLLER_URL>/restconf/operational/network-topology:network-topology/topology/flow:1/

class SDCNode:
    def __init__(self, id):
        self.id=id
        self.map_node_port={}    # map_node_port[dst] = port
        self.map_port_node={}    # map_port_node[port] = dst_id
    
    def is_host(self):
        return SDCNodeIdType.is_host(self.id)
    
    def add_port(self, port, other_id):
        if self.is_host():
            port = other_id
        if other_id != None:
            self.map_node_port[other_id] = port
        self.map_port_node[port] = other_id
    
    def get_port(self, other_id):
        return self.map_node_port[other_id]
    
    def is_connected(self, other_id):
        is_conn = other_id in self.map_node_port
        return is_conn
    
    def get_all_connected(self):
        return self.map_node_port.keys()
    
    def get_all_ports(self):
        return self.map_port_node.keys()
    
    def get_other_node(self, port_num):
        if self.is_host() and int(port_num) < 5:
            print "Host node..", port_num, self.map_node_port.keys()[0]
            return self.map_node_port.keys()[0]
        if port_num not in self.map_port_node:
            print "No port in this node..", port_num, self.id
            return None
        return self.map_port_node[port_num]

class SDCTopo:
    def __init__(self, base_url, id, pw):
        self.host_mac_to_ip={}                  # dict[mac] = ip
        self.host_ip_to_mac={}
        self.nodes = {}        # dict[id] = SDCNodeLink
        self.base_url = base_url
        self.id, self.pw = id, pw
        self.build_topo()
        self.default_port_match = None
        
    
    def tp_is_switch(self, tp):
        tp_split = tp.split(":", 1)
        if tp_split[0] == "openflow":
            return True
    
    def tp_to_id(self, tp):
        if self.tp_is_switch(tp):
            return tp.split(":")[1]     # tp is "openflow:404000000:5"
        else:
            return tp.split(":", 1)[1]  # tp is "host:ab:cd:ef:00:11:22"
    
    def tp_to_port(self, tp):
        if self.tp_is_switch(tp):
            return tp.split(":")[2]
        return None
    
    def build_topo(self):
        # Build topology from the ONOS info.
        self.topo_graph = networkx.Graph()

        # Get the list of hosts
        data = getJsonData(CONTROLLER_URL + "/hosts")
        for node in data["hosts"]:
            self.parse_node_addr(node)
            
        # Get switch nodes (and ports.)
        data = getJsonData(CONTROLLER_URL + "/devices")
        for node in data["devices"]: 
            nodeDetails = getJsonData(CONTROLLER_URL + "/devices/" + node["id"] + "/ports")
            self.parse_switch_ports(nodeDetails)
            
        # Get link mapping between switches
        data = getJsonData(CONTROLLER_URL + "/links")
        for link in data["links"]:
            self.parse_link(link)
    
    def parse_node_addr(self, host):
        # Get host MAC and IP addresses
        print((host))
        host_ip = host["ipAddresses"][0]
        host_mac = host["mac"]
        #self.host_mac_to_ip[host_mac] = host_ip
        #self.host_ip_to_mac[host_ip] = host_mac
        # TODO: erreur
    
    def parse_switch_ports(self, node):
        for port in node["ports"]:
            if port["port"] == "LOCAL":
                continue
            
            if port["element"] in self.nodes:
                node = self.nodes[port["element"]]
            else:
                node = SDCNode(port["element"])
                self.nodes[port["element"]]=node
                
            node.add_port(port["port"], None)
    
    # def __get_port_data(self, dpid, port):
    #     # /restconf/operational/opendaylight-inventory:nodes/node/openflow:40960010/node-connector/openflow:40960010:4
    #     url = self.base_url +\
    #         "/restconf/operational/opendaylight-inventory:nodes/node/openflow:" +\
    #         str(dpid) + "/node-connector/openflow:"+ str(dpid)+":"+str(port)
    #     response = requests.get(url, auth=HTTPBasicAuth(self.id, self.pw))
    #     if(response.ok):
    #         data = json.loads(response.content)
    #     else:
    #         response.raise_for_status()
    #     return data["node-connector"][0]
    
    # def is_port_down(self, dpid, port):
    #     data = self.__get_port_data(dpid, port)
    #     return data["flow-node-inventory:state"]["link-down"] #Link is down
    
    # def get_port_interface_name(self, dpid, port):
    #     data = self.__get_port_data(dpid, port)
    #     return data["flow-node-inventory:name"]
    
    def parse_link(self, link):
        # <link-id>openflow:40960021:2</link-id>
        # <source-tp>openflow:40960021:2</source-tp>
        # <dest-tp>openflow:40960010:1</dest-tp>
        src_tp = link["src"]["device"].encode('ascii')
        dst_tp = link["dst"]["device"].encode('ascii')
        
        src_id = self.tp_to_id(src_tp)
        dst_id = self.tp_to_id(dst_tp)
        src_port = self.tp_to_port(src_tp)
        dst_port = self.tp_to_port(dst_tp)
        
        if src_id in self.nodes:
            src_node = self.nodes[src_id]
        else:
            src_node = SDCNode(src_id)
            self.nodes[src_id]=src_node
            
        if dst_id in self.nodes:
            dst_node = self.nodes[dst_id]
        else:
            dst_node = SDCNode(dst_id)
            self.nodes[dst_id]=dst_node       
            
        src_node.add_port(src_port, dst_id)
        dst_node.add_port(dst_port, src_id)
        
        #if self.tp_is_switch(src_tp) and self.tp_is_switch(dst_tp):
        self.topo_graph.add_edge(src_id, dst_id)    
    
    def get_connected_switch(self, host_ip):
        host_mac = self.host_ip_to_mac[host_ip]
        node = self.nodes[host_mac]
        return node.get_all_connected()[0]
        
    def get_all_hosts_ip(self):
        return self.host_mac_to_ip.values()
    
    def get_all_nodes(self):
        return self.nodes.keys()
    
    def get_all_switches(self):
        all_nodes = self.nodes.keys()
        all_switches = []
        for node_id in all_nodes:
            if SDCNodeIdType.is_switch(node_id):
                all_switches.append(node_id)
        return all_switches
    
    def get_all_switches_with_port(self):
        all_switches = []
        for sw in self.get_all_switches():
            all_switches.append( (sw, self.get_all_ports(sw)) )
        
        return all_switches
    
    def get_all_ports(self, id):
        node=self.nodes[id]
        return node.get_all_ports()
    
    def get_all_connected(self, id):
        node=self.nodes[id]
        return node.get_all_connected()
    
    def get_switch_port_to_dst(self, src_id, dst_id):
        src_node = self.nodes[src_id]
        return src_node.get_port(dst_id)
    
    def get_connected_node_via_port(self, switch_id, port_num):
        # Get the other node id connected through the port.
        if switch_id not in self.nodes:
            return None
        switch_node = self.nodes[switch_id]
        return switch_node.get_other_node(port_num)
    
    def get_connected_node_port(self, switch_id, port_num):
        # Get the other node id and port which connects to this switch
        other_id = self.get_connected_node_via_port(switch_id, port_num)
        if other_id == None:
            return (None, None)
        other_port = self.get_switch_port_to_dst(other_id, switch_id)
        return (other_id, other_port)
    
    def get_host_mac(self, host_ip):
        if host_ip not in self.host_ip_to_mac:
            return None
        return self.host_ip_to_mac[host_ip]
    
    def get_host_ip(self, host_mac):
        if host_mac in self.host_mac_to_ip:
            return self.host_mac_to_ip[host_mac]
        return host_mac
    
    def print_all_hosts(self):
        print "host to switches: [host_ip] -- [port:switch]:"
        for host_ip in self.get_all_hosts_ip():
            switch = self.get_connected_switch(host_ip)
            host_mac = self.host_ip_to_mac[host_ip]
            switch_port = self.get_switch_port_to_dst(switch, host_mac)
            print "%s -- (%s) %s"%(host_ip, switch_port, switch)
    
    def print_all_links(self):
        print "all links... [node:port] -- [other node]"
        for node in self.nodes.values():
            for dst in node.get_all_connected():
                print "%s:%s -- %s"%(node.id, node.get_port(dst), dst)
    
    def build_default_path_port_match(self):
        self.default_port_match = defaultdict(dict)
        for switch in self.get_all_nodes():
            if SDCNodeIdType.get_type(switch) == SDCNodeIdType.Aggr or SDCNodeIdType.get_type(switch) == SDCNodeIdType.Edge:
                upports, downports = network_defpath.get_up_down_ports(self, switch)
                for i in range(max(len(upports), len(downports))):
                    inport = downports[i%len(downports)]
                    outport = upports[i%len(upports)]
                    self.default_port_match[switch][inport]=outport
    
    def get_default_outport(self, switch, inport):
        if self.default_port_match == None:
            self.build_default_path_port_match()
        if inport in self.default_port_match[switch]:
            return self.default_port_match[switch][inport]
        return None
    
    def find_all_path(self, src_ip, dst_ip):
        src_mac = self.get_host_mac(src_ip)
        dst_mac = self.get_host_mac(dst_ip)
        
        paths= networkx.all_shortest_paths(self.topo_graph, source=src_mac, target=dst_mac)
        return list(paths)
    
    def find_all_path_port_map(self, src_ip, dst_ip):
        port_map=[]
        for path in self.find_all_path(src_ip, dst_ip):
            port_map.append( self.get_switch_port_map(path) )
        return port_map
    
    def get_switch_port_map(self, path):
        switch_port_map = []    # [ (inport, switch, outport), ...]
        for i in range(1, len(path)-1):
            prev_node = path[i-1]
            this_node = path[i]
            next_node = path[i+1]
            inport = self.get_switch_port_to_dst(this_node, prev_node)
            outport = self.get_switch_port_to_dst(this_node, next_node)
            switch_port_map.append( (inport, this_node, outport) )
        return switch_port_map

def test():
    print "\nTesting SDCTopo..."
    topo = SDCTopo(CONTROLLER_URL, CONTROLLER_ID, CONTROLLER_PW)
    print "\nAll hosts..."
    topo.print_all_hosts()
    print "\nAll links..."
    topo.print_all_links()
    
    

# Main
def main():
    test()

    #networkx.draw(topo)
    #plt.show()



if __name__ == '__main__':
    main()