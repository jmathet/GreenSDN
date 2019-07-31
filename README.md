GreenSDN

# Reporsitory Organisation
* ``app_elastic_tree`` : external application using the API REST of ONOS. This is the logical module of the ElasticTree application.

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

# Run the appliction

1. Run ONOS controller

``` ~$ cd onos```
``` ~/onos$ bazel run onos-local -- clean debug```

2. Run CLI and activate some onos application
``` ~/onos$ ./tools/test/bin/onos localhost ```
``` app activate proxyarp``` (for default path algo)

3. Create network (mininet)

``` ~$ cd GreenSDN/mininet/ ```
``` ~/GreenSDN/mininet$ sudo python fattree_k4.py ```

# Network topology

Fat-tree topology

## Network IP adresses
IP networks in a ```k=4``` fat-tree topology.

<img src="network_GRAPH_16HOSTS(IP).png"
     alt="Markdown png"
     style="float: left; margin-right: 10px;" />