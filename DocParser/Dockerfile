FROM python:3.8

LABEL maintainer="philippe.saade@lau.edu"

# Download doc to docx converter
RUN apt-get -y update
RUN apt-get install -y default-jre libreoffice-java-common libreoffice-writer

# We copy just the requirements.txt first to leverage Docker cache
COPY ./requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install -r requirements.txt

COPY . /app
RUN mkdir -p /app/files/
RUN mkdir -p /app/static/
ENTRYPOINT [ "python" ]
CMD [ "app.py" ]