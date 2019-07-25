#
# Title:        SDCon
# Description:  Integrated Control Platform for Software-Defined Clouds
# Licence:      GPL - http://www.gnu.org/copyleft/gpl.html
#
# Copyright (c) 2018, The University of Melbourne, Australia
#
#!/usr/bin/env python
#
# This program manages network part for network-cloud integration. (OpenDaylight part, for ODL+OpenStack)
#
# Base source code for topology discovery and flow table injection has been derived and modified from:
#      https://github.com/nayanseth/sdn-loadbalancing
#
# For function parameters,
#     Host: always IP address (e.g. 192.168.0.4)
#     Switch: always DPID (e.g. 40960020)
# Do not use switch's IP address for any function call.

import requests
from requests.auth import HTTPBasicAuth
import json
import sys
import networkx
import topo_discovery, network_defpath
from  monitoringTools import *

ODL_FLOW_PRIORITY_DEFAULT_PATH = 5
ODL_FLOW_PRIORITY_DEFAULT_PATH_ARP      = ODL_FLOW_PRIORITY_DEFAULT_PATH+3
ODL_FLOW_PRIORITY_DEFAULT_PATH_LEARN    = ODL_FLOW_PRIORITY_DEFAULT_PATH+2
ODL_FLOW_PRIORITY_DEFAULT_PATH_BROADCAST= ODL_FLOW_PRIORITY_DEFAULT_PATH+1
ODL_FLOW_PRIORITY_DEFAULT_PATH_FOR_HOST = ODL_FLOW_PRIORITY_DEFAULT_PATH+3

ODL_FLOW_PRIORITY_SPECIAL_PATH          = ODL_FLOW_PRIORITY_DEFAULT_PATH+10
ODL_FLOW_PRIORITY_SPECIAL_PATH_QUEUE    = ODL_FLOW_PRIORITY_DEFAULT_PATH+11

FLOWNAME_DEFAULT        = "sdc-default-path"
FLOWNAME_SPECIAL        = "sdc-special-path"
FLOWNAME_SPECIAL_QUEUE  = "sdc-queue-path"

## Raw REST API call to ODL
def generate_xml_flow_rule(flow_id, action_outport, priority, action_queue=None, action_table=None,
    match_inport=None, match_src_ip=None, match_dst_ip=None, 
    match_src_mac=None, match_dst_mac=None, match_is_arp=False,
    table_id=0, flowname='Default'):
    xml = '''<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"no\"?>
        <flow xmlns=\"urn:opendaylight:flow:inventory\">
            <priority>'''+str(priority)+'''</priority>
            <flow-name>'''+str(flowname)+'''</flow-name>
            <match>'''
    if match_src_ip or match_dst_ip or match_src_mac or match_dst_mac or match_is_arp:
        xml +='<ethernet-match>'
    if match_src_ip or match_dst_ip:
        xml +='<ethernet-type><type>2048</type></ethernet-type>'
    elif match_is_arp:
        xml +='<ethernet-type><type>2054</type></ethernet-type>'
    if match_src_mac:
        xml +='<ethernet-source><address>'+ str(match_src_mac)+'</address></ethernet-source>'
    if match_dst_mac:
        xml +='<ethernet-destination><address>'+ str(match_dst_mac)+'</address></ethernet-destination>'        
    if match_src_ip or match_dst_ip or match_src_mac or match_dst_mac or match_is_arp:
        xml +='</ethernet-match>'
            
    if match_inport:
        xml +='<in-port>'+ str(match_inport)+'</in-port>'
    if match_src_ip:
        xml +='<ipv4-source>' + str(match_src_ip)+'/32</ipv4-source>'
    if match_dst_ip:
        xml +='<ipv4-destination>' + str(match_dst_ip)+'/32</ipv4-destination>'
    action_order = 0
    xml += '''
            </match>
            <id>'''+str(flow_id)+'''</id>
            <table_id>'''+str(table_id)+'''</table_id>
            <instructions>'''
    if action_queue or action_outport:
        xml +='''<instruction><order>0</order>
                <apply-actions>'''
    if action_queue:
        xml += '''
                    <action><order>'''+str(action_order)+'''</order>
                        <set-queue-action>
                        <queue-id>''' + str(action_queue) +'''</queue-id>
                        </set-queue-action>
                    </action>'''
        action_order += 1
    if action_outport:
        if type(action_outport) != list:
            action_outport = [action_outport]
        for outport in action_outport:
            xml += '''
                    <action><order>'''+str(action_order)+'''</order>
                        <output-action>
                        <output-node-connector>''' + str(outport) +'''</output-node-connector>
                        <max-length>65535</max-length>
                        </output-action>
                    </action>'''
            action_order += 1
    
    if action_queue or action_outport:
        xml +='''</apply-actions>
                </instruction>'''

    if action_table:
        xml += '''
                <instruction>
                    <order>1</order>
                    <go-to-table>
                        <table_id>'''+str(action_table)+'''</table_id>
                    </go-to-table>
                </instruction>'''        
    xml +='''</instructions>
        </flow>'''
        #print(xmlSrcToDst)
    return xml


