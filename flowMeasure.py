import requests
import json
from datetime import datetime
import time

PORTSTAT_URL = "http://130.194.73.219:8181/onos/v1/statistics/ports"
PORT_URL = "http://130.194.73.219:8181/onos/v1/devices/"
auth = ("onos", "rocks")
CHAIN_NAME = "networkId"
interval = 0.3

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
    print(json.dumps(getPortStat(PORTSTAT_URL), indent=4, sort_keys=True))
    #getPortStat(PORTSTAT_URL)
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