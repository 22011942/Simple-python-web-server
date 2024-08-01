FROM python:latest
WORKDIR /src
COPY . .
RUN pip install requests
CMD python server.py 8000