#!/usr/bin/env python

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

# Stores H1 and H2 from user
global h1,h2
baseUrl = "http://128.250.25.13:8181/"


h1 = ""
h2 = ""

'''
print("Enter Host 1")
h1 = int(input())
print("\nEnter Host 2")
h2 = int(input())
print("\nEnter Host 3 (H2's Neighbour)")
h3 = int(input())
'''

h1 = b"192.168.0.2"
h2 = b"192.168.0.9"

flag = True


# Method To Get REST Data In JSON Format
def getResponse(url,choice):

	response = requests.get(url, auth=HTTPBasicAuth('admin', 'admin'))

	if(response.ok):
		jData = json.loads(response.content)
		if(choice=="topology"):
			topologyInformation(jData)
		elif(choice=="statistics"):
			getStats(jData)
	else:
		response.raise_for_status()

def topologyInformation(data):
	global switch
	global deviceMAC
	global deviceIP
	global hostPorts
	global linkPorts
	global G
	global cost

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
					switch[ip] = switchID

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

def getStats(data):
	print("Cost Computation....\n")
	global cost
	txRate = 0
	for i in data["node-connector"]:
		tx = int(i["opendaylight-port-statistics:flow-capable-node-connector-statistics"]["packets"]["transmitted"])
		rx = int(i["opendaylight-port-statistics:flow-capable-node-connector-statistics"]["packets"]["received"])
		txRate = tx + rx
		#print txRate

	time.sleep(2)

	response = requests.get(stats, auth=HTTPBasicAuth('admin', 'admin'))
	tempJSON = ""
	if(response.ok):
		tempJSON = json.loads(response.content)

	for i in tempJSON["node-connector"]:
		tx = int(i["opendaylight-port-statistics:flow-capable-node-connector-statistics"]["packets"]["transmitted"])
		rx = int(i["opendaylight-port-statistics:flow-capable-node-connector-statistics"]["packets"]["received"])
		cost = cost + tx + rx - txRate

	#cost = cost + txRate
	#print cost

def systemCommand(cmd):
	terminalProcess = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
	terminalOutput, stderr = terminalProcess.communicate()
	print("\n*** Flow Pushed\n")

def pushFlowRules(bestPath):

	bestPath = bestPath.split(b"::")

	for currentNode in range(0, len(bestPath)-1):
		if (currentNode==0):
			inport = hostPorts[h2]
			srcNode = bestPath[currentNode]
			dstNode = bestPath[currentNode+1]
			outport = linkPorts[srcNode + b"::" + dstNode]
			outport = outport.split(b"::")[0]
		else:
			prevNode = bestPath[currentNode-1]
			#print prevNode
			srcNode = bestPath[currentNode]
			#print srcNode
			dstNode = bestPath[currentNode+1]
			inport = linkPorts[prevNode + b"::" + srcNode]
			inport = inport.split(b"::")[1]
			outport = linkPorts[srcNode + b"::" + dstNode]
			outport = outport.split(b"::")[0]

		xmlSrcToDst = '<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"no\"?><flow xmlns=\"urn:opendaylight:flow:inventory\"><priority>32767</priority><flow-name>Load Balance 1</flow-name><match><in-port>'\
			+ str(inport).encode('ascii')+'</in-port><ipv4-destination>'\
			+ str(h1).encode('ascii')+'/32</ipv4-destination><ipv4-source>'\
			+ str(h2).encode('ascii')+'/32</ipv4-source><ethernet-match><ethernet-type><type>2048</type></ethernet-type></ethernet-match></match><id>1</id><table_id>0</table_id><instructions><instruction><order>0</order><apply-actions><action><order>0</order><output-action><output-node-connector>'\
			+ str(outport).encode('ascii')\
			+'</output-node-connector></output-action></action></apply-actions></instruction></instructions></flow>'

		xmlDstToSrc = '<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"no\"?><flow xmlns=\"urn:opendaylight:flow:inventory\"><priority>32767</priority><flow-name>Load Balance 2</flow-name><match><in-port>' \
			+ str(outport).encode('ascii') +'</in-port><ipv4-destination>'\
			+ str(h2).encode('ascii')+'/32</ipv4-destination><ipv4-source>'\
			+ str(h1).encode('ascii')+'/32</ipv4-source><ethernet-match><ethernet-type><type>2048</type></ethernet-type></ethernet-match></match><id>2</id><table_id>0</table_id><instructions><instruction><order>0</order><apply-actions><action><order>0</order><output-action><output-node-connector>'\
			+ str(inport).encode('ascii')\
			+'</output-node-connector></output-action></action></apply-actions></instruction></instructions></flow>'
		
		#print("\n{}\n".format(xmlSrcToDst));
		
		#print("\n{}\n".format(xmlDstToSrc));

		flowsutil.push_flow_xml(baseUrl, str(bestPath[currentNode]).encode('ascii'), "0", "1", xmlSrcToDst)
		flowsutil.push_flow_xml(baseUrl, str(bestPath[currentNode]).encode('ascii'), "0", "2", xmlDstToSrc)


	srcNode = bestPath[-1]
	prevNode = bestPath[-2]
	inport = linkPorts[prevNode + b"::" + srcNode]
	inport = inport.split(b"::")[1]
	outport = hostPorts[h1]

	xmlSrcToDst = '<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"no\"?><flow xmlns=\"urn:opendaylight:flow:inventory\"><priority>32767</priority><flow-name>Load Balance 1</flow-name><match><in-port>' + str(inport).encode('ascii') +'</in-port><ipv4-destination>'+ str(h1).encode('ascii')+'/32</ipv4-destination><ipv4-source>'+ str(h2).encode('ascii')+'/32</ipv4-source><ethernet-match><ethernet-type><type>2048</type></ethernet-type></ethernet-match></match><id>1</id><table_id>0</table_id><instructions><instruction><order>0</order><apply-actions><action><order>0</order><output-action><output-node-connector>' + str(outport).encode('ascii') +'</output-node-connector></output-action></action></apply-actions></instruction></instructions></flow>'

	xmlDstToSrc = '<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"no\"?><flow xmlns=\"urn:opendaylight:flow:inventory\"><priority>32767</priority><flow-name>Load Balance 2</flow-name><match><in-port>' + str(outport).encode('ascii') +'</in-port><ipv4-destination>'+ str(h2).encode('ascii')+'/32</ipv4-destination><ipv4-source>'+ str(h1).encode('ascii')+'/32</ipv4-source><ethernet-match><ethernet-type><type>2048</type></ethernet-type></ethernet-match></match><id>2</id><table_id>0</table_id><instructions><instruction><order>0</order><apply-actions><action><order>0</order><output-action><output-node-connector>' + str(inport).encode('ascii') +'</output-node-connector></output-action></action></apply-actions></instruction></instructions></flow>'

	#print("\n{}\n".format(xmlSrcToDst));

	#print("\n{}\n".format(xmlDstToSrc));
	
	flowsutil.push_flow_xml(baseUrl, str(bestPath[-1]).encode('ascii'), "0", "1", xmlSrcToDst)
	flowsutil.push_flow_xml(baseUrl, str(bestPath[-1]).encode('ascii'), "0", "2", xmlDstToSrc)

