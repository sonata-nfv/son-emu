FROM sfc-base

ADD vnfs/sf.py sf.py
ADD vnfs/datastore.py datastore.py
ADD vnfs/dockers/sf2_s/sf2_s.py sf2_s.py
ADD vnfs/dockers/sf2_s/start.sh start.sh
RUN chmod +x start.sh

ENV SON_EMU_CMD ./start.sh
CMD /bin/bash
