#
# Title:        SDCon
# Description:  Integrated Control Platform for Software-Defined Clouds
# Licence:      GPL - http://www.gnu.org/copyleft/gpl.html
#
# Copyright (c) 2018, The University of Melbourne, Australia
#
import os
import sys,subprocess
import networkx
import network_manager, topo_discovery, sdcon_config
from monitoringTools import *
from sdcon_config import SDCNodeIdType

# < Default path principles >
#  * For known host: forward to relavant port.
#  * For unknown host, broadcast, and all other pacekts: use the default rule set by controller!

# < Table entires >
#  * Table 0
#    - Match all known host mac -> goto Table 1 (priority: between 4-100)
#    - For unknown hosts, automatically use the default rule with lower priority
#  * Table 1: additional processing before forwarding.
#    - Match ARP packet -> Send to Controller and Goto Table 2 (high priority)
#    - Otherwise -> Just goto Table 2 (lower priority)
#  * Table 2: deciding path for 'known' hosts.
#    - Down-ward : match dl_dst -> action = outport
#    - Up-ward   : match dl_dst && in_port -> action = outport (For load distribution)


# Table IDs: when self-learn mode is enabled, other rules must be placed in the next table;
#   so that the incoming packets can be processed after self-learn action
#   by forwarding to the next table.
TABLE_ID_PREPROCESS = 1 # for ARP rule. e.g. arp ... actions=outport(CONTROLLER),goto_table=2
TABLE_ID_HOST = 0 # for specific host rules. e.g. dl_dst=AB:CD:EF:... actions=outport(9)
TABLE_ID_BASE = 0 # for basic rules. e.g. in_port=8 actions=outport(9)

# Self-learn: switches automatically push new forwarding rule for all incoming 
#   traffics. The source address of the incoming packet will be the destination
#   of the new rule. It will be installed on top of the other rules. 


def get_up_down_ports(topo, switch_id):
    type = SDCNodeIdType.get_type(switch_id)
    upports=set()
    downports=set()
    for port in topo.get_all_ports(switch_id):
        other_id = topo.get_connected_node_via_port(switch_id, port)
        
        print "Debug: (%s,type=%s) port=%s, other=%s"%(switch_id,str(type),str(port),str(other_id))
        
        if other_id == None or SDCNodeIdType.get_type(other_id) < type:
            downports.add(port)
        elif SDCNodeIdType.get_type(other_id) > type:
            upports.add(port)
    return (sorted(list(upports)), sorted(list(downports)))

def get_up_down_connected(topo, switch_id):
    type = SDCNodeIdType.get_type(switch_id)
    up_connected = set()
    down_connected = set()
    for other_id in topo.get_all_connected(switch_id):
        if SDCNodeIdType.get_type(other_id) > type:
            up_connected.add(other_id)
        elif SDCNodeIdType.get_type(other_id) < type:
            down_connected.add(other_id)
    return (list(up_connected), list(down_connected))

def get_default_path_port_pair(all_inports, all_outports):
    in_out = {}
    all_inports.sort()
    all_outports.sort()
    if len(all_outports) == 0 or len(all_outports) == 0:
        return in_out
        
    for i in range(len(all_inports)):
        inport = all_inports[i%len(all_inports)]
        outport = all_outports[i%len(all_outports)] 
        in_out[inport] = outport
    return in_out

def get_sub_hosts(topo, switch_id):
    # Find all connected hosts under this switch (downstream only)
    up_nodes, down_nodes = get_up_down_connected(topo, switch_id)
    connected_hosts = set()
    for down_n in down_nodes:
        if SDCNodeIdType.is_host(down_n):
            connected_hosts.add(down_n)
        else:
            sub_hosts = get_sub_hosts(topo, down_n)
            connected_hosts.update(sub_hosts)
    return list(connected_hosts)

def get_super_hosts(topo, switch_id):
    # Find all connected hosts of my upper switches (for up-stream.) Not including my sub-host
    up_nodes, down_nodes = get_up_down_connected(topo, switch_id)
    connected_hosts = set()
    my_sub = get_sub_hosts(topo, switch_id)
    for upnode in up_nodes:
        if SDCNodeIdType.is_host(upnode):
            connected_hosts.add(upnode)
        else:
            # Result = {All sub nodes of upper layer} - {my sub}
            up_sub = get_sub_hosts(topo, upnode)
            connected_hosts.update(up_sub)
            connected_hosts.difference_update( my_sub )
            
            super_hosts = get_super_hosts(topo, upnode)
            connected_hosts.update(super_hosts)
    
    return list(connected_hosts)

