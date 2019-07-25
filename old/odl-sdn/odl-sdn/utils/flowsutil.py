import requests
from requests.auth import HTTPBasicAuth
from symbol import except_clause
import sys

    
    
def get_all_flows (baseUrl, openflow_node, table_id):
    try:
        url = baseUrl + 'restconf/config/opendaylight-inventory:nodes/node/openflow:' + str(openflow_node,'ascii','ignore') + '/table/' + str(table_id,'ascii','ignore')
        response = requests.get(url, auth=HTTPBasicAuth("admin", "admin"),  headers={"Accept": "application/json"})
        response.raise_for_status();
        return response.json()
    except(requests.exceptions.Timeout,requests.exceptions.RequestException,requests.exceptions.RequestException) as err:
        print(err)
        sys.exit(1)    
    
def get_flow (baseUrl, openflow_node, table_id, flow_id):
    try:
        url = baseUrl + 'restconf/config/opendaylight-inventory:nodes/node/openflow:' + str(openflow_node,'ascii','ignore')+'/table/' + str(table_id,'ascii','ignore') + '/flow/' + str(flow_id,'ascii','ignore')
        response = requests.get(url, auth=HTTPBasicAuth("admin", "admin"),  headers={"Accept": "application/json"})
        response.raise_for_status();
        return response.json()
    except(requests.exceptions.Timeout,requests.exceptions.RequestException,requests.exceptions.RequestException) as err:
        print(err)
        sys.exit(1)

    

def del_all_flows (baseUrl, openflow_node, table_id):
    try:
        url = baseUrl + 'restconf/config/opendaylight-inventory:nodes/node/openflow:' + str(openflow_node,'ascii','ignore')+'/table/' + str(table_id,'ascii','ignore')
        response = requests.delete(url, auth=HTTPBasicAuth("admin", "admin"),  headers={"Accept": "application/json"})
        response.raise_for_status();
    except(requests.exceptions.Timeout,requests.exceptions.RequestException,requests.exceptions.RequestException) as err:
        print(err)
        sys.exit(1)
    
def del_flow (baseUrl, openflow_node, table_id, flow_id):
    try:
        url = baseUrl + 'restconf/config/opendaylight-inventory:nodes/node/openflow:' + openflow_node +'/table/' + str(table_id,'ascii','ignore') + '/flow/' + str(flow_id,'ascii','ignore')
        response = requests.delete(url, auth=HTTPBasicAuth("admin", "admin"),  headers={"Accept": "application/json"})
        response.raise_for_status()
    except(requests.exceptions.Timeout,requests.exceptions.RequestException,requests.exceptions.RequestException) as err:
        print(err)
        if(response.status_code != 404):
            sys.exit(1)
    
def push_flow_xml (baseUrl, openflow_node, table_id, flow_id, xml):
    try:
        url=''
        url = baseUrl + 'restconf/config/opendaylight-inventory:nodes/node/openflow:' + str(openflow_node,'ascii','ignore') +'/table/' + str(table_id,'ascii','ignore') + '/flow/' + str(flow_id,'ascii','ignore')
        response = requests.put(url, data=xml, auth=HTTPBasicAuth("admin", "admin"),  headers={"Accept": "application/json", "Content-Type" : "application/xml"})
        response.raise_for_status();
    except(requests.exceptions.Timeout,requests.exceptions.RequestException,requests.exceptions.RequestException) as err:
        print(err)
        sys.exit(1)
    
def del_all_flows_nodes (baseUrl, openflow_nodes, table_id):
        for openflow_node in openflow_nodes:
                del_all_flows (baseUrl, str(openflow_node), table_id)
                
def del_all_nodes_flowid (baseUrl, openflow_nodes, table_id, flowid):
        for openflow_node in openflow_nodes:
            del_flow (baseUrl, openflow_node, table_id, flowid)
#test 
    