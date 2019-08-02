GreenSDN project : Create a plug and play application implementing ElasticTree

# Reporsitory Organisation
* ``app_elastic_tree`` : external application using the API REST of ONOS. This is the logical module of the ElasticTree application.
    *   ```topo_discovery.py``` : build graph of the current topology based on ONOS info
    *   ``` defaultpath.py``` :  create single default path between every host in the network
    *   ``` flowMeasure.py``` : compute the number of switches needed in each layer in order to satisfy traffic and save energy

* ``mininet`` : Python file to create virtual  SDN network connected to ONOS controller (fat-tree topology) using mininet

* ``old`` : backup of some files (to be delete in the final version)

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

1. Run ONOS controller

    ``` 
    ~$ cd onos
     ~/onos$ bazel run onos-local -- clean debugm
     ```

2. Run CLI and activate some onos application
    ``` ~/onos$ ./tools/test/bin/onos localhost
    onos > app activate proxyarp 
    onos > app activate fwd
    ``` 
    (proxyarp : for default path algo, fwd : for the host discovery - will be deactivated later)

3. Create network (mininet) 4 or 8 degree (```k```)

    ``` 
    ~$ cd GreenSDN/mininet/ 
     ~/GreenSDN/mininet$ sudo python fattree.py <k>
     mininet> pingall
     ```

4. Deactivate forwarding ONOS app

    ``` onos> app deactivate fwd 
    ```

5. Create default path
    ```  
    ~$ cd GreenSDN/app_elastic_tree/ 
     python defaultpath.py <k>
     ```

# Network topology

Fat-tree topology

## Network IP adresses
IP networks in a ```k=4``` fat-tree topology.

<img src="network_GRAPH_16HOSTS(IP).png"
     alt="Markdown png"
     style="float: left; margin: 20px;" />

## Network default-path