def get_reachable_host_via_port(topo, switch_id, port):
    # Find all rechable hosts from this switch via the port.
    connected_hosts = set()
    
    other_id = topo.get_connected_node_via_port(switch_id, port)
    
    connected_hosts.update(get_sub_hosts(topo, other_id)) # lower layer hosts of the other_id
    connected_hosts.update(get_super_hosts(topo, other_id)) # connectable hosts of the other_id
    connected_hosts.difference_update(get_sub_hosts(topo, switch_id)) # Remove my sub-hosts
    
    return connected_hosts

# A wrapper function of add_flow_path(). It creates two flows.
def add_flow_path(switch, action_outport, priority, action_table=None,\
    match_inport=None, match_src_mac=None, match_dst_mac=None, match_is_arp=False,\
    table_id=0):
    # Create the intended flow and forward to ARP table.
    if match_dst_mac:
        action_table = TABLE_ID_PREPROCESS
    
    network_manager.add_flow(switch, action_outport, priority, action_table=action_table, \
        match_inport=match_inport, match_src_mac=match_src_mac,\
        match_dst_mac=match_dst_mac, match_is_arp=match_is_arp,\
        table_id=table_id, flowname=network_manager.FLOWNAME_DEFAULT)
    '''
    if match_dst_mac and int(table_id) != 0:
        network_manager.add_flow(switch, [], priority, action_table=1, \
            match_inport=match_inport, match_src_mac=match_src_mac,\
            match_dst_mac=match_dst_mac, match_is_arp=match_is_arp,\
            table_id=0, flowname=network_manager.FLOWNAME_DEFAULT)    
        add_rule_goto_table(switch, priority, from_table=0, to_table=1)
    '''

def add_rule_arp(switch):
    # Force forward to controller as well, for ARP processing and host discovery.
    outport = "CONTROLLER"
    network_manager.add_flow(switch, outport, network_manager.ODL_FLOW_PRIORITY_DEFAULT_PATH_ARP, \
        match_is_arp=True, 
        action_table = TABLE_ID_BASE, flowname=network_manager.FLOWNAME_DEFAULT,\
        table_id = TABLE_ID_PREPROCESS)

def add_rule_goto_table(switch_id, priority, from_table, to_table):
    if from_table == to_table:
        return
    network_manager.add_flow(switch_id, [], priority, action_table = to_table, table_id = from_table,
        flowname=network_manager.FLOWNAME_DEFAULT)


#####################################################
# Path for downward: match - dl_dst, action - downport
#####################################################
# Add host rules for directly connected hosts
def add_path_down_direct_hosts(topo, switch_id):
    for node_id in topo.get_all_connected(switch_id):
        if SDCNodeIdType.is_host(node_id):
            outport = topo.get_switch_port_to_dst(switch_id, node_id)
            add_flow_path(switch_id, outport, network_manager.ODL_FLOW_PRIORITY_DEFAULT_PATH_FOR_HOST,\
                match_dst_mac=node_id, \
                table_id = TABLE_ID_HOST)

# Add host rules for indirectly connected hosts
def add_path_down_indirect_hosts(topo, switch_id):
    up_nodes, down_nodes = get_up_down_connected(topo, switch_id)
    for down_switch in down_nodes:
        if SDCNodeIdType.is_host(down_switch):
            continue # rule applies only to switches
        outport = topo.get_switch_port_to_dst(switch_id, down_switch)
        hosts = get_sub_hosts(topo, down_switch)
        for dst_mac in hosts:
            add_flow_path(switch_id, outport, network_manager.ODL_FLOW_PRIORITY_DEFAULT_PATH_FOR_HOST,\
                match_dst_mac=dst_mac, \
                table_id = TABLE_ID_HOST)

