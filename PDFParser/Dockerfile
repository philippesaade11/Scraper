FROM python:3.8

LABEL maintainer="philippe.saade@lau.edu"

RUN apt-get -y update
RUN apt-get install -y libmagickwand-dev ghostscript
RUN mv /etc/ImageMagick-6/policy.xml /etc/ImageMagick-6/policy.xml.off

# We copy just the requirements.txt first to leverage Docker cache
COPY ./requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install -r requirements.txt

COPY . /app
RUN mkdir -p /app/files/
RUN mkdir -p /app/static/
ENTRYPOINT [ "python" ]
CMD [ "app.py" ]