<!--
# Copyright (c) 2017 SONATA-NFV and Paderborn University
# ALL RIGHTS RESERVED.
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Neither the name of the SONATA-NFV, Paderborn University
# nor the names of its contributors may be used to endorse or promote
# products derived from this software without specific prior written
# permission.
#
# This work has been performed in the framework of the SONATA project,
# funded by the European Commission under Grant number 671517 through
# the Horizon 2020 and 5G-PPP programmes. The authors would like to
# acknowledge the contributions of their colleagues of the SONATA
# partner consortium (www.sonata-nfv.eu).
-->

# vim-emu: A NFV multi-PoP emulation platform

This emulation platform was created to support network service developers to locally prototype and test their network services in realistic end-to-end multi-PoP scenarios. It allows the execution of real network functions, packaged as Docker containers, in emulated network topologies running locally on the developer's machine. The emulation platform also offers OpenStack-like APIs for each emulated PoP so that it can integrate with MANO solutions, like OSM. The core of the emulation platform is based on [Containernet](https://containernet.github.io).

The emulation platform `vim-emu` is developed as part of OSM's DevOps MDG.

### Acknowledgments

This software was originally developed by the [SONATA project](http://www.sonata-nfv.eu), funded by the European Commission under grant number 671517 through the Horizon 2020 and 5G-PPP programs.

### Cite this work

If you use the emulation platform for your research and/or other publications, please cite the following paper to reference our work:

* M. Peuster, H. Karl, and S. v. Rossem: [MeDICINE: Rapid Prototyping of Production-Ready Network Services in Multi-PoP Environments](http://ieeexplore.ieee.org/document/7919490/). IEEE Conference on Network Function Virtualization and Software Defined Networks (NFV-SDN), Palo Alto, CA, USA, pp. 148-153. doi: 10.1109/NFV-SDN.2016.7919490. (2016)

## Installation

There are multiple ways to install and use the emulation platform. The easiest way is the automated installation using the OSM installer. The bare-metal installation requires a freshly installed Ubuntu 16.04 LTS and is done by an ansible playbook. Another option is to use a nested Docker environment to run the emulator inside a Docker container.

### Automated installation (recommended)

```sh
./install_osm.sh --lxdimages --vimemu
```

This command will install OSM (as LXC containers) as well as the emulator (as a Docker container) on a local machine. It is recommended to use a machine with Ubuntu 16.04.

### Manual installation

#### Option 1: Bare-metal installation

```sh
sudo apt-get install ansible git aptitude
```

##### Step 1. Containernet installation

```sh
cd
git clone https://github.com/containernet/containernet.git
cd ~/containernet/ansible
sudo ansible-playbook -i "localhost," -c local install.yml
```

##### Step 2. vim-emu installation

```sh
cd
git clone https://osm.etsi.org/gerrit/osm/vim-emu.git
cd ~/vim-emu/ansible
sudo ansible-playbook -i "localhost," -c local install.yml
```

#### Option 2: Nested Docker Deployment
This option requires a Docker installation on the host machine on which the emulator should be deployed.

```sh
git clone https://osm.etsi.org/gerrit/osm/vim-emu.git</code>
cd ~/vim-emu</code>
# build the container:
docker build -t vim-emu-img .
# run the (interactive) container:
docker run --name vim-emu -it --rm --privileged --pid='host' -v /var/run/docker.sock:/var/run/docker.sock vim-emu-img /bin/bash
```


## Usage

### Example

This simple example shows how to start the emulator with a simple topology (terminal 1) and how to start (terminal 2) some empty VNF containers in the emulated datacenters (PoPs) by using the vim-emu CLI.

* First terminal (start the emulation platform):
    * `sudo python examples/default_single_dc_topology.py`
* Second terminal (use `docker exec vim-emu <command>` for nested Docker deployment):
    * `vim-emu compute start -d dc1 -n vnf1`
    * `vim-emu compute start -d dc1 -n vnf2`
    * `vim-emu compute list`
* First terminal:
    * `containernet> vnf1 ifconfig`
    * `containernet> vnf1 ping -c 2 vnf2`

A more advanced example that includes OSM can be found in the [official vim-emu documentation in the OSM wiki](https://osm.etsi.org/wikipub/index.php/VIM_emulator).

### Further documentation and useful links

* [Official vim-emu documentation in the OSM wiki](https://osm.etsi.org/wikipub/index.php/VIM_emulator)
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

* `cd ~/vim-emu`
* `sudo pytest -v`
* (To force Python2: `sudo python2 -m  pytest -v`)

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

