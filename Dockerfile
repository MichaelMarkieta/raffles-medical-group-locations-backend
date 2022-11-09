FROM python:3.10.4-slim-bullseye
RUN apt-get update
RUN apt-get install -y libxml2-dev
RUN apt-get install -y libxslt-dev
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY scraper.py ./
ENV PYTHON_ENV=production
CMD ["python3", "scraper.py"]