# syntax=docker/dockerfile:1
FROM python:3.9-slim
RUN apt-get update; apt-get install -y curl unzip gcc python3-dev
WORKDIR /code
# set virtual env
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN apt install curl
RUN curl -sSL "https://gitlab.com/crossref/api-summaries/-/jobs/artifacts/main/download?job=annotate" -o artifacts.zip
RUN unzip artifacts.zip
RUN rm data/*.json
RUN rm data/*.db
RUN rm data/*.csv
RUN ls data/
COPY requirements.txt requirements.txt
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
EXPOSE 5000
COPY . .
CMD ["streamlit", "run","precipitation-reports.py"]g