# builder image
FROM ubuntu:20.04 AS builder

RUN apt-get update && apt-get install --no-install-recommends -y python3 python3-dev python3-venv python3-pip python3-wheel build-essential && \
	apt-get clean && rm -rf /var/lib/apt/lists/*

# create and activate virtual environment
# using final folder name to avoid path issues with packages
RUN python3 -m venv /home/user/froling-data-collector/venv
ENV PATH="/home/user/froling-data-collector/venv/bin:$PATH"

# install requirements
COPY requirements.txt .
RUN pip3 install --no-cache-dir wheel
RUN pip3 install --no-cache-dir -r requirements.txt


# runner image
FROM ubuntu:20.04 AS runner
LABEL Description="froling-data-collector"

RUN apt-get update && apt-get install --no-install-recommends -y python3 python3-venv && \
	apt-get clean && rm -rf /var/lib/apt/lists/*

#RUN mkdir -p /share/froling-data
RUN useradd --create-home user
RUN mkdir /home/user/froling-data-collector
COPY --from=builder /home/user/froling-data-collector/venv /home/user/froling-data-collector/venv
WORKDIR /home/user/froling-data-collector
COPY . .
RUN chown -R user:user /home/user/froling-data-collector
#RUN chown -R user:user /share/froling-data
RUN chmod a+x /home/user/froling-data-collector/run.sh

# change user
#USER user

# make sure all messages always reach console
ENV PYTHONUNBUFFERED=1

# activate virtual environment
ENV VIRTUAL_ENV=/home/user/froling-data-collector/venv
ENV PATH="/home/user/froling-data-collector/venv/bin:$PATH"

#CMD ["/bin/bash"]
CMD ["./run.sh"]
