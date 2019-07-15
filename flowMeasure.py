import requests
import json
from datetime import datetime
import time
import math

PORTSTAT_URL = "http://130.194.73.219:8181/onos/v1/statistics/ports"
PORT_URL = "http://130.194.73.219:8181/onos/v1/devices/"
FLOWSSTAT_URL = "http://127.0.0.1:8181/onos/v1/statistics/flows/link"
auth = ("onos", "rocks")
CHAIN_NAME = "networkId"
interval = 0.3
EDGE_DEVICES = ["of:0000000000000bb9",
                "of:0000000000000bba",
                "of:0000000000000bbb",
                "of:0000000000000bbc",
                "of:0000000000000bbd",
                "of:0000000000000bbe",
                "of:0000000000000bbf",
                "of:0000000000000bc0"]
AGREGATION_DEVICES = ["of:00000000000007d1",
                    "of:00000000000007d2",
                    "of:00000000000007d3",
                    "of:00000000000007d4",
                    "of:00000000000007d5",
                    "of:00000000000007d6",
                    "of:00000000000007d7",
                    "of:00000000000007d8"]
CORE_DEVICES = ["of:00000000000003e9",
                "of:00000000000003ea",
                "of:00000000000003eb",
                "of:00000000000003ec"]

def getJsonData(url):
    r = requests.get(url, auth=auth)
    return r.json()

def getPortStat(url):
    portStat = getJsonData(url)

    bits = {}
    portBits = {}
    for device in portStat["statistics"]:
	deviceId = device["device"]
        for p in device["ports"]:
            bits[p["port"]] = (p["bytesSent"] + p["bytesReceived"]) * 8
        portBits[deviceId] = bits
    #print json.dumps(portBits)
    return portBits

def getFlowStat(r):
    # url : url on the API REST PATH for flow statistic
    # r : link rate paraneter (to set the desired average link utilisation)

    listLEdge_up_p_e = {} # Number of links for edge swicth e in pod p (where 2*p+e is the list index)
    listLAgg_down_p = {} # Number of down links needs to suport the down-traffic (where the pod number p is the list index)
    NAgg_up_p = {} # TODO comment (p index)

    for i in range(0,4):
        rate = 0
        for j in range(0,2):
            url1 = FLOWSSTAT_URL + "?device=" + EDGE_DEVICES[2*i+j] + "&port=1"
            url2 = FLOWSSTAT_URL + "?device=" + EDGE_DEVICES[2*i+j] + "&port=2"

            flowStat1 = getJsonData(url1)
            flowStat2 = getJsonData(url2)

            rate1_up = flowStat1["loads"][0]["rate"] # rate between edge j and a1 of the pod p in the up direction
            rate2_up = flowStat2["loads"][0]["rate"] # rate between edge j and a2 of the pod p in the up direction
            rate1_down = flowStat1["loads"][1]["rate"] # rate between edge j and a1 of the pod p in the down direction 
            rate2_down = flowStat2["loads"][1]["rate"] # rate between edge j and a2 of the pod p in the down direction

            LEdge_up_p_e = (rate1_up + rate2_up)*8*10**(-9) # total rate up in Gbits/sec
            LEdge_down_p_e = (rate1_down + rate2_down)*8*10**(-9) # total rate down in Gbits/sec

            # listLEdge_up_p_e.append(LEdge_up_p_e) # ERREUR 

            LEdge_p_e = max(math.ceil(LEdge_up_p_e/r),math.ceil(LEdge_down_p_e/r),1) # 1GBytes links

            print("Number of links needs between the edge swicth " + str(2*i+j) + " and the aggregation layer")
            print("LEdge_up_p_e = " + str(LEdge_up_p_e) + " Gbits/sec")
            print("LEdge_down_p_e = " + str(LEdge_down_p_e) + " Gbits/sec")
            print("LEdge_p_e = " + str(LEdge_p_e) + " (1 Gbits/sec links)")
        
        # NAgg_up_p = NAgg_up_p.extend(max(listLEdge_up_p_e))


    print("**************************************************************************")
    for i in range(0,4): # pod range
        rate_up = 0
        rate_down = 0
        for j in range(0,2): # Aggr devices in the pod
            url1 = FLOWSSTAT_URL + "?device=" + AGREGATION_DEVICES[2*i+j] + "&port=1"
            url2 = FLOWSSTAT_URL + "?device=" + AGREGATION_DEVICES[2*i+j] + "&port=2"

            flowStat1 = getJsonData(url1)
            flowStat2 = getJsonData(url2)

            rate1_up = flowStat1["loads"][0]["rate"] # rate between aggregation j and c1 of the pod p in the up direction
            rate2_up = flowStat2["loads"][0]["rate"] # rate between edge j and c2 of the pod p in the up direction
            rate1_down = flowStat1["loads"][1]["rate"] # rate between edge j and c1 of the pod p in the down direction 
            rate2_down = flowStat2["loads"][1]["rate"] # rate between edge j and c2 of the pod p in the down direction

            LAgg_up_p = rate_up + (rate1_up + rate2_up)*8*10**(-9) # total rate up in Gbits/sec
            LAgg_down_p = rate_down + (rate1_down + rate2_down)*8*10**(-9) # total rate down in Gbits/sec

        # listLAgg_down_p.extend(LAgg_down_p) # ERREUR

        LAgg_p = max(math.ceil(LAgg_up_p/r),math.ceil(LAgg_down_p/r),1) # 1GBytes links

        k = 4 # Switch degree
        # NAgg_down_p = math.ceil(max(listLAgg_down_p/k/2)) # ERREUR SANS DOUTE

        # NAgg_p = max(NAgg_up_p(i),) # A FINIR


        print("Number of links needs between aggregation swicthes of the pod " + str(i) + " and the core layer")
        print("LAgg_up_p = " + str(LAgg_up_p) + " Gbits/sec")
        print("LAgg_down_p = " + str(LAgg_down_p) + " Gbits/sec")
        print("LAgg_p = " + str(LAgg_p) + " (1 Gbits/sec links)")
        

    print("**************************************************************************")

    
    return flowStat1

