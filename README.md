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

* Add runtime API
 * call startAPI from topology definition and start it in a own thread?
 * make it possible to start different API endpoints for different DCs?
* Add resource constraints to datacenters
* Add constraints to Links
* Check if we can use the Mininet GUI to visualize our DCs?