FROM marksteve/python
ADD requirements /tmp/requirements
RUN pip install -r /tmp/requirements/common.txt

RUN add-apt-repository -y ppa:chris-lea/node.js
RUN apt-get update
RUN apt-get install -y nodejs
RUN npm install -g browserify
RUN npm install -g watchify
RUN npm install -g reactify
RUN npm install -g csscomb

RUN pip install watchdog

RUN mkdir /src
VOLUME /src
WORKDIR /src