#####################################################
# Path for upward: match - dl_dst and in_port=downport, action - upport
#####################################################
def add_path_up_port_match_known_hosts(topo, switch_id):
    upports, downports = get_up_down_ports(topo, switch_id)
    if upports == None or len(upports) == 0 or downports == None or len(downports) == 0:
        return
    
    dsts = {}
    # Get all reachable destinations of each up-port
    for upport in upports:
        dsts[upport] = get_reachable_host_via_port(topo, switch_id, upport)
    
    # Find all hosts, in order to find the host that can reach only through a specific port.
    dsts_all = set()
    dst_port = {}
    for port in dsts:
        dsts_all.update(dsts[port])
        for dst in dsts[port]:
            dst_port[dst] = port
    
    # in = downport, out = upports
    in_out = get_default_path_port_pair(all_inports= downports, all_outports = upports)
    for inport in in_out: 
        outport = in_out[inport]
        if outport:
            # Find all connected super-hosts of the outport.
            up_known_hosts = dsts[outport]
            for dst in up_known_hosts:
                add_flow_path(switch_id, outport, network_manager.ODL_FLOW_PRIORITY_DEFAULT_PATH,\
                    match_inport=inport, match_dst_mac=dst,\
                    table_id = TABLE_ID_BASE)
                #print "Debug: (%s) dl_dst=%s in_port=%s >> outport:%s"%(switch_id, str(dst), str(inport), str(outport))
        other_hosts = set(dsts_all)
        if outport:
            other_hosts.difference_update(dsts[outport])
        print "Debug: (%s) port %s other hosts = %s"%(switch_id, str(port), str(other_hosts))
        if len(other_hosts) != 0:
            for dst in other_hosts:
                outport = dst_port[dst]
                add_flow_path(switch_id, outport, network_manager.ODL_FLOW_PRIORITY_DEFAULT_PATH,\
                    match_inport=inport, match_dst_mac=dst,\
                    table_id = TABLE_ID_BASE)
                #print "Debug: Extra (%s) dl_dst=%s in_port=%s >> outport:%s"%(switch_id, str(dst), str(inport), str(outport))            

# Add port-base rules from down-port to up-port
def add_path_up_port_match(topo, switch_id):
    upports, downports = get_up_down_ports(topo, switch_id)
    if downports == None or len(downports) == 0:
        return
    
    # in = downport, out = upports
    in_out = get_default_path_port_pair(all_inports= downports, all_outports = upports)
    for inport in in_out: 
        add_flow_path(switch_id, in_out[inport], network_manager.ODL_FLOW_PRIORITY_DEFAULT_PATH,\
            match_inport=inport,  \
            table_id = TABLE_ID_BASE)

#####################################################
# Main function
#####################################################
def set_default_path_switch(topo, switch_id):
    add_path_down_direct_hosts(topo, switch_id) # To specific destination (to down ports)
    add_path_down_indirect_hosts(topo, switch_id)
    add_path_up_port_match_known_hosts(topo, switch_id)
    
    #add_path_up_port_match(topo, switch_id) # For the rest going from down to up level
    #add_path_broadcast_common(topo, switch_id) # To broadcast (everywhere)
    #add_path_flood(topo, switch_id) # Unknown packets from upper to lower : Flood
    #add_rule_self_learn(topo, switch_id) # Self-learn function
    add_rule_arp(switch_id)
    
    if TABLE_ID_PREPROCESS < TABLE_ID_HOST:
        add_rule_goto_table(switch_id, network_manager.ODL_FLOW_PRIORITY_DEFAULT_PATH, \
            from_table=TABLE_ID_PREPROCESS, to_table=TABLE_ID_HOST)

def set_default_paths(topo=None):
    if topo == None:
        topo = topo_discovery.SDCTopo(CONTROLLER_URL, CONTROLLER_ID, CONTROLLER_PW)
    for switch_id in topo.get_all_switches():
        set_default_path_switch(topo, switch_id)
    # add_path_extra_for_controller(topo)

def del_all_default_paths(topo):
    del_all_rule_self_learn(topo)
    tables = set([TABLE_ID_PREPROCESS, TABLE_ID_HOST, TABLE_ID_BASE])
    for table in tables:
        network_manager.del_all_flows_match_name(topo, network_manager.FLOWNAME_DEFAULT, table_id = table)

def test_new_function(topo):
    return

# Main
def _print_usage():
    print("Usage:\t python %s set \t- add default paths for CLOUDS-Pi"%(sys.argv[0]))
    print("      \t python %s del \t- delete all default paths that have been set up with this program"%(sys.argv[0]))

def main():
    if len(sys.argv) < 2:
        _print_usage()
        return
    topo = topo_discovery.SDCTopo(CONTROLLER_URL, CONTROLLER_ID, CONTROLLER_PW)
    if sys.argv[1] == "set":
        set_default_paths(topo)
    elif sys.argv[1] == "del":
        del_all_default_paths(topo)
    elif sys.argv[1] == "test":
        test_new_function(topo)
    else:
        _print_usage()
        return

if __name__ == "__main__":
    main()