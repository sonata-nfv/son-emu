# emulator-strawman

(c) 2015 by Manuel Peuster


## emu-vim

### Requirements
* needs the latest Dockernet to be installed in the system
 * the wrapper uses standard Python imports to use the Dockernet modules
* Uses ZeroMQ based RPC to open a cloud-like interface that can be used by a demo CLI client
 * pip install import zerorpc
 * This will be replaced / extended by a REST API later

### Project structure
* **emuvim/** all emulator code 
 * **api/** Data center API endpoint implementations (zerorpc, OpenStack REST, ...)
 * **cli/** CLI client to interact with a running emulator
 * **dcemulator/** Dockernet wrapper that introduces the notion of data centers and API endpoints
 * **test/** Unit tests
 * **example_topology.py** An example topology script to show how topologies can be specified

### Installation
Automatic installation is provide through an Ansible playbook.
* Requires: Ubuntu 14.04 LTS
* `sudo apt-get install ansible git`
* `sudo vim /etc/ansible/hosts`
* Add: `localhost ansible_connection=local`

#### 1. Dockernet
* `git clone https://github.com/mpeuster/dockernet.git`
* `cd dockernet/ansible`
* `sudo ansible-playbook install.yml`
* Wait (and have a coffee) ...

#### 2. Emulator
* `cd`
* `git clone https://github.com/mpeuster/emulator-strawman.git`
* `cd emulator-strawman/ansible`
* `sudo ansible-playbook install.yml`


### Run
* First terminal:
 * `sudo python example_topology.py`
* Second terminal:
 * TODO add CLI commands here (e.g. request the start of a new compute resource)


### TODO
* DCemulator
 * ...
* Write unit tests
* Create an Ansible-based automatic installation routine
* Add resource constraints to datacenters
* Check if we can use the Mininet GUI to visualize our DCs?


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
 * Start compute
 * Stop compute
