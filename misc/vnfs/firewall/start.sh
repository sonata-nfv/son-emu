#! /bin/bash

#This gives time to the Dockernet to configure the network namespace of the container
sleep 3

echo "Ubuntu started"
echo "start ovs"
service openvswitch-switch start

NAME='fw'

#echo "setup ovs bridge"
ovs-vsctl add-br $NAME
#ovs-vsctl set bridge $NAME datapath_type=netdev
ovs-vsctl set bridge $NAME protocols=OpenFlow10,OpenFlow12,OpenFlow13
#ovs-vsctl set-fail-mode $NAME secure
#ovs-vsctl set bridge $NAME other_config:disable-in-band=true

ovs-vsctl add-port $NAME ${NAME}-eth0

#send out through same interface, on single port
ovs-ofctl add-flow $NAME 'in_port=1,action=in_port'

# iptables -I FORWARD -m physdev --physdev-in eth0 --physdev-out eth1 -d 8.8.8.8 -j DROP

echo "Firewall started"