def push_flow_raw(base_url, openflow_node, jsonFlow):
    url = base_url + '/restconf/config/opendaylight-inventory:nodes/node/openflow:' \
        + openflow_node+'/table/' + table_id + '/flow/' + flow_id
    response = postJsonData(url, jsonFlow)
    if response.status_code != 200 and response.status_code != 201:
        print (url)
        print (xml)
        print (response.json())
        response.raise_for_status()

def get_flows_raw(nodeID):
    # Debug: ODL_CONTROLLER_URL/restconf/config/opendaylight-inventory:nodes/node/openflow:40960000/table/0
    url = CONTROLLER_URL + "/flows/" + str(nodeID)
    response = getJsonData(url)
    if response.status_code != 200:
        print (response.json())
        print ("Cannot push a flow...",openflow_node, table_id0)
        #response.raise_for_status()
    return response.json()


def del_flow_raw(baseUrl, id, pw, openflow_node, table_id, flow_id):
    print ("Deleting flow %s from %s."%(flow_id, openflow_node))
    
    url = baseUrl + '/restconf/config/opendaylight-inventory:nodes/node/openflow:' + openflow_node+'/table/' + str(table_id) + '/flow/' + str(flow_id)
    response = requests.delete(url, auth=HTTPBasicAuth(id, pw),  headers={"Accept": "application/json"})
    if response.status_code != 200:
        print (response.json())
        response.raise_for_status()

def get_all_nodes_raw(baseUrl, id, pw,):
    # Debug:  "ODL_CONTROLLER_URL/restconf/operational/opendaylight-inventory:nodes/
    url = baseUrl + '/restconf/operational/opendaylight-inventory:nodes/'
    response = requests.get(url, auth=HTTPBasicAuth(id, pw), \
        headers={"Accept": "application/json"})
    if response.status_code != 200:
        print (response.json())
        print ("Cannot push a flow...",openflow_node, table_id)
        #response.raise_for_status()
    return response.json()

def get_all_switch_info():
    # included info. : ip address of the switch = ret[n]["flow-node-inventory:ip-address"]
    #                  node-connectors (ports)  = ret[n]["node-connector"][i]...
    #                  flow tables              = ret[n]["flow-node-inventory:table"]...
    jdata = get_all_nodes_raw(CONTROLLER_URL, CONTROLLER_ID, CONTROLLER_PW)
    return jdata["nodes"]["node"]

def add_flow(switch, action_outport, priority, action_queue=None, action_table=None,\
    match_inport=None, match_src_ip=None, match_dst_ip=None, \
    match_src_mac=None, match_dst_mac=None, match_is_arp=False,\
    table_id=0, flowname='Default'):
    
    # flow id generation delete
    
    print "Adding flow to %s prio %d match(inport:%s, src_ip:%s, dst_ip:%s, src_mac:%s, dst_mac:%s) -> action=outport(%s,%s,%s)" \
        % (switch, priority, match_inport, match_src_ip, match_dst_ip, match_src_mac, match_dst_mac, str(action_outport),action_queue, str(action_table)) 
    xml = generate_xml_flow_rule(flow_id, action_outport, priority, 
        action_queue=action_queue, action_table=action_table, match_inport=match_inport,
        match_src_ip=match_src_ip, match_dst_ip=match_dst_ip, 
        match_src_mac=match_src_mac, match_dst_mac=match_dst_mac,
        match_is_arp=match_is_arp, table_id=table_id, flowname=flowname)
    push_flow_raw(sdcon_config.ODL_CONTROLLER_URL, sdcon_config.ODL_CONTROLLER_ID, sdcon_config.ODL_CONTROLLER_PW, 
        switch, str(table_id), str(flow_id), xml)


