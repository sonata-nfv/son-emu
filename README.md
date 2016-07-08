[![Build Status](http://jenkins.sonata-nfv.eu/buildStatus/icon?job=son-emu)](http://jenkins.sonata-nfv.eu/job/son-emu)

# son-emu
This is the repository of [SONATA's](http://sonata-nfv.eu) emulation platform.

This emulation platform was created to support network  service developers to locally prototype and test complete network service chains in realistic end-to-end multi-PoP scenarios. It allows the direct execution of real network functions, packaged as Docker containers, in emulated network topologies running locally on the network service developer's machine.

More details about the the emulator's architecture and concepts can be found in the following publication(s):

* Peuster, Manuel, Holger Karl, and Steven van Rossem. ["MeDICINE: Rapid Prototyping of Production-Ready Network Services in Multi-PoP Environments."](http://arxiv.org/abs/1606.05995) pre-print arXiv:1606.05995 (2016).

## Development
(if applicable)

### Building
Describe briefly how to build the software.

### Dependencies

* [argparse](https://pypi.python.org/pypi/argparse) >= 1.4.0 (Python software foundation License)
* [docker-py](https://pypi.python.org/pypi/docker-py) == 1.7.1(Apache 2.0)
* [Flask](https://pypi.python.org/pypi/Flask) >= 0.11 (BSD)
* [flask_restful](https://pypi.python.org/pypi/Flask-RESTful) >= 0.3 (BSD)
* [networkx](https://pypi.python.org/pypi/networkx/) >= 1.11  (BSD)
* [oslo.config](http://docs.openstack.org/developer/oslo.config/) >= 3.9.0  (Apache 2.0)
* [paramiko](https://pypi.python.org/pypi/paramiko/1.16.0) >= 1.6 (LGPL)
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
Contributing to the Gatekeeper is really easy. You must:

1. Clone [this repository](http://github.com/sonata-nfv/son-emu);
2. Work on your proposed changes, preferably through submiting [issues](https://github.com/sonata-nfv/son-emu/issues);
3. Submit a Pull Request;
4. Follow/answer related [issues](https://github.com/sonata-nfv/son-emu/issues) (see Feedback-Chanel, below).

## Installation
There are two ways to install and use son-emu. The simple one is to use Vagrant to create a VirtualBox-based VM on you machine that contains the pre-installed and configured emulator. The more complicated installation requires a freshly installed Ubuntu 14.04 LTS or 16.04 LTS and is done by a ansible playbook.

### Vagrant Installation

* Request VirtualBox and Vagrant to be installed on the system.
* `git clone https://github.com/sonata-nfv/son-emu.git`
* `cd ~/son-emu`
* `vagrant up`
* `vagrant ssh` to enter the new VM in which the emulator is installed.

Follow the MOTD in the VM to run the example topology and the dummy-gatekeeper. The dummy-gatekeeper's default port 5000 is forwarded to the host machine and can be accessed from it by using, e.g., curl http://127.0.0.1:5000/packages.

### Ansible Installation

* Requires: Ubuntu 14.04 LTS or 16.04 LTS
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
* `cd`
* `git clone https://github.com/sonata-nfv/son-emu.git`
* `cd ~/son-emu/ansible`
* `sudo ansible-playbook install.yml`

## Usage
(if applicable) Describe briefly how to use the software.

### CLI
* [Full CLI command documentation](https://github.com/sonata-nfv/son-emu/wiki/CLI-Command-Overview)

## License

Son-emu is published under Apache 2.0 license. Please see the LICENSE file for more details.

## Useful Links

* Any useful link and brief description. For example:
* http://www.google/ Don't be evil.

---
#### Lead Developers

The following lead developers are responsible for this repository and have admin rights. They can, for example, merge pull requests.

* Manuel Peuster (https://github.com/mpeuster)
* Steven Van Rossem (https://github.com/stevenvanrossem)

#### Feedback-Chanel

* You may use the mailing list [sonata-dev@lists.atosresearch.eu](mailto:sonata-dev@lists.atosresearch.eu)
* * [GitHub issues](https://github.com/sonata-nfv/son-emu/issues)
