[![Build Status](http://jenkins.sonata-nfv.eu/buildStatus/icon?job=son-emu)](http://jenkins.sonata-nfv.eu/job/son-emu)

# son-emu
This is the repository of [SONATA's](http://sonata-nfv.eu) emulation platform.

This emulation platform was created to support network  service developers to locally prototype and test complete network service chains in realistic end-to-end multi-PoP scenarios. It allows the direct execution of real network functions, packaged as Docker containers, in emulated network topologies running locally on the network service developer's machine.

### Cite this work

If you use son-emu for your research and/or other publications, please cite the following paper to reference our work:

* Manuel Peuster, Holger Karl, and Steven van Rossem. "**MeDICINE: Rapid Prototyping of Production-Ready Network Services in Multi-PoP Environments.**" to appear in IEEE Conference on Network Function Virtualization and Software Defined Network (NFV-SDN), 2016.
  * Pre-print online: http://arxiv.org/abs/1606.05995

A short demo that showcases son-emu together with its dummy gatekeeper is available [here](https://www.youtube.com/watch?v=ZANz97pV9ao).

### Development

To install the emulator package in development mode, do:

* `python setup.py develop`

#### Folder Structure

* `ansible` Install scripts
* `misc` Example packages and VNFs
* `src` 
	* `emuvim` Emulator components
		* `api` API endpoint implementations
			* `rest` REST API for son-emu-cli
    		* `sonata` Dummy gatekeeper API
		* `cli` Command line client to control the emulator
		* `dcemulator` Emulator core
			* `resourcemodel` Resource limitation models
	* `examples` Example topology scripts
	* `test` Test scripts
* `utils` Helper scripts for SONATA's CI/CD setup


#### Run Unit Tests
* `cd ~/son-emu`
* `sudo py.test -v src/emuvim/test/unittests`


### Building

Son-emu is entirely written in Python and does not require a special build process. Please check the [Installation](https://github.com/sonata-nfv/son-emu#installation) section for more details about the installation of son-emu.

### Dependencies

Son-emu requires the latest version of [Containernet](https://github.com/mpeuster/containernet) to be installed on the system.

Despite of this son-emu has the following dependencies:

* [argparse](https://pypi.python.org/pypi/argparse) >= 1.4.0 (Python software foundation License)
* [docker-py](https://pypi.python.org/pypi/docker-py) == 1.7.1(Apache 2.0)
* [Flask](https://pypi.python.org/pypi/Flask) >= 0.11 (BSD)
* [flask_restful](https://pypi.python.org/pypi/Flask-RESTful) >= 0.3 (BSD)
* [networkx](https://pypi.python.org/pypi/networkx/) >= 1.11  (BSD)
* [oslo.config](http://docs.openstack.org/developer/oslo.config/) >= 3.9.0  (Apache 2.0)
* [prometheus_client](https://pypi.python.org/pypi/prometheus_client) >= 0.0.13 (Apache 2.0)
* [pyaml](https://pypi.python.org/pypi/pyaml) >=15.8.2 (WTFPL)
* [pytest-runner](https://pypi.python.org/pypi/pytest-runner) >= 2.8 (MIT)
* [pytest](https://pypi.python.org/pypi/pytest) >= 2.9 (MIT)
* [requests](https://pypi.python.org/pypi/requests) >= 2.10 (Apache 2.0)
* [ryu](https://pypi.python.org/pypi/ryu/4.4) >= 4.4 (Apache 2.0)
* [six](https://pypi.python.org/pypi/six/) >=1.9 (MIT)
* [tabulate](https://pypi.python.org/pypi/tabulate) >= 0.7.5 (public domain)
* [urllib3](https://pypi.python.org/pypi/urllib3) >= 1.15 (MIT)
* [zerorpc](http://www.zerorpc.io) >= 0.5.2 (MIT)

### Contributing
Contributing to the son-emu is really easy. You must:

1. Clone [this repository](http://github.com/sonata-nfv/son-emu);
2. Work on your proposed changes, preferably through submiting [issues](https://github.com/sonata-nfv/son-emu/issues);
3. Submit a Pull Request;
4. Follow/answer related [issues](https://github.com/sonata-nfv/son-emu/issues) (see Feedback-Chanel, below).

## Installation
There are two ways to install and use son-emu. The simple one is to use Vagrant to create a VirtualBox-based VM on you machine that contains the pre-installed and configured emulator. The more complicated installation requires a freshly installed Ubuntu 14.04 LTS and is done by a ansible playbook.

### Vagrant Installation

* Request VirtualBox and Vagrant to be installed on the system.
* `git clone https://github.com/sonata-nfv/son-emu.git`
* `cd ~/son-emu`
* `vagrant up`
* `vagrant ssh` to enter the new VM in which the emulator is installed.

Follow the MOTD in the VM to run the example topology and the dummy-gatekeeper. The dummy-gatekeeper's default port 5000 is forwarded to the host machine and can be accessed from it by using, e.g., curl http://127.0.0.1:5000/packages.

### Ansible Installation

* Requires: Ubuntu 14.04 LTS
* `sudo apt-get install ansible git aptitude`
* `sudo vim /etc/ansible/hosts`
* Add: `localhost ansible_connection=local`

#### 1. Containernet

* `cd`
* `git clone https://github.com/mpeuster/containernet.git`
* `cd ~/containernet/ansible`
* `sudo ansible-playbook install.yml`
* Wait (and have a coffee) ...

#### 2. Emulator

* `cd`
* `git clone https://github.com/sonata-nfv/son-emu.git`
* `cd ~/son-emu/ansible`
* `sudo ansible-playbook install.yml`

## Usage

### Examples
#### Manual Usage Example:

This simple example shows how to start the emulator with a simple topology (terminal 1) and how to start (terminal 2) some empty VNF containers in the emulated datacenters (PoPs) by using the son-emu-cli.

* First terminal (start the emulation platform):
 * `sudo python src/emuvim/examples/simple_topology.py`
* Second terminal:
 * `son-emu-cli compute start -d datacenter1 -n vnf1`
 * `son-emu-cli compute start -d datacenter1 -n vnf2`
 * `son-emu-cli compute list`
* First terminal:
 * `containernet> vnf1 ifconfig`
 * `containernet> vnf1 ping -c 2 vnf2`

#### Dummy Gatekeeper Example:

This example shows how to deploy a SONATA example package in the emulator using the dummy gatekeeper.

* First terminal (start the emulation platform):
 * `sudo python src/emuvim/examples/sonata_y1_demo_topology_1.py`
* Second terminal (deploy the example package):
 * Upload: `curl -i -X POST -F package=@sonata-demo-docker.son http://127.0.0.1:5000/packages`
 * Instantiate: `curl -X POST http://127.0.0.1:5000/instantiations -d "{}"`
 * Verify that service runs: `son-emu-cli compute list`

Note: The [son-push](https://github.com/mpeuster/son-cli) tool can be used instead of CURL.


### Further Documentation
* [Full CLI command documentation](https://github.com/sonata-nfv/son-emu/wiki/CLI-Command-Overview)
* [Requirements for Docker containers executed by the emulator](https://github.com/sonata-nfv/son-emu/wiki/Container-Requirements)

## License

Son-emu is published under Apache 2.0 license. Please see the LICENSE file for more details.

## Useful Links

* [Mininet](http://mininet.org)

---
#### Lead Developers

The following lead developers are responsible for this repository and have admin rights. They can, for example, merge pull requests.

* Manuel Peuster (https://github.com/mpeuster)
* Steven Van Rossem (https://github.com/stevenvanrossem)

#### Contributors

* Hadi Razzaghi Kouchaksaraei (https://github.com/hadik3r)
* Wouter Tavernier (https://github.com/wtaverni)
* Geoffroy Chollon (https://github.com/cgeoffroy)

#### Feedback-Chanel

* You may use the mailing list [sonata-dev@lists.atosresearch.eu](mailto:sonata-dev@lists.atosresearch.eu)
* [GitHub issues](https://github.com/sonata-nfv/son-emu/issues)
