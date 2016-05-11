[![Build Status](http://jenkins.sonata-nfv.eu/buildStatus/icon?job=son-emu)](http://jenkins.sonata-nfv.eu/job/son-emu)

# Distributed Cloud Emulator

### Lead Developers
The following lead developers are responsible for this repository and have admin rights. They can, for example, merge pull requests.

* Manuel Peuster (mpeuster)
* Steven Van Rossem (stevenvanrossem)

### Environment
* Python 2.7
* Latest [Containernet](https://github.com/mpeuster/containernet) installed on the system

### Dependencies
* pyaml (public domain)
* zerorpc (MIT)
* tabulate (public domain)
* argparse (Python software foundation license)
* networkx (BSD)
* six>=1.9 (MIT)
* ryu (Apache 2.0)
* oslo.config (Apache 2.0)
* pytest (MIT)
* pytest-runner (MIT)
* Flask (BSD)
* flask_restful (BSD)
* requests  (Apache 2.0)
* docker-py (Apache 2.0)
* paramiko (LGPL)

### 3rd-party code used
* (none)


### Project structure

* **src/emuvim/** all emulator code 
 * **api/** Data center API endpoint implementations (zerorpc, OpenStack REST, ...)
 * **cli/** CLI client to interact with a running emulator
 * **dcemulator/** Containernet wrapper that introduces the notion of data centers and API endpoints
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

#### 1. Containernet
* `cd`
* `git clone https://github.com/mpeuster/containernet.git`
* `cd ~/containernet/ansible`
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
 * `containernet> vnf1 ping -c 2 vnf2`
* Second terminal:
 *  `son-emu-cli monitor get_rate -vnf vnf1`

### Run Unit Tests
* `cd ~/son-emu`
* `sudo py.test -v src/emuvim` (equivalent to `python setup.py test -v --addopts 'src/emuvim'` but with direct access to the commandline arguments)

### CLI
* [Full CLI command documentation](https://github.com/sonata-nfv/son-emu/wiki/CLI-Command-Overview)

