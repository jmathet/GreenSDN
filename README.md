GreenSDN project : Create a plug and play application implementing ElasticTree

# Reporsitory Organisation
### ``` mininet-simulation ``` folder: 
* ``app`` : external application using the API REST of ONOS. This is the logical module of the ElasticTree application.
    *   ```topo_discovery.py``` : build graph of the current topology based on ONOS info
    *   ``` defaultpath.py``` :  create single default path between every host in the network
    *   ``` flowMeasure.py``` : compute the number of switches needed in each layer in order to satisfy traffic and save energy
    *   ``` monitoringTools.py ``` : basic functions
    *   ``` runElasticTree.py ``` : main function (deamon)
    *   ``` deviceList ``` : folder to store the list of devices for 4 and 4 degree fattre
    *   ``` ruleTempalte ```: folder to store json template of flow rules

* ``fattree.py`` : Python file to create virtual  SDN network connected to ONOS controller (fat-tree topology) using mininet. The topology is k-fattree (4 or 8 degree)

### ``` Pi-simulation``` folder:
* ``app`` : external application using the API REST of ONOS. This is the logical module of the ElasticTree application.
    *   ```topo_discovery.py``` : build graph of the current topology based on ONOS info
    *   ``` defaultpath.py``` :  create single default path between every host in the network
    *   ``` flowMeasure.py``` : compute the number of switches needed in each layer in order to satisfy traffic and save energy
    *   ``` monitoringTools.py ``` : basic functions
    *   ``` runElasticTree.py ``` : main function (deamon)
    *   ``` deviceList ``` : folder to store the list of devices for our special fattre
    *   ``` ruleTempalte ```: folder to store json template of flow rules

* ```scriptsSSH_pi ``` : scripts to simplify the management of Raspberry-pi



# Requirements
### ONOS requirements
* git
* zip
* curl
* unzip
* python 2.7
* python 3 (needed by Bazel)
* Bazel (minimum version : 0.27.0)

### ONOS
* Version 2.2
* Developper Quick Start : https://wiki.onosproject.org/display/ONOS/Developer+Quick+Start

### Python ElasticTree app requirements
* pip (package management)
* Python packages :
    *   networkx
    *   matplolib
    *   request
    *   json

# Run the appliction

### Mininet simulation

1. Run ONOS controller

    ``` 
    ~$ cd onos
    ~/onos$ bazel run onos-local -- clean debugm
     ```

2. Run CLI and activate some onos application
    ``` 
    ~/onos$ ./tools/test/bin/onos localhost
    onos > app activate proxyarp 
    onos > app activate fwd
    ``` 
    (proxyarp : for default path algo, fwd : for the host discovery - will be deactivated later)

3. Create network (mininet) 4 or 8 degree (```k```)

    ``` 
    ~$ cd GreenSDN/mininet/ 
    ~/GreenSDN/mininet$ sudo python fattree.py <k> {traffic|notraffic}
    mininet> pingall
     ```

4. Deactivate forwarding ONOS app

    ``` 
    onos> app deactivate fwd 
    ```

5. Create default path
    ```  
    ~$ cd GreenSDN/app_elastic_tree/ 
    python defaultpath.py <k>
    ```

6. Run ElasticTree algo
    ```  
    ~$ cd GreenSDN/app_elastic_tree/ 
    python runElasticTree.py <k>
    ```
### Pi simulation

1. Run ONOS controller

    ``` 
    ~$ cd onos
    ~/onos$ bazel run onos-local -- clean debugm
     ```

2. Run CLI and activate some onos application
    ``` 
    ~/onos$ ./tools/test/bin/onos localhost
    onos > app activate proxyarp 
    ``` 
<span style="color:red">/!\ WARNING </span> Without ```proxyarp``` default paths are not working


# Network topology

Fat-tree topology

## Network IP adresses
IP networks in a ```k=4``` fat-tree topology.
The idea is the following : to create different sub-network depinding the position in the fat-tree topology. We decided to use ```10.0.0.0/8``` as network address. Then, each POD sub-network is identify throught the 8 following bits. The POD p is using the ```10.p.0.0/16``` network IP address. The next 8 bits are used to specify the number of the edge switch in the current POD, the IP address of this sub-network is : ```10.p.e.0/24```. Finally, the last 8 bits are used by the number of the host connected to the edge switch e: ```10.p.e.h/24```

<img src="figures/network_GRAPH_16HOSTS(IP).png"
     alt="Markdown png"
     style="float: left; margin: 20px;" />

## Network default-path
 Flow rules for downward traffic match the IP destination and send the traffic to the corresponding port. Every layer of switches only matches a certain number of bits of the IP address, this number corresponds to the netmask of the following sub-net.
 The upward traffic is defined by: traffic that goes outside of the current sub-network. Here, only the source IP is used to balance the traffic on every links available. Once again, netmasks are used to reduced the number on flow rules.


<span style="color:red">/!\ WARNING </span> Higher priority (high number) matches FIRST
