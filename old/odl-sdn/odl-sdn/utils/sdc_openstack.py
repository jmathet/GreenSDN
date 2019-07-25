from keystoneauth1.identity import v3
from keystoneauth1 import session
from novaclient import client
from openstack import connection as openstack_connection

OPENSTACK_AUTH_URL = "http://iaas.cis.unimelb.edu.au:5000/v3"
OPENSTACK_AUTH_ADMIN_ID = "admin"
OPENSTACK_AUTH_ADMIN_PW = "itscloudytoday11"

#OPENSTACK_AUTH_URL = "http://192.168.50.111/identity"
#OPENSTACK_AUTH_ADMIN_ID = "admin"
#OPENSTACK_AUTH_ADMIN_PW = "admin"
IMAGE_NAME = "cirros-0.3.4-x86_64-uec"
FLAVOR_NAME = "m1.nano"
NETWORK_NAME = "vx-net0"

MONITOR_NUM_POINTS=6 #5 mins x 6 = 30 mins

class NetworkType:
    Internal = 'fixed'
    Floating = 'floating'

def create_VM(conn, vm_name, image_name, flavor_name, network_name, host_name):
    print("Creating VM:"+ vm_name+ ", in host:"+host_name)
    
    image = conn.compute.find_image(image_name)
    flavor = conn.compute.find_flavor(flavor_name)
    network = conn.network.find_network(network_name)
    #keypair = create_keypair(conn)
    
    if image is None:
        raise LookupError("Cannot find this image: "+image)
    if flavor is None:
        raise LookupError("Cannot find this flavor: "+flavor)
    if network is None:
        raise LookupError("Cannot find this network: "+network)
    
    server = conn.compute.create_server(
        name=vm_name, 
        image_id=image.id, 
        flavor_id=flavor.id,
        networks=[{"uuid": network.id}],
        availability_zone="nova:"+host_name) #, key_name=keypair.name)
    
    server = conn.compute.wait_for_server(server)
    conn.compute.migrate_server()
    
    
    print("ssh root@{ip}".format(ip=server.access_ipv4))
    return server

def connect_openstack(auth_url, auth_id, auth_pw):
    auth_args = {
        'auth_url': auth_url,
        'username': auth_id,
        'password': auth_pw,
        'project_name': 'admin',
        'user_domain_name': 'default',
        'project_domain_name': 'default',
    }
    conn = openstack_connection.Connection(**auth_args)
    
    # for testing only
    #for network in conn.network.networks():
    #    print(network)  
    return conn

def get_vm_ip(conn, vm_name, type = NetworkType.Internal):
    server = get_VM(conn, vm_name)
    if server != None:
        for addr in server.addresses.values()[0]:
            if addr['OS-EXT-IPS:type']==type:
                print addr['addr']
    return None

def get_VM(conn, vm_name):
    server = conn.compute.find_server(vm_name)
    if server != None:
        server = conn.compute.wait_for_server(server)
    return server

def test_clouds_lab():
    conn = connect_openstack(OPENSTACK_AUTH_URL,
        OPENSTACK_AUTH_ADMIN_ID, OPENSTACK_AUTH_ADMIN_PW)
    
    SERVER_NAME="Jay-Test0001"
    IMAGE_NAME = "CirrOS"
    FLAVOR_NAME = "m1.nano"
    NETWORK_NAME = "admin-private"
    
    server=create_VM(conn, SERVER_NAME, IMAGE_NAME, FLAVOR_NAME, NETWORK_NAME, "compute5")

def connect_novaclient(auth_url, auth_id, auth_pw):
    auth = v3.Password(auth_url=auth_url,
                   username=auth_id,
                   password=auth_pw,    
                   project_name='admin',
                   user_domain_id='default',
                   project_domain_id='default')
    sess = session.Session(auth=auth)
    nova = client.Client("2.1", session=sess)
    return nova
        

def live_migrate_VM(conn, nova, vm_name, desthost=None, block_migration=True, disk_over_commit=False):
    server = get_VM(conn, vm_name)
    s = nova.servers.get(server.id)
    nova.servers.live_migrate(s.id, desthost, block_migration, disk_over_commit)
    

def test_conn():
    conn = connect_openstack(OPENSTACK_AUTH_URL, OPENSTACK_AUTH_ADMIN_ID, OPENSTACK_AUTH_ADMIN_PW)
    for server in conn.compute.servers():
        print(server)
    
    for image in conn.compute.images():
        print(image)
    
    for flavor in conn.compute.flavors():
        print(flavor)
    
    for network in conn.network.networks():
        print(network)    




if __name__ == "__main__":
    conn = connect_openstack(OPENSTACK_AUTH_URL, OPENSTACK_AUTH_ADMIN_ID, OPENSTACK_AUTH_ADMIN_PW)
    test_conn()
    nova = connect_novaclient(OPENSTACK_AUTH_URL, OPENSTACK_AUTH_ADMIN_ID, OPENSTACK_AUTH_ADMIN_PW)
    live_migrate_VM(conn, nova, 'adel', 'compute3')
    