# syntax=docker/dockerfile:1
FROM python:3.9
WORKDIR /code
# set virtual env
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY requirements.txt requirements.txt
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
EXPOSE 5000
COPY . .
CMD ["streamlit", "run","precipitation-reports.py"]g