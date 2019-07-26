import requests
import json

CONTROLLER_URL = "http://127.0.0.1:8181/onos/v1"

auth = ("onos", "rocks")
headers = {'Content-Type':'application/json' , 'Accept':'application/json'}

DEFAULT_ACCESS_CAPACITY = 5e8
DEFAULT_CAPACITY = 5e8

FLOWSSTAT_URL = CONTROLLER_URL + "/statistics/flows/link"
FLOWS_URL = CONTROLLER_URL + "/flows" 

PORTSTAT_URL = CONTROLLER_URL + "/statistics/ports"
PORT_URL = CONTROLLER_URL + "/devices/"

k = 4 # Switch degree

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

def portNumber2Mac(halfurl, deviceId):
    deviceId = deviceId.replace(":", "%3A")
    url = halfurl + deviceId + "/ports"
    mac = getJsonData(url)

    mapping = {}
    for port in mac["ports"]:
	    mapping[port["port"]] = port["annotations"]["portMac"]
    return mapping

def getJsonData(url):
    r = requests.get(url, auth=auth)
    return r.json()

def delJsonData(url):
    r = requests.delete(url, auth=auth)
    return r

def postJsonData(url, jsonFile):
    r = requests.post(url, data=json.dumps(jsonFile), auth=auth, headers=headers)
    return r

def getFlowStatFromDevice(device, port):
    url = FLOWSSTAT_URL + "?device=" + device + "&port=" + port
    return(getJsonData(url))


def postFlowRule(deviceID, inPort, outPort):
    # Loading the flow tule template
    with open('ruleTemplate_portIN_portOUT.json') as json_file:  
        flowRule = json.load(json_file)
    # Replacing some fields
    flowRule["flows"][0]["deviceId"] = deviceID
    flowRule["flows"][0]["treatment"]["instructions"][0]["port"] = outPort
    flowRule["flows"][0]["selector"]["criteria"][0]["port"] = inPort

    r = postJsonData(FLOWS_URL, flowRule)
    return r

def postFlowRule_dstIP_outPort(deviceID, destIP, outPort):
    # Loading the flow tule template
    with open('ruleTemplate_IPdest_portOUT.json') as json_file:  
        flowRule = json.load(json_file)
    # Replacing some fields
    flowRule["flows"][0]["deviceId"] = deviceID
    flowRule["flows"][0]["treatment"]["instructions"][0]["port"] = outPort
    flowRule["flows"][0]["selector"]["criteria"][0]["ip"] = destIP
    print(json.dumps(flowRule))
    r = postJsonData(FLOWS_URL, flowRule)
    return r

def deleteAllFlowRule(deviceID):
    # Getting the list of flow rules for the current device
    url = FLOWS_URL + "/" + deviceID
    flowList = getJsonData(url)
    # Removal of each flow (one by one) 
    for flow in flowList["flows"]:
        print(flow["id"])
        url = FLOWS_URL + "/" + deviceID + "/" + flow["id"]
        r = delJsonData(url)
        print(url)
    return r