def get_flows(sw, table_id):
    data = get_flows_raw(sdcon_config.ODL_CONTROLLER_URL, sdcon_config.ODL_CONTROLLER_ID, sdcon_config.ODL_CONTROLLER_PW, sw, table_id)
    flows = []
    if 'flow-node-inventory:table' in data:
        for obj in data['flow-node-inventory:table']:
            if "flow" in obj:
                flows = obj['flow']
                break
    return flows

def del_all_flows_match_name(topo, flowname, table_id="0"):
    all_switches = topo.get_all_switches()
    for sw in all_switches:
        flows = get_flows(sw, table_id)
        for fl in flows:
            if flowname == fl['flow-name']:
                del_flow_raw(sdcon_config.ODL_CONTROLLER_URL, sdcon_config.ODL_CONTROLLER_ID, sdcon_config.ODL_CONTROLLER_PW, sw, table_id, fl['id'])

def del_all_flows_match_src_dst_ip(topo, src_ip, dst_ip, table_id="0"):
    all_switches = topo.get_all_switches()
    for sw in all_switches:
        flows = get_flows(sw, table_id)
        for fl in flows:
            try:
                if src_ip in fl['match']['ipv4-source'] and dst_ip in fl['match']['ipv4-destination']:
                    del_flow_raw(sdcon_config.ODL_CONTROLLER_URL, sdcon_config.ODL_CONTROLLER_ID, sdcon_config.ODL_CONTROLLER_PW, sw, table_id, fl['id'])
            except KeyError:
                continue

def del_all_flows_match_priority(topo, table_id, priority):
    all_switches = topo.get_all_switches()
    for sw in all_switches:
        flows = get_flows(sw, table_id)
        for fl in flows:
            if priority == fl['priority']:
                del_flow_raw(sdcon_config.ODL_CONTROLLER_URL, sdcon_config.ODL_CONTROLLER_ID, sdcon_config.ODL_CONTROLLER_PW, sw, table_id, fl['id'])

## Path management

def get_low_utilization_path(topo, src_host, dst_host):
    # Find the lowest utilization.
    all_paths = topo.find_all_path(src_host, dst_host)
    
    # For debugging
    print("\nDebug: all Paths for %s --> %s"%(src_host, dst_host))
    for path in all_paths:
        print(path)    # Each path is a list of switch IDs, e.g., [40960023, 40960012, 40960000, 40960010, 40960021]
    
    # Select a path
    path_bw=[]
    for path in all_paths:
        bw = network_monitor.get_bw_usage_along_links(topo, path, exclude_src_ip=src_host, exclude_dst_ip=dst_host)
        path_bw.append(bw)
    
    low_path = path_bw.index(min(path_bw))
    selected_path = all_paths[low_path]
    print("Debug: selected path for %s --> %s = %s"%(src_host, dst_host, selected_path))
    return selected_path

def get_default_path(topo, src_ip, dst_ip):
    all_paths = list(topo.find_all_path(src_ip, dst_ip))
    if len(all_paths) == 1:  # only one path
        return all_paths[0]
    
    # Multiple paths
    all_port_map =[]
    for path in all_paths:
        all_port_map.append(topo.get_switch_port_map(path))
    
    for probe in range(len(all_port_map[0])):
        path_i = 0
        while path_i < len(all_port_map):
            inport, switch, outport = all_port_map[path_i][probe]
            def_outport = topo.get_default_outport(switch, inport)
            if def_outport and def_outport != outport:
                del all_port_map[path_i]
                del all_paths[path_i]
            path_i += 1
        if len(all_paths) == 1:
            return all_paths[0]
    print "get_default_path: cannot find a default path!", src_ip, dst_ip
    return None

def add_path_along_links(topo, path, src_host, dst_host):
    for (inport, this_node, outport) in topo.get_switch_port_map(path):
        add_flow(this_node, outport, ODL_FLOW_PRIORITY_SPECIAL_PATH, match_src_ip= src_host, match_dst_ip=dst_host, flowname = FLOWNAME_SPECIAL)

def add_path_along_low_utilization(topo, src_host, dst_host, src_vm_ip=None, dst_vm_ip=None):
    if src_vm_ip == None:
        src_vm_ip = src_host
    if dst_vm_ip == None:
        dst_vm_ip = dst_host        
    selected_path = get_low_utilization_path(topo, src_host, dst_host)
    add_path_along_links(topo, selected_path, src_vm_ip, dst_vm_ip)

