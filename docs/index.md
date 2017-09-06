---
layout: default
---


# [](#overview)Overview

Containernet is a fork of the famous [Mininet](http://mininet.org) network emulator and allows to use [Docker](https://www.docker.com) containers as hosts in the emulated network topologies. This enables interesting functionalities to build networking/cloud emulators and testbeds. One example for this is the [NFV multi-PoP infrastructure emulator](https://github.com/sonata-nfv/son-emu) created by the [SONATA](http://sonata-nfv.eu) project.

## Containernet in action

<script type="text/javascript" src="https://asciinema.org/a/4eSesgrJL8t2VikiDnHoD9qRF.js" id="asciicast-4eSesgrJL8t2VikiDnHoD9qRF" async data-autoplay="true" data-size="medium" data-loop="true" data-rows="12"></script>

## Cite this work

If you use [Containernet](containernet.github.io) for your work, please cite the following publication:

* M. Peuster, H. Karl, and S. v. Rossem: [MeDICINE: Rapid Prototyping of Production-Ready Network Services in Multi-PoP Environments](http://ieeexplore.ieee.org/document/7919490/). IEEE Conference on Network Function Virtualization and Software Defined Networks (NFV-SDN), Palo Alto, CA, USA, pp. 148-153. doi: 10.1109/NFV-SDN.2016.7919490. (2016)


# [](#get-started)Get started

Using Containernet is very similar to using Mininet with [custom topologies](http://mininet.org/walkthrough/#custom-topologies).

## Create a custom topology

First, a Python-based topology has to be created as shown in the following example.

```python
"""
Example topology with two containers (d1, d2),
two switches, and one controller:

          - (c)-
         |      |
(d1) - (s1) - (s2) - (d2)
"""
from mininet.net import Containernet
from mininet.node import Controller
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import info, setLogLevel
setLogLevel('info')

net = Containernet(controller=Controller)
info('*** Adding controller\n')
net.addController('c0')
info('*** Adding docker containers using ubuntu:trusty images\n')
d1 = net.addDocker('d1', ip='10.0.0.251', dimage="ubuntu:trusty")
d2 = net.addDocker('d2', ip='10.0.0.252', dimage="ubuntu:trusty")
info('*** Adding switches\n')
s1 = net.addSwitch('s1')
s2 = net.addSwitch('s2')
info('*** Creating links\n')
net.addLink(d1, s1)
net.addLink(s1, s2, cls=TCLink, delay='100ms', bw=1)
net.addLink(s2, d2)
info('*** Starting network\n')
net.start()
info('*** Testing connectivity\n')
net.ping([d1, d2])
info('*** Running CLI\n')
CLI(net)
info('*** Stopping network')
net.stop()
```

You can find this topology in [`containernet/examples/containernet_example.py`](https://github.com/containernet/containernet/tree/master/examples/containernet_example.py).

## Run emulation and interact with containers

Containernet requires root access to configure the emulated network described by the topology script:

```bash
sudo python containernet_example.py
```

After launching the emulated network, you can interact with the involved containers through Mininet's interactive CLI as shown with the `ping` command in the following example:

```bash
containernet> d1 ping -c3 d2
PING 10.0.0.252 (10.0.0.252) 56(84) bytes of data.
64 bytes from 10.0.0.252: icmp_seq=1 ttl=64 time=200 ms
64 bytes from 10.0.0.252: icmp_seq=2 ttl=64 time=200 ms
64 bytes from 10.0.0.252: icmp_seq=3 ttl=64 time=200 ms

--- 10.0.0.252 ping statistics ---
3 packets transmitted, 3 received, 0% packet loss, time 2002ms
rtt min/avg/max/mdev = 200.162/200.316/200.621/0.424 ms
containernet>
```

To stop the emulation, do:

```
containernet> exit
```

# [](#installation)Installation

Automatic installation is provided using an Ansible playbook. Requires a bare-metal machine or VM with Ubuntu **16.04 LTS**.

```bash
sudo apt-get install ansible git aptitude
git clone https://github.com/containernet/containernet.git
cd containernet/ansible
sudo ansible-playbook -i "localhost," -c local install.yml
```

# [](#references)References

Containernet has been used for a variety of research tasks and networking projects. If you use Containernet, let us [know](mailto:containernet@peuster.de).

## Publications

* S. v. Rossem, W. Tavernier, M. Peuster, D. Colle, M. Pickavet and P. Demeester: [Monitoring and debugging using an SDK for NFV-powered telecom applications](https://biblio.ugent.be/publication/8521281/file/8521284.pdf). IEEE Conference on Network Function Virtualization and Software Defined Networks (NFV-SDN), Palo Alto, CA, USA, Demo Session. (2016)

* M. Peuster, H. Karl: [Understand Your Chains: Towards Performance Profile-based Network Service Management.](http://ieeexplore.ieee.org/document/7956044/) Accepted in Fifth European Workshop on Software Defined Networks (EWSDN). IEEE. (2016)

* Qiao, Yuansong, et al. [Doopnet: An emulator for network performance analysis of Hadoop clusters using Docker and Mininet.](http://ieeexplore.ieee.org/document/7543832/) Computers and Communication (ISCC), 2016 IEEE Symposium on. IEEE, 2016.

* M. Peuster, S. Dräxler, H. Razzaghi, S. v. Rossem, W. Tavernier and H. Karl: [A Flexible Multi-PoP Infrastructure Emulator for Carrier-grade MANO Systems](https://cs.uni-paderborn.de/fileadmin/informatik/fg/cn/Publications_Conference_Paper/Publications_Conference_Paper_2017/peuster_netsoft_demo_paper_2017.pdf). In IEEE 3rd Conference on Network Softwarization (NetSoft) Demo Track . (2017) **Best demo award!**

* M. Peuster and H. Karl: Profile Your Chains, Not Functions: Automated Network Service Profiling in DevOps Environments. IEEE Conference on Network Function Virtualization and Software Defined Networks (NFV-SDN), Berlin, Germany. (2017) (accepted)

## Links

* [Mininet website](http://mininet.org)
* [Maxinet website](http://maxinet.github.io)
* [Docker](https://www.docker.com)

# [](#contact)Contact

## Support
If you have any questions, please use GitHub's [issue system](https://github.com/containernet/containernet/issues) or Containernet's [Gitter channel](https://gitter.im/containernet/) to get in touch.

## Contribute
Your contributions are very welcome! Please fork the GitHub repository and create a pull request. We use [Travis-CI](https://travis-ci.org/containernet/containernet) to automatically test new commits. 

## Lead developer

Manuel Peuster
* Mail: <manuel (dot) peuster (at) upb (dot) de>
* GitHub: [@mpeuster](https://github.com/mpeuster)
* Website: [Paderborn University](https://cs.uni-paderborn.de/cn/person/?tx_upbperson_personsite%5BpersonId%5D=13271&tx_upbperson_personsite%5Bcontroller%5D=Person&cHash=bafec92c0ada0bdfe8af6e2ed99efb4e)
