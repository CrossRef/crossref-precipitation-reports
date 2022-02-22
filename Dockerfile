# syntax=docker/dockerfile:1
#FROM python:3.9-alpine
FROM python:3.9
WORKDIR /code
#RUN apk add --no-cache gcc musl-dev linux-headers
#RUN apt install -y gcc musl-dev linux-headers
COPY requirements.txt requirements.txt
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
EXPOSE 5000
COPY . .
CMD ["streamlit", "run","precipitation-reports.py"]g