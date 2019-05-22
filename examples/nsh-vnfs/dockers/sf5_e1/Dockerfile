FROM sfc-base

ADD vnfs/sf.py sf.py
ADD vnfs/datastore.py datastore.py
ADD vnfs/dockers/sf5_e1/sf5_e1.py sf5_e1.py
ADD vnfs/dockers/sf5_e1/start.sh start.sh
RUN chmod +x start.sh

ENV SON_EMU_CMD ./start.sh
CMD /bin/bash
