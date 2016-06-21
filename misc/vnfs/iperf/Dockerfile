FROM      ubuntu
MAINTAINER iMinds

RUN apt-get update && apt-get install -y \
	mz \
	iperf


ADD start.sh start.sh
RUN chmod +x start.sh

# emulator specific entrypoint
ENV SON_EMU_CMD ./start.sh

# always use bash as defauld command
CMD /bin/bash