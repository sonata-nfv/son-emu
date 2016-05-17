#!/bin/bash
# test if a vnf can be deployed and monitored

#start test emulator topology
python src/emuvim/examples/monitoring_demo_topology.py &

# start a vnf
son-emu-cli compute start -d datacenter1 -n vnf1  --net '(id=input,ip=10.0.10.3/24),(id=output,ip=10.0.10.4/24)'
# monitor a metric
son-emu-cli monitor setup_metric -vnf vnf1:output --metric tx_packets

sleep 5

# check if metric is monitored as expected
cpu_load=$(son-emu-cli monitor prometheus -d datacenter1 -vnf vnf1 -q 'sum(rate(container_cpu_usage_seconds_total{id="/docker/<uuid>"}[10s]))')

# stop the monitor
son-emu-cli monitor stop_metric -vnf vnf1:output --metric tx_packets

#stop the vnf
son-emu-cli compute stop -d datacenter1 -n vnf1

# test if prometheus query worked
if [[ $cpu_load =~ $regex ]] ; then
	echo " cpu monitor test OK"
	exit 0
else
	echo $cpu_load
	echo "cpu monitor test not OK"
	exit 1
fi
