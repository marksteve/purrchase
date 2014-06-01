FROM marksteve/python
ADD requirements /tmp/requirements
RUN pip install -r /tmp/requirements/common.txt
RUN mkdir /src
VOLUME /src
WORKDIR /src
