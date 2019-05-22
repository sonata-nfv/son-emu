FROM sfc-base

ADD vnfs/aggregator.py aggregator.py
ADD vnfs/datastore.py datastore.py
ADD vnfs/dockers/report_aggregator/start.sh start.sh
RUN chmod +x start.sh
RUN mkdir fig

CMD ./start.sh
