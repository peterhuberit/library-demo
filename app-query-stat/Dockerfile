FROM python:3.8-slim-buster
COPY requirements.txt .
RUN pip install --quiet -r requirements.txt
COPY src/ .
ENTRYPOINT ["python", "-u", "query_stat.py"]