# Main
'''
try:
	flowsutil.del_all_flows(baseUrl,"40960021","0")
except ValueError as error:
	print(error)

try:	
	flows = flowsutil.get_all_flows(baseUrl,"40960021","0")
	print(flows)
except ValueError as error:
	print(error)

try:
	flows = flowsutil.del_flow(baseUrl, "40960021", "0", "1")
except ValueError as error:
	print(error)	

try:
	flows = flowsutil.get_flow(baseUrl,"40960021","0","1")
except ValueError as error:
	print(error)
	raise 
'''

while flag:

	#Creating Graph
	G = nx.Graph()

	# Stores Info About H3 And H4's Switch
	switch = {}

	# MAC of Hosts i.e. IP:MAC
	deviceMAC = {}

	# IP of Hosts i.e. MAC:IP
	deviceIP = {}

	# Stores Switch Links To H3 and H4's Switch
	switchLinks = {}

	# Stores Host Switch Ports
	hostPorts = {}

	# Stores Switch To Switch Path
	path = {}
	# Stores Link Ports
	linkPorts = {}
	# Stores Final Link Rates
	finalLinkTX = {}
	# Store Port Key For Finding Link Rates
	portKey = ""
	# Statistics
	global stats
	stats = ""
	# Stores Link Cost
	global cost
	cost = 0

	try:
		
		# Device Info (Switch To Which The Device Is Connected & The MAC Address Of Each Device)
		topology = "http://128.250.25.13:8181/restconf/operational/network-topology:network-topology"
		getResponse(topology,"topology")

		# Print Device:MAC Info
		print("\nDevice IP & MAC\n")
		print(deviceMAC)

		# Print Switch:Device Mapping
		print("\nSwitch:Device Mapping\n")
		print(switch)

		# Print Host:Port Mapping
		print("\nHost:Port Mapping To Switch\n")
		print(hostPorts)

		# Print Switch:Switch Port:Port Mapping
		print("\nSwitch:Switch Port:Port Mapping\n")
		print(linkPorts)


		print(G.nodes)
		print(G.edges)

		#flowsutil.del_all_flows_nodes(baseUrl, G.nodes , "0")

		# Paths
		print("\nAll Paths\n")
		#for path in nx.all_simple_paths(G, source=2, target=1):
			#print(path)
		for path in nx.all_shortest_paths(G, source=int(switch[h2].split(b':',1)[1]), target=int(switch[h1].split(b':',1)[1]), weight=None):
			print(path)

		# Cost Computation
		
		tmp = ''
		for currentPath in nx.all_shortest_paths(G, source=int(switch[h2].split(b':',1)[1]), target=int(switch[h1].split(b':',1)[1]), weight=None):
			for node in range(0,len(currentPath)-1):
				tmp = tmp + str(currentPath[node]) + '::'
				key = (str(currentPath[node])+ '::' + str(currentPath[node+1])).encode('ascii')
				port = linkPorts[key]
				port = port.split(b'::',1)[0]
				port = int(port)
				stats = "http://128.250.25.13:8181/restconf/operational/opendaylight-inventory:nodes/node/openflow:"+str(currentPath[node])+"/node-connector/openflow:"+str(currentPath[node])+":"+str(port)
				getResponse(stats,"statistics")
			tmp = tmp + str(currentPath[len(currentPath)-1])
			tmp = tmp.strip("::")
			finalLinkTX[tmp] = cost
			cost = 0
			tmp = ""

		print("\nFinal Link Cost\n")
		print(finalLinkTX)

		shortestPath = min(finalLinkTX, key=finalLinkTX.get)
		print("\n\nShortest Path: ",shortestPath)

		pushFlowRules(shortestPath.encode('ascii'))

		time.sleep(SLEEP_INTERVAL)
	except ValueError as error:
		print(error)
		raise
	except KeyboardInterrupt:
		break
		exit