def portNumber2Mac(halfurl, deviceId):
    deviceId = deviceId.replace(":", "%3A")
    url = halfurl + deviceId + "/ports"
    mac = getJsonData(url)

    mapping = {}
    for port in mac["ports"]:
	    mapping[port["port"]] = port["annotations"]["portMac"]
    #print json.dumps(mapping)
    return mapping


def getportSpeed(url):

    bits1 = getPortStat(url)
    time.sleep(interval)
    bits2 = getPortStat(url)
    time.sleep(interval)

    portSpeed = {}
    for deviceId in bits1.keys():
	mapping = portNumber2Mac(PORT_URL, deviceId)
	for portNumber in bits1[deviceId]:
            #print portNumber
            #print list(mapping.keys())
	    if str(portNumber) in list(mapping.keys()):
                #print portNumber
	    	portSpeed[mapping[str(portNumber)]] = int((bits2[deviceId][portNumber] - bits1[deviceId][portNumber])/interval)
    return portSpeed

def send(url, chains, sliceInfo):

    res = {}
    data = {}

    portSpeed = getportSpeed(url)

    for chainName in chains.keys():
        data["CHAIN_NAME"].append(chainName)
        chainSpeed ={}
        for name in chains[chainName].keys():
            chainSpeed[netid] = (portSpeed[sliceInfo[name]["portMac"]])
        l = sorted(chainSpeed.items(), key=lambda d:d[1], reverse=True)

        data["flows"].append(l[0][1])
        data["src"].append(sliceInfo[l[0][0]]["networkId"])
        data["dst"].append(sliceInfo[l[1][0]]["networkId"])

    res["status"] = "ok"
    res["data"] = data

    return json.dumps(res)


if __name__ == "__main__":
    getFlowStat(1)
    '''
    boolean flag = False
    delta = 0
    while (flag && delta < 600) {
        send = send(PORTSTAT_URL,  )
        print send
        time.sleep(0.7)
        delta += 1
    }
    '''