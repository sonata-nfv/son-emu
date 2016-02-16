# Distributed Cloud Emulator

Contributors:

* Manuel Peuster <manuel.peuster@upb.de>


### Requirements
* needs the latest [Dockernet](https://github.com/mpeuster/dockernet) to be installed on the system
 * the emulator is implemented against Dockernet's APIs
* The emulator uses ZeroMQ based RPC to for communication between demo CLI client and cloud-like APIs
 * `pip install zerorpc`
 * (This will be replaced / extended by a REST API later)

### Project structure
* **emuvim/** all emulator code 
 * **api/** Data center API endpoint implementations (zerorpc, OpenStack REST, ...)
 * **cli/** CLI client to interact with a running emulator
 * **dcemulator/** Dockernet wrapper that introduces the notion of data centers and API endpoints
 * **test/** Unit tests
 * **example_topology.py** An example topology script to show how topologies can be specified

### Installation
Automatic installation is provide through Ansible playbooks.
* Requires: Ubuntu 14.04 LTS
* `sudo apt-get install ansible git`
* `sudo vim /etc/ansible/hosts`
* Add: `localhost ansible_connection=local`

#### 1. Dockernet
* `cd`
* `git clone https://github.com/mpeuster/dockernet.git`
* `cd ~/dockernet/ansible`
* `sudo ansible-playbook install.yml`
* Wait (and have a coffee) ...

#### 2. Emulator
* Fork the repository.
* `cd`
* `git clone https://github.com/<user>/son-emu.git`
* `cd ~/son-emu/ansible`
* `sudo ansible-playbook install.yml`


### Run
* First terminal:
 * `cd ~/son-emu/emuvim`
 * `sudo python example_topology.py`
* Second terminal:
 * `cd ~/son-emu/emuvim/cli`
 * `./son-emu-cli compute start -d dc1 -n vnf1`
 * `./son-emu-cli compute start -d dc1 -n vnf2`
 * `./son-emu-cli compute list`
* First terminal:
 * `dockernet> vnf1 ping -c 2 vnf2`

#### Example scripts:
 * `./start_dcnetwork` starts an example datacenter network with monitoring api endpoint
 * `./start_example_chain` sets up an example service chain, using the example docker container from `package_samples` https://github.com/sonata-nfv/packaging_samples/tree/master/VNFs

### Run Unit Tests
* `cd ~/son-emu/emuvim`
* `sudo python test` or `sudo python test -v` for more outputs

### CLI
* [Full CLI command documentation](https://github.com/sonata-nfv/son-emu/wiki/CLI-Command-Overview)


### TODO
* DCemulator
 * Advanced network model
  * improve network management, multiple interfaces per container
  * API to create multiple networks (per DC?)
* SDN Controller
 * simple API to chain running VNFs
* Add resource constraints to datacenters
* Check if we can use the Mininet GUI to visualize our DCs?
* (Unit tests for zerorpc API endpoint, and any other new endpoint)


### Features / Done
* Define a topology (Python script)
 * Add data centers
 * Add switches and links between the,
* Define API endpoints in topology
 * call startAPI from topology definition and start it in a own thread
 * make it possible to start different API endpoints for different DCs
* DCemulator
 * correctly start and connect new compute resources at runtime
 * remove and disconnect compute resources at runtime
 * do IP management for new containers
 * list active compute resources
* Cloud-like reference API with CLI for demonstrations
 * Write CLI client
 * Start compute (name, DC, image, network)
 * Stop compute
* Create an Ansible-based automatic installation routine
* Unit tests

