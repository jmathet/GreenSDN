import requests
import json

CONTROLLER_URL = "http://127.0.0.1:8181/onos/v1"
auth = ("onos", "rocks")
headers = {'Content-Type':'application/json' , 'Accept':'application/json'}

FLOWSSTAT_URL = CONTROLLER_URL + "/statistics/flows/link"
FLOWSPOST_URL = CONTROLLER_URL + "/flows"

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

def postJsonData(url, jsonFile):
    r = requests.post(url, data=json.dumps(jsonFile), auth=auth, headers=headers)
    return r

def getFlowStatFromDevice(device, port):
    url = FLOWSSTAT_URL + "?device=" + device + "&port=" + port
    return(getJsonData(url))


def postFlowRule(deviceID, inPort, outPort):
    with open('ruleTemplate.json') as json_file:  
        flowRule = json.load(json_file)
    flowRule["flows"][0]["deviceId"] = deviceID
    flowRule["flows"][0]["treatment"]["instructions"][0]["port"] = outPort
    flowRule["flows"][0]["selector"]["criteria"][0]["port"] = inPort
    url = FLOWSPOST_URL + "?appId=myapp"
    r = postJsonData(url, flowRule)
    return r
