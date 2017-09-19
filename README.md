# News: `son-emu` was adopted by OSM as `vim-emu`

We are happy to announce that SONATA's emulation platform was adopted by ETSI's [OSM project](https://osm.etsi.org) as part of their DevOps MDG under its new name `vim-emu` (Sep. 2017). The developments of the core emulator components will now take place in the [new project repository](https://osm.etsi.org/gitweb/?p=osm/vim-emu.git) hosted by OSM. This GitHub repository will act as a mirror until the [SONATA project](http://sonata-nfv.eu) has ended.

* Official OSM repository: https://osm.etsi.org/gitweb/?p=osm/vim-emu.git
* GitHub mirror of the OSM repository: https://github.com/sonata-nfv/son-emu/tree/osm/master (not always up to date)
* Old SONATA repository: https://github.com/sonata-nfv/son-emu (used for SONATA-specific developments)

**As an external user or contributer, you should always use the [official OSM repository](https://osm.etsi.org/gitweb/?p=osm/vim-emu.git).**

---

[![Join the chat at https://gitter.im/containernet/Lobby](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/containernet/Lobby?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge) [![Build Status](http://jenkins.sonata-nfv.eu/buildStatus/icon?job=son-emu-pipeline)](http://jenkins.sonata-nfv.eu/job/son-emu-pipeline)

# son-emu
This is the repository of [SONATA's](http://sonata-nfv.eu) NFV multi-PoP emulation platform.

This emulation platform was created to support network service developers to locally prototype and test complete network service chains in realistic end-to-end multi-PoP scenarios. It allows the execution of real network functions, packaged as Docker containers, in emulated network topologies running locally on the network service developer's machine.

The emulation platform is based on [Containernet](https://containernet.github.io).

### Cite this work

If you use the emulation platform for your research and/or other publications, please cite the following paper to reference our work:

* M. Peuster, H. Karl, and S. v. Rossem: [MeDICINE: Rapid Prototyping of Production-Ready Network Services in Multi-PoP Environments](http://ieeexplore.ieee.org/document/7919490/). IEEE Conference on Network Function Virtualization and Software Defined Networks (NFV-SDN), Palo Alto, CA, USA, pp. 148-153. doi: 10.1109/NFV-SDN.2016.7919490. (2016)


#### Folder Structure

* `ansible` Install scripts
* `misc` Example packages and VNFs
* `src` 
    * `emuvim` Emulator components
        * `api` API endpoint implementations
            * `rest` REST API for son-emu-cli
            * `sonata` SONATA dummy gatekeeper API
            * `openstack` OpenStack-like APIs for MANO integration
        * `cli` Command line client to control the emulator
        * `dashboard` A web-based dashboard to display the emulator's state
        * `dcemulator` Emulator core
            * `resourcemodel` Resource limitation models
        * `examples` Example topology scripts
        * `test` Test scripts
* `utils` Helper scripts for CI/CD setup


#### Run Unit Tests
* `cd ~/son-emu`
* `sudo py.test -v src/emuvim/test/unittests`
(To force using Python2: `python2 -m  pytest -v src/emuvim/test/unittests`)


### Building

The emulation platform is entirely written in Python and does not require a special build process. Please check the [Installation](https://github.com/sonata-nfv/son-emu#installation) section for more details about the installation of the emulator.

### Dependencies

The emulation platform requires the latest version of [Containernet](https://containernet.github.io) to be installed on the system.

Despite of this, the emulation platform has the following dependencies:

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

### Contributing
Contributing to the the emulator is really easy. You must:

1. Clone [this repository](http://github.com/sonata-nfv/son-emu);
2. Work on your proposed changes, preferably through submitting [issues](https://github.com/sonata-nfv/son-emu/issues);
3. Submit a Pull Request;
4. Follow/answer related [issues](https://github.com/sonata-nfv/son-emu/issues) (see Feedback-Chanel, below).

## Installation
There are three ways to install and use the emulation platform. The simple one is to use Vagrant to create a VirtualBox-based VM on your machine that contains the pre-installed and configured emulator. The more complicated installation requires a freshly installed Ubuntu 16.04 LTS and is done by an ansible playbook. The third option is to use a nested Docker environment to run the emulator inside a Docker container.

### Option 1: Vagrant Installation

* Request VirtualBox and Vagrant to be installed on the system.
* `git clone https://github.com/sonata-nfv/son-emu.git`
* `cd ~/son-emu`
* `vagrant up`
* `vagrant ssh` to enter the new VM in which the emulator is installed.

Follow the MOTD in the VM to run the example topology and the dummy-gatekeeper. The dummy-gatekeeper's default port 5000 is forwarded to the host machine and can be accessed from it by using, e.g., curl http://127.0.0.1:5000/packages.

### Option 2: Ansible Installation

* Requires: Ubuntu 16.04 LTS
* `sudo apt-get install ansible git aptitude`

#### 1. Containernet

* `cd`
* `git clone https://github.com/containernet/containernet.git`
* `cd ~/containernet/ansible`
* `sudo ansible-playbook -i "localhost," -c local install.yml`

#### 2. Emulator

* `cd`
* `git clone https://github.com/sonata-nfv/son-emu.git`
* `cd ~/son-emu/ansible`
* `sudo ansible-playbook -i "localhost," -c local install.yml`

### Option 3: Nested Docker Deployment
This option requires a Docker installation on the host machine on which the emulator should be deployed.

* **Option a)** Build container manually:
    * `git clone https://github.com/sonata-nfv/son-emu.git`
    * `cd ~/son-emu`
    * Build the container: `docker build -t son-emu-img .`
    * Run the (interactive) container: `docker run --name son-emu -it --rm --privileged --pid='host' -v /var/run/docker.sock:/var/run/docker.sock son-emu-img /bin/bash`
* **Option b)** Use latest pre-build container from [DockerHub](https://hub.docker.com/r/sonatanfv/son-emu/):
    * Pull the container: `docker pull sonatanfv/son-emu:dev`
    * Run the (interactive) container: `docker run --name son-emu -it --rm --privileged --pid='host' -v /var/run/docker.sock:/var/run/docker.sock sonatanfv/son-emu:dev /bin/bash`


## Usage

### Examples

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


### Further Documentation
* [Full CLI command documentation](https://github.com/sonata-nfv/son-emu/wiki/CLI-Command-Overview)
* [Requirements for Docker containers executed by the emulator](https://github.com/sonata-nfv/son-emu/wiki/Container-Requirements)
* [REST API](https://github.com/sonata-nfv/son-emu/wiki/APIs)

## License

The emulation platform is published under Apache 2.0 license. Please see the LICENSE file for more details.

## Useful Links

* [Mininet](http://mininet.org)
* [Containernet](https://containernet.github.io)
* [Maxinet](https://maxinet.github.io)

---
#### Lead Developers

The following lead developers are responsible for this repository and have admin rights. They can, for example, merge pull requests.

* Manuel Peuster (https://github.com/mpeuster)
* Steven Van Rossem (https://github.com/stevenvanrossem)

#### Contributors

* Hadi Razzaghi Kouchaksaraei (https://github.com/hadik3r)
* Wouter Tavernier (https://github.com/wtaverni)
* Geoffroy Chollon (https://github.com/cgeoffroy)
* Eduard Maas (https://github.com/edmaas)

#### Feedback-Chanel

* You may use the mailing list [sonata-dev@lists.atosresearch.eu](mailto:sonata-dev@lists.atosresearch.eu)
* [GitHub issues](https://github.com/sonata-nfv/son-emu/issues)
