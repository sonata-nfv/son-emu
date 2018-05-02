<!--
# Copyright (c) 2017 SONATA-NFV and Paderborn University
# ALL RIGHTS RESERVED.
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Neither the name of the SONATA-NFV, Paderborn University
# nor the names of its contributors may be used to endorse or promote
# products derived from this software without specific prior written
# permission.
#
# This work has been performed in the framework of the SONATA project,
# funded by the European Commission under Grant number 671517 through
# the Horizon 2020 and 5G-PPP programmes. The authors would like to
# acknowledge the contributions of their colleagues of the SONATA
# partner consortium (www.sonata-nfv.eu).
-->

A complete description of the Service Function Chaining API can be found under
https://docs.openstack.org/developer/networking-sfc/api.html

### Working Example
This section describes a complete, working example of the SFC API with Sonata.
The following diagram shows the structure of the service chain that will be created.

```
+-------+      +------+     +------+     +-------+
| Host1 |      | VNF1 |     | VNF2 |     | Host2 |
+-------+      +------+     +------+     +-------+
     |p1       p2|  |p3     p4|  |p5      p6|
     |           |  |         |  |          |           PC1 = {{p1, p2}, {p3, p4}, {p5, p6}}
     +------>----+  +---->----+  +---->-----+
     |                                      |
     ^                                      v           PC2 = {{p6, p1}}
     +-------------------<------------------+
```
Two port chains, PC1 and PC2, are created. PC1 chains packets from Host1 over VNF1 and VNF2 to Host2.
Both network functions, VNF1 and VNF2, simply forward all packets from ingress to egress. PC2 creates a
direct chain from Host2 to Host1, such that replies can be routed send back.
(Note: Port chains are unidirectional)

#### Prerequisites
The following python packages required in order for the Openstack CLI commands to work.
```
sudo pip install python-openstackclient networking-sfc
```
Also the docker images `ubuntu:trusty` and `sonatanfv/sonata-snort-ids-vnf` have to be locally available
(otherwise Sonata cannot start the containers).

#### Execution
First, start the DCEmulator:
```
sudo python src/emuvim/examples/openstack_single_dc.py
```    
It creates a single data center and connects it to an instance of the Openstack API listening on `http://0.0.0.0:6001`.

Then execute the following script. It starts the containers and sets up the port chains as described above.
Finally a ping from Host1 to Host2 is executed to check the connection established by the port chains.

```
export OS_USERNAME="admin"
export OS_PASSWORD="nope"
export OS_PROJECT_NAME="nope"
export OS_AUTH_URL="http://0.0.0.0:6001"

# 1. Create ports
openstack port create --network default p1
openstack port create --network default p2
openstack port create --network default p3
openstack port create --network default p4
openstack port create --network default p5
openstack port create --network default p6

# 2. Start servers
openstack server create --image ubuntu:trusty --flavor m1.tiny --port p1 Host1
openstack server create --image sonatanfv/sonata-snort-ids-vnf --flavor m1.tiny \
  --port p2 --port p3 --property IFIN="p2-0" --property IFOUT="p3-0" VNF1
openstack server create --image sonatanfv/sonata-snort-ids-vnf --flavor m1.tiny \
  --port p4 --port p5 --property IFIN="p4-0" --property IFOUT="p5-0" VNF2
openstack server create --image ubuntu:trusty --flavor m1.tiny --port p6 Host2

# 3. Create port pairs
openstack sfc port pair create --ingress p1 --egress p2 PP1
openstack sfc port pair create --ingress p3 --egress p4 PP2
openstack sfc port pair create --ingress p5 --egress p6 PP3
openstack sfc port pair create --ingress p6 --egress p1 PP4 # for direct ping reply Host2->Host1

# 4. Create port groups
openstack sfc port pair group create --port-pair PP1 --port-pair PP2 --port-pair PP3 PPG1
openstack sfc port pair group create --port-pair PP4 PPG2

# 5. Create port chain
openstack sfc port chain create --port-pair-group PPG1 PC1
openstack sfc port chain create --port-pair-group PPG2 PC2

# 6. Test the port chain
export HOST1_DOCKER=$(openstack server list | grep "Host1" | awk '{print "mn."$4}')
export HOST2_IP=$(openstack port show p6 | grep fixed_ips \
  | awk 'match($4, "\x27,") {print substr($4, 13, RSTART - 13)}')
sudo docker exec -it ${HOST1_DOCKER} ping -c 5 ${HOST2_IP}
```

To verify that the port chains actually works, commenting out the creation of either port chain (step 5)
will result in the ping packets not getting through.

### Unimplemented Features
While all functions of the API are implemented and can be called, some of the internal functionality
remains unimplemented at the moment:
* Updating/deleting port chains (the metadata is updated, but the implemented chain is not)
* FlowClassifiers (can be called, metadata is handles but not actually implemented with the chain)
