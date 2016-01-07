# emulator-strawman

(c) 2015 by Manuel Peuster


## emu-vim

### Requirements
* needs the latest Dockernet to be installed in the system
 * the wrapper uses standard Python imports to use the Dockernet modules
* Uses ZeroMQ based RPC to open a cloud-like interface that can be used by a demo CLI client
 * pip install import zerorpc
 * This will be replaced / extended by a REST API later

### TODO
* DCemulator
 * correctly start and connect new compute resources at runtime
 * remove and disconnect compute resources at runtime
 * list active compute resources
* Cloud-like reference API with CLI for demonstrations
 * Write CLI client
 * Start compute
 * Stop compute
* Re-factor endpoint API so that API objects can be more or less statless (ask DCEmulator for available DCs instead of maintaining a own list)
* Create an Ansible-based automatic installation routine
* Add resource constraints to datacenters
* Check if we can use the Mininet GUI to visualize our DCs?


### Features
* Define a topology (Python script)
 * Add data centers
 * Add switches and links between the,
* Define API endpoints in topology
 * call startAPI from topology definition and start it in a own thread
 * make it possible to start different API endpoints for different DCs
