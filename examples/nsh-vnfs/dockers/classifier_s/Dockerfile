FROM sfc-base

ADD vnfs/classifier.py classifier.py
ADD vnfs/dockers/classifier_s/classifier_simple.py classifier_simple.py
ADD vnfs/dockers/classifier_s/start.sh start.sh
RUN chmod +x start.sh

ENV SON_EMU_CMD ./start.sh
CMD /bin/bash
