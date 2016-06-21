FROM      ubuntu
MAINTAINER iMinds

RUN apt-get update && apt-get install -y \
	iptables \
	arptables \
	ebtables \
	bridge-utils \
	tcpdump \
	openvswitch-switch \
	openvswitch-common
	
RUN mv /usr/sbin/tcpdump /usr/bin/tcpdump

ADD start.sh start.sh
RUN chmod +x start.sh

# emulator specific entrypoint
ENV SON_EMU_CMD ./start.sh

# always use bash as defauld command
CMD /bin/bash