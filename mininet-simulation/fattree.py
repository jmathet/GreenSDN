from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node
from mininet.node import Controller, RemoteController
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.util import waitListening
import sys, time


class FatTree( Topo ):

    CoreSwitchList = []
    AggSwitchList = []
    EdgeSwitchList = []
    HostList = []

    def __init__( self, k):
        " Create Fat Tree topo."
        self.pod = k
        self.iCoreLayerSwitch = (k/2)**2
        self.iAggLayerSwitch = k*k/2
        self.iEdgeLayerSwitch = k*k/2
        self.density = k/2
        self.iHost = self.iEdgeLayerSwitch * self.density



        # Init Topo
        Topo.__init__(self)

        self.createTopo()

        self.createLink(1000)

    def createTopo(self):
        self.createCoreLayerSwitch(self.iCoreLayerSwitch)
        self.createAggLayerSwitch(self.iAggLayerSwitch)
        self.createEdgeLayerSwitch(self.iEdgeLayerSwitch)
        self.createHost(self.iHost)

    """
    Create Switch and Host
    """

    def _addSwitch(self, number, level, switch_list):
        for x in xrange(1, number+1):
            PREFIX = str(level) + "00"
            if x >= int(10):
                PREFIX = str(level) + "0"
            switch_list.append(self.addSwitch('s' + PREFIX + str(x)))

    def createCoreLayerSwitch(self, NUMBER):
        self._addSwitch(NUMBER, 1, self.CoreSwitchList)

    def createAggLayerSwitch(self, NUMBER):
        self._addSwitch(NUMBER, 2, self.AggSwitchList)

    def createEdgeLayerSwitch(self, NUMBER):
        self._addSwitch(NUMBER, 3, self.EdgeSwitchList)

    def createHost(self, NUMBER):
        for x in xrange(1, NUMBER+1):
            PREFIX = "h"
            self.HostList.append(self.addHost(PREFIX + str(x)))

    """
    Add Link
    """
    def createLink(self, bandwidth):
        # bandwidth in Mbit
        linkopts = dict(bw=bandwidth) 
        end = self.pod/2
        for x in xrange(0, self.iAggLayerSwitch, end):
            for i in xrange(0, end):
                for j in xrange(0, end):
                    self.addLink(
                        self.CoreSwitchList[i*end+j],
                        self.AggSwitchList[x+i],
                        **linkopts)

        for x in xrange(0, self.iAggLayerSwitch, end):
            for i in xrange(0, end):
                for j in xrange(0, end):
                    self.addLink(
                        self.AggSwitchList[x+i],
                        self.EdgeSwitchList[x+j],
                        **linkopts)

        for x in xrange(0, self.iEdgeLayerSwitch):
            for i in xrange(0, self.density):
                self.addLink(
                    self.EdgeSwitchList[x],
                    self.HostList[self.density * x + i],
                    **linkopts)

"""
Set IP
"""
def setHostIp(net, topo):
    hosts = []
    for k in xrange(len(topo.HostList)):
        hosts.append(net.get(topo.HostList[k]))

    h = 0
    end = topo.pod/2
    print (end)
    for pod in range(1, topo.pod + 1):
        for edgeSwitchNummber in range(1, end+1):
            for hostNbInSwitch in range(1, end+1):
                print("pod = " + str(pod) + " / edgeSwitchNummber = " + str(edgeSwitchNummber) + " / hostNbInSwitch = " + str(hostNbInSwitch))
                hosts[h].setIP("10.%d.%d.%d" % (pod, edgeSwitchNummber, hostNbInSwitch))
                print(hosts[h].IP())
                print(h+1)
                h += 1
                


topos = { 'fattree' : ( lambda k : FatTree(k)) }


def runMyNetwork(k, traffic):
    "Create Fat Tree network"
    mytopo = FatTree(k)
    net = Mininet(topo=mytopo, link = TCLink, controller=RemoteController( 'c0', ip='130.194.73.219')) #TODO : mettre le bon controleur
    net.start()
    # Set hosts IP addresses.
    setHostIp(net, mytopo)
    print(traffic)
    if (traffic == "traffic"):
        # Ping all
        net.pingAll()
        time.sleep(10)
        # Traffic generation
        generateTraffic(net,mytopo)
    else:
        # CLI running
        CLI(net)
    net.stop()
    
def generateTraffic(net, topo):
# Uniform traffic generator
    print("\n TRAFFIC GENERATOR \n")
    for bandwidth in range(100,1000, 100):
        print(bandwidth)
        for h in range(topo.iHost//2):
            dst = net.hosts[2*h +1]
            # Create the server command and sends it
            serverCmd = "iperf -s -u &"
            dst.cmd(serverCmd)
            src = net.hosts[h]
            print(str(src.IP()) + " >> " + str(dst.IP()))
            # Create the client command and sends it
            clientCmd = "iperf -c " + str(dst.IP()) + " -u -b " + str(bandwidth) + "m -t 120 &"
            src.cmd(clientCmd)
        time.sleep(120)

if __name__ == '__main__':
    # Tell mininet to print useful information
    setLogLevel('info')
    if (len(sys.argv) != 3):
        print("Usage : sudo python fattree.py k traffic/notraffic")
    else: 
        runMyNetwork(int(sys.argv[1]), sys.argv[2])
