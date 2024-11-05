FROM python:latest

COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
EXPOSE 5182
CMD ["python", "tracker_server.py"]