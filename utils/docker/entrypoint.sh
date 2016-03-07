#! /bin/bash -e
set -x

#cp /dockernet/util/docker/entrypoint.sh /tmp/x.sh
#cat /tmp/x.sh | awk 'NR==1{print; print "set -x"} NR!=1' > /dockernet/util/docker/entrypoint.sh

exec /dockernet/util/docker/entrypoint.sh $*
