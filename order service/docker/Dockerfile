FROM python:3.8 as base


FROM base as builder

WORKDIR /install

COPY src/requirements.txt /requirements.txt

RUN pip install --prefix=/install -r /requirements.txt


FROM base

COPY --from=builder /install /usr/local

COPY src/server.py /opt/my_server/server.py

ENTRYPOINT ["python", "/opt/my_server/server.py"]

EXPOSE 8000