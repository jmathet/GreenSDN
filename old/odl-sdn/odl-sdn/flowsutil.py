import requests
from requests.auth import HTTPBasicAuth
from symbol import except_clause

    
    
def get_all_flows (baseUrl, openflow_node, table_id):
    url = baseUrl + 'restconf/config/opendaylight-inventory:nodes/node/openflow:' + openflow_node + '/table/' + table_id
    response = requests.get(url, auth=HTTPBasicAuth("admin", "admin"),  headers={"Accept": "application/json"})
    if response.status_code == 200:
        return response.json()
    else:   
        raise ValueError('Error:', response.json())
    
    
def get_flow (baseUrl, openflow_node, table_id, flow_id):
    url = baseUrl + 'restconf/config/opendaylight-inventory:nodes/node/openflow:' + openflow_node+'/table/' + table_id + '/flow/' + flow_id
    response = requests.get(url, auth=HTTPBasicAuth("admin", "admin"),  headers={"Accept": "application/json"})
    if response.status_code == 200:
        return response.json()
    else:   
        raise ValueError('Error:', response.json())
    

def del_all_flows (baseUrl, openflow_node, table_id):
    url = baseUrl + 'restconf/config/opendaylight-inventory:nodes/node/openflow:' + openflow_node+'/table/' + table_id
    response = requests.delete(url, auth=HTTPBasicAuth("admin", "admin"),  headers={"Accept": "application/json"})
    if response.status_code != 200:
        raise ValueError('Error:', response.json())
    
def del_flow (baseUrl, openflow_node, table_id, flow_id):
    url = baseUrl + 'restconf/config/opendaylight-inventory:nodes/node/openflow:' + openflow_node+'/table/' + table_id + '/flow/' + flow_id
    response = requests.delete(url, auth=HTTPBasicAuth("admin", "admin"),  headers={"Accept": "application/json"})
    if response.status_code != 200:
        raise ValueError('Error:', response.json())
    
def push_flow_xml (baseUrl, openflow_node, table_id, flow_id, xml):
    url = baseUrl + 'restconf/config/opendaylight-inventory:nodes/node/openflow:' + openflow_node+'/table/' + table_id + '/flow/' + flow_id
    response = requests.put(url, data=xml, auth=HTTPBasicAuth("admin", "admin"),  headers={"Accept": "application/json", "Content-Type" : "application/xml"})
    if response.status_code != 200 and response.status_code != 201:
        raise ValueError('Error:', response.json())
    
def del_all_flows_nodes (baseUrl, openflow_nodes, table_id):
        for openflow_node in openflow_nodes:
            try:
                del_all_flows (baseUrl, str(openflow_node), table_id)
            except ValueError:
                pass
#test 
    