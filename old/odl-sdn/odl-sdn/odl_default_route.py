#!/usr/bin/env python

# odl_default_route.py
# This program finds network topology and set up a default route using ECMP
# Network traffic will be distributed evenly among multiple paths based on src IP
# Base source code for topology discovery and flow table injection is from:
#      https://github.com/nayanseth/sdn-loadbalancing

import requests
from requests.auth import HTTPBasicAuth
import json
import unicodedata
from subprocess import Popen, PIPE
import time
import networkx as nx
from sys import exit
import flowsutil
from networkx.algorithms import flow

SLEEP_INTERVAL=5

ODL_CONTROLLER_URL = "http://128.250.25.13:8181/"
ODL_CONTROLLER_ID = "admin"
ODL_CONTROLLER_PW = "admin"

HOST_IP_REFIX = b"192.168.0."
HOST_IP_RANGE = range(2,9+1)
DEFAULT_PRIORITY = 1000

#Creating Graph
G = nx.Graph()
# MAC of Hosts i.e. IP:MAC
deviceMAC = {}
# Edge switch connection of each host
mapHostSwitch = {}
# Stores Host Switch Ports
hostPorts = {}
# Stores Link Ports
linkPorts = {}

# Method To Get REST Data In JSON Format
def getResponse(url):
    response = requests.get(url, auth=HTTPBasicAuth(ODL_CONTROLLER_ID, ODL_CONTROLLER_PW))

    if(response.ok):
        jData = json.loads(response.content)
        topologyInformation(jData)
    else:
        response.raise_for_status()

def topologyInformation(data):
    global mapHostSwitch
    global deviceMAC
    global hostPorts
    global linkPorts
    global G
    deviceIP={}

    for i in data["network-topology"]["topology"]:
        for j in i["node"]:
            # Device MAC and IP

            if "host-tracker-service:addresses" in j:
                for k in j["host-tracker-service:addresses"]:
                    ip = k["ip"].encode('ascii')
                    mac = k["mac"].encode('ascii')
                    deviceMAC[ip] = mac
                    deviceIP[mac] = ip

            # Device Switch Connection and Port

            if "host-tracker-service:attachment-points" in j:

                for k in j["host-tracker-service:attachment-points"]:
                    mac = k["corresponding-tp"].encode('ascii')
                    mac = mac.split(b':',1)[1]
                    ip = deviceIP[mac]
                    temp = k["tp-id"].encode('ascii')
                    switchID = temp.split(b':')
                    port = switchID[2]
                    hostPorts[ip] = port
                    switchID = switchID[0] + b':' + switchID[1]
                    mapHostSwitch[ip] = switchID

    # Link Port Mapping
    for i in data["network-topology"]["topology"]:
        for j in i["link"]:
            if "host" not in j['link-id']:
                src = j["link-id"].encode('ascii').split(b':')
                srcPort = src[2]
                dst = j["destination"]["dest-tp"].encode('ascii').split(b':')
                dstPort = dst[2]
                srcToDst = src[1] + b'::' + dst[1]
                linkPorts[srcToDst] = srcPort + b'::' + dstPort
                G.add_edge((int)(src[1]),(int)(dst[1]))

def systemCommand(cmd):
    terminalProcess = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
    terminalOutput, stderr = terminalProcess.communicate()
    print("\n*** Flow Pushed\n")

def pushFlow(switch, inport, outport, srcHost, dstHost, tableId=0, flowId=1, priority=DEFAULT_PRIORITY, flowname="Default"):
    print("Pushing flow into %s (inPort %s -> outPort %s) for %s --> %s"%(switch, str(inport), str(outport), srcHost, dstHost))
    xml = '''<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"no\"?>
        <flow xmlns=\"urn:opendaylight:flow:inventory\">
            <priority>'''+str(priority)+'''</priority>
            <flow-name>'''+str(flowname)+'''</flow-name>
            <match>
                <in-port>''' + str(inport).encode('ascii')+'''</in-port>
                <ipv4-destination>''' + str(dstHost).encode('ascii')+'''/32</ipv4-destination>
                <ipv4-source>''' + str(srcHost).encode('ascii')+'''/32</ipv4-source>
                <ethernet-match><ethernet-type><type>2048</type></ethernet-type></ethernet-match>
            </match>
            <id>'''+str(flowId)+'''</id>
            <table_id>'''+str(tableId)+'''</table_id>
            <instructions><instruction>
                <order>0</order><apply-actions><action><order>0</order><output-action>
                <output-node-connector>''' + str(outport).encode('ascii') +'''</output-node-connector></output-action></action></apply-actions>
            </instruction></instructions>
        </flow>'''
        #print(xmlSrcToDst)
    flowsutil.push_flow_xml(ODL_CONTROLLER_URL, switch, str(tableId), str(flowId), xml)

flowId=1
def pushFlowRules(path, srcHost, dstHost):
    global flowId
    for i in range(len(path)):
        thisNode = str(path[i])
        if(len(path)==1):
            #srcHost::Switch::dstHost
            inport  = hostPorts[srcHost]
            outport = hostPorts[dstHost]
        elif (i == 0):
            #srcHost::Switch
            nextNode = str(path[i+1])
            inport = hostPorts[srcHost]
            outport = linkPorts[thisNode + b"::" + nextNode].split(b"::")[0]
        elif (i == len(path)-1):
            #Switch::dstHost
            prevNode = str(path[i-1])
            inport = linkPorts[prevNode + b"::" + thisNode].split(b"::")[1]
            outport = hostPorts[dstHost]
        else:
            #Switch::Switch
            prevNode = str(path[i-1])
            nextNode = str(path[i+1])
            inport = linkPorts[prevNode + b"::" + thisNode].split(b"::")[1]
            outport = linkPorts[thisNode + b"::" + nextNode].split(b"::")[0]
        pushFlow(thisNode.encode('ascii'), inport, outport, srcHost, dstHost, flowId=flowId)
    flowId+=1
    return

def findRoute(srcHost, dstHost, selection=0):
    # Paths
    print("\nAll Paths for %s --> %s"%(srcHost, dstHost))
    paths= nx.all_shortest_paths(G, 
            source=int(mapHostSwitch[srcHost].split(b':',1)[1]), 
            target=int(mapHostSwitch[dstHost].split(b':',1)[1]), 
            weight=None)
    allPaths = list(paths)
    for path in allPaths:
        print(path)

    print("\nSelected Path for %s --> %s"%(srcHost, dstHost))
    selectedPath = allPaths[min(selection, len(allPaths)-1)]
    print(selectedPath)

    pushFlowRules(selectedPath, srcHost, dstHost)


# Main
def main():
    try:
        # Device Info (Switch To Which The Device Is Connected & The MAC Address Of Each Device)
        topology = "http://128.250.25.13:8181/restconf/operational/network-topology:network-topology"
        getResponse(topology)

        print("\nDevice IP & MAC")
        print(deviceMAC)

        print("\nHost to EdgeSwitch Mapping")
        print(mapHostSwitch)

        print("Host to EdgeSwitch Port Mapping")
        print(hostPorts)

        print("\nLinkPorts:Switch to Switch Port Mapping")
        print(linkPorts)

        for srcIp in HOST_IP_RANGE:
            for dstIp in HOST_IP_RANGE:
                if srcIp == dstIp:
                    continue

                srcHost = HOST_IP_REFIX+str(srcIp)
                dstHost = HOST_IP_REFIX+str(dstIp)
                findRoute(srcHost, dstHost, srcIp%2)

    except ValueError as error:
        print(error)
        raise
    except KeyboardInterrupt:
        exit

main()
