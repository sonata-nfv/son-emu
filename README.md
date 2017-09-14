# vim-emu: A NFV multi-PoP emulation platform

This emulation platform was created to support network service developers to locally prototype and test their network services in realistic end-to-end multi-PoP scenarios. It allows the execution of real network functions, packaged as Docker containers, in emulated network topologies running locally on the developer's machine. The emulation platform also offers OpenStack-like APIs for each emulated PoP so that it can integrate with MANO solutions, like OSM. The core of the emulation platform is based on [Containernet](https://containernet.github.io).

The emulation platform `vim-emu` is developed as part of OSM's DevOps MDG.

### Acknowledgments

This software was originally developed by the [SONATA project](http://www.sonata-nfv.eu), funded by the European Commission under grant number 671517 through the Horizon 2020 and 5G-PPP programs.

### Cite this work

If you use the emulation platform for your research and/or other publications, please cite the following paper to reference our work:

* M. Peuster, H. Karl, and S. v. Rossem: [MeDICINE: Rapid Prototyping of Production-Ready Network Services in Multi-PoP Environments](http://ieeexplore.ieee.org/document/7919490/). IEEE Conference on Network Function Virtualization and Software Defined Networks (NFV-SDN), Palo Alto, CA, USA, pp. 148-153. doi: 10.1109/NFV-SDN.2016.7919490. (2016)

## Installation

There are three ways to install and use the emulation platform. The bare-metal installation requires a freshly installed Ubuntu 16.04 LTS and is done by an ansible playbook. The second option is to use a nested Docker environment to run the emulator inside a Docker container. The third option is to use Vagrant to create a VirtualBox-based VM on your machine that contains the pre-installed and configured emulator.

### Option 1: Bare-metal installation

* Requires: Ubuntu 16.04 LTS
* `sudo apt-get install ansible git aptitude`

#### 1. Containernet

* `cd`
* `git clone https://github.com/containernet/containernet.git`
* `cd ~/containernet/ansible`
* `sudo ansible-playbook -i "localhost," -c local install.yml`

#### 2. vim-emu

* `cd`
* `git clone https://github.com/sonata-nfv/son-emu.git`
* `cd ~/son-emu/ansible`
* `sudo ansible-playbook -i "localhost," -c local install.yml`

### Option 3: Nested Docker Deployment
This option requires a Docker installation on the host machine on which the emulator should be deployed.

* `git clone https://github.com/sonata-nfv/son-emu.git`
* `cd ~/son-emu`
* Build the container: `docker build -t son-emu-img .`
* Run the (interactive) container: `docker run --name son-emu -it --rm --privileged --pid='host' -v /var/run/docker.sock:/var/run/docker.sock son-emu-img /bin/bash`

### Option 3: Vagrant Installation
* Request VirtualBox and Vagrant to be installed on the system.
* `git clone https://github.com/sonata-nfv/son-emu.git`
* `cd ~/son-emu`
* `vagrant up`
* `vagrant ssh` to enter the new VM in which the emulator is installed.

## Usage

### Example

This simple example shows how to start the emulator with a simple topology (terminal 1) and how to start (terminal 2) some empty VNF containers in the emulated datacenters (PoPs) by using the son-emu-cli.

* First terminal (start the emulation platform):
 * `sudo python examples/simple_topology.py`
* Second terminal:
 * `son-emu-cli compute start -d datacenter1 -n vnf1`
 * `son-emu-cli compute start -d datacenter1 -n vnf2`
 * `son-emu-cli compute list`
* First terminal:
 * `containernet> vnf1 ifconfig`
 * `containernet> vnf1 ping -c 2 vnf2`

### Further documentation and useful links

* [Full CLI command documentation](https://github.com/sonata-nfv/son-emu/wiki/CLI-Command-Overview)
* [Requirements for Docker containers executed by the emulator](https://github.com/sonata-nfv/son-emu/wiki/Container-Requirements)
* [REST API](https://github.com/sonata-nfv/son-emu/wiki/APIs)
* [Mininet](http://mininet.org)
* [Containernet](https://containernet.github.io)
* [Maxinet](https://maxinet.github.io)

## Development

### How to contribute?

Please check [this OSM wiki page](https://osm.etsi.org/wikipub/index.php/Workflow_with_OSM_tools) to learn how to contribute to a OSM module.

### Testing

To run the unit tests do:

* `cd ~/son-emu`
* `sudo py.test -v src/emuvim/test/unittests`
(To force Python2: `python2 -m  pytest -v src/emuvim/test/unittests`)

## Seed code contributors:

### Lead:

* Manuel Peuster (https://github.com/mpeuster)
* Steven Van Rossem (https://github.com/stevenvanrossem)

### Contributors

* Hadi Razzaghi Kouchaksaraei (https://github.com/hadik3r)
* Wouter Tavernier (https://github.com/wtaverni)
* Geoffroy Chollon (https://github.com/cgeoffroy)
* Eduard Maas (https://github.com/edmaas)
* Malte Splietker (https://github.com/splietker)
* Johannes Kampmeyer (https://github.com/xschlef)

## License

The emulation platform is published under Apache 2.0 license. Please see the LICENSE file for more details.

## Contact

Manuel Peuster (Paderborn University) <manuel@peuster.de>