def create_special_path(src_ip, dst_ip, src_vm_ip=None, dst_vm_ip=None):
    # To set a rule for vm traffic, give the compute nodes IP at src_ip/dst_ip,
    #  and provide VM IPs as src_vm_ip/dst_vm_ip.
    # If xxx_vm_ip is set, we use them as a flow matching rule.
    topo = topo_discovery.SDCTopo(sdcon_config.ODL_CONTROLLER_URL, sdcon_config.ODL_CONTROLLER_ID, sdcon_config.ODL_CONTROLLER_PW)
    add_path_along_low_utilization(topo, src_ip,dst_ip, src_vm_ip, dst_vm_ip)
    
def delete_special_path(src_ip, dst_ip):
    topo = topo_discovery.SDCTopo(sdcon_config.ODL_CONTROLLER_URL, sdcon_config.ODL_CONTROLLER_ID, sdcon_config.ODL_CONTROLLER_PW)
    del_all_flows_match_src_dst_ip(topo, src_ip, dst_ip)

def clear_all_paths():
    topo = topo_discovery.SDCTopo(sdcon_config.ODL_CONTROLLER_URL, sdcon_config.ODL_CONTROLLER_ID, sdcon_config.ODL_CONTROLLER_PW)
    del_all_flows_match_name(topo, FLOWNAME_SPECIAL, table_id = 0)
    del_all_flows_match_name(topo, FLOWNAME_SPECIAL_QUEUE, table_id = 0)
    network_defpath.del_all_default_paths(topo)
    
def path_string_format(path):
    return " -> ".join( [str(p) for p in path] )

def print_all_paths(src_ip, dst_ip):
    topo = topo_discovery.SDCTopo(sdcon_config.ODL_CONTROLLER_URL, sdcon_config.ODL_CONTROLLER_ID, sdcon_config.ODL_CONTROLLER_PW)
    
    print "\nCurrently utilizing path for %s -> %s" %(src_ip, dst_ip)
    print path_string_format(network_monitor.monitor_get_current_path(topo, src_ip, dst_ip))
    
    print "\nPort-switch mappings of the path:"
    print path_string_format(network_monitor.monitor_get_current_path_port_map(topo, src_ip,dst_ip))
    
    all_path = topo.find_all_path_port_map(src_ip, dst_ip)
    print "\nAll paths %s -> %s: (in_port, switch, out_port)" %(src_ip, dst_ip)
    for path in all_path:
        print path_string_format(path)

def test_set_path():
    print "\nTesting..."
    
    topo = topo_discovery.SDCTopo(sdcon_config.ODL_CONTROLLER_URL, sdcon_config.ODL_CONTROLLER_ID, sdcon_config.ODL_CONTROLLER_PW)
    print "\nAll hosts..."
    topo.print_all_hosts()
    print "\nAll links..."
    topo.print_all_links()
    
    src_ip, dst_ip = "192.168.0.4", "192.168.0.7"
    
    print "\nBefore setting a special path..."
    print_all_paths(src_ip, dst_ip)
    
    print "\nCreating a special path for %s -> %s..."%(src_ip,dst_ip)
    create_special_path(src_ip, dst_ip)
    print "\nAfter setting a special path..."
    print_all_paths(src_ip, dst_ip)
    
    print "\nDeleting the special path"
    delete_special_path(src_ip, dst_ip)
    print "\nBack to default path..."
    print_all_paths(src_ip, dst_ip)
    
    print "\nDefault path for %s -> %s :"%(src_ip, dst_ip)
    print get_default_path(topo, src_ip, dst_ip)

## Todo:
# Update queue (a qos setting for multiple queues..

# Main
def _print_usage():
    print("Usage:\t python %s test-path \t- test path creation/deletion"%(sys.argv[0]))
    print("      \t python %s set-path <src_IP> <dst_IP>\t- set a special path for <src> to <dst>"%(sys.argv[0]))
    print("      \t python %s del-path <src_IP> <dst_IP>\t- delete the special path for <src> to <dst> and back to default path"%(sys.argv[0]))
    print("      \t python %s get-path <src_IP> <dst_IP>\t- prints all paths between two hosts"%(sys.argv[0]))
    print("      \t python %s clear \t- clear all paths set up by SDCon"%(sys.argv[0]))

# Main
def main():
    network_monitor.start_monitor()
    
    if len(sys.argv) < 2:
        _print_usage()
        return
    
    if sys.argv[1] == "test-path":
        test_set_path()
    elif sys.argv[1] == "set-path":
        create_special_path(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == "del-path":
        delete_special_path(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == "get-path":
        print_all_paths(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == "clear":
        clear_all_paths()
    else:
        _print_usage()
        return

if __name__ == '__main__':
    main()
