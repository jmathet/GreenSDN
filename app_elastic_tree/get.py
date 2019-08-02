from monitoringTools import *

if __name__ == "__main__":
    data = getJsonData("http://127.0.0.1:8181/onos/v1/devices")
    for device in data["devices"]:
        print(device["id"])