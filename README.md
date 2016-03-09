[![Build Status](http://jenkins.sonata-nfv.eu/buildStatus/icon?job=son-emu)](http://jenkins.sonata-nfv.eu/job/son-emu)

# Distributed Cloud Emulator

## Lead Developers
The following lead developers are responsible for this repository and have admin rights. They can, for example, merge pull requests.


* Manuel Peuster (mpeuster)
* Steven Van Rossem (stevenvanrossem)


### Dependencies
* needs the latest [Dockernet](https://github.com/mpeuster/dockernet) to be installed on the system
* pyaml
* zerorpc
* tabulate
* argparse
* networkx
* six>=1.9
* ryu
* oslo.config
* pytest
* pytest-runner
* Flask
* flask_restful

### Project structure

* **src/emuvim/** all emulator code 
 * **api/** Data center API endpoint implementations (zerorpc, OpenStack REST, ...)
 * **cli/** CLI client to interact with a running emulator
 * **dcemulator/** Dockernet wrapper that introduces the notion of data centers and API endpoints
 * **examples/** Example topology scripts
 * **test/** Unit tests
* **ansible/** Ansible install scripts
* **util/** helper scripts

### Installation
Automatic installation is provide through Ansible playbooks.

* Requires: Ubuntu 14.04 LTS
* `sudo apt-get install ansible git`
* `sudo vim /etc/ansible/hosts`
* Add: `localhost ansible_connection=local`

#### 1. Dockernet
* `cd`
* `git clone -b dockernet-sonata https://github.com/mpeuster/dockernet.git`
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

In the `~/son-emu` directory:

* During development:
 * `python setup.py develop`
* Otherwise, for a classic installation:
 * `python setup.py install`
* First terminal:
 * `sudo python src/emuvim/examples/simple_topology.py 
`
* Second terminal:
 * `son-emu-cli compute start -d datacenter1 -n vnf1`
 * `son-emu-cli compute start -d datacenter1 -n vnf2`
 * `son-emu-cli compute list`
* First terminal:
 * `dockernet> vnf1 ping -c 2 vnf2`
* Second terminal:
 *  `son-emu-cli monitor get_rate -vnf vnf1`

### Run Unit Tests
* `cd ~/son-emu`
* `sudo py.test -v src/emuvim` (equivalent to `python setup.py test -v --addopts 'src/emuvim'` but with direct access to the commandline arguments)

### CLI
* [Full CLI command documentation](https://github.com/sonata-nfv/son-emu/wiki/CLI-Command-Overview)

