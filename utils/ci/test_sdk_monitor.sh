#!/bin/bash
# test if a vnf can be deployed and monitored

#start test emulator topology
#python src/emuvim/examples/monitoring_demo_topology.py &

# start a vnf
son-emu-cli compute start -d datacenter1 -n vnf1  --net '(id=input,ip=10.0.10.3/24),(id=output,ip=10.0.10.4/24)'

sleep 1

# monitor a metric
son-emu-cli monitor setup_metric -vnf vnf1:output --metric tx_packets

# allow some time to gather metrics
sleep 20

# check if metric is monitored as expected (exported by son-emu, has vnf name as metric id)
tx_rate=$(son-emu-cli monitor-zapi prometheus -d datacenter1 -vnf vnf1 -q 'rate(sonemu_tx_count_packets{vnf_name="vnf1"}[10s])')

sleep 1

# test if prometheus query worked
echo $tx_rate

regex='\[[0-9.]*, .*\]'

if [[ $tx_rate =~ $regex ]] ; then
	echo " tx_rate monitor test OK"
else
	echo "tx_rate monitor test not OK"
	exit 1
fi


# check if cpu load can be monitored (exported by cAdvisor, needs uuid)
cpu_load=$(son-emu-cli monitor-zapi prometheus -d datacenter1 -vnf vnf1 -q 'sum(rate(container_cpu_usage_seconds_total{id="/docker/<uuid>"}[10s]))')

sleep 1


# test if prometheus query worked
echo $cpu_load

regex='\[[0-9.]*, .*\]'

if [[ $cpu_load =~ $regex ]] ; then
	echo " cpu monitor test OK"
else
	echo "cpu monitor test not OK"
	exit 1
fi

exit 0


