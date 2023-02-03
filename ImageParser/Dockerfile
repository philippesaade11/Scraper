FROM python:3.8

LABEL maintainer="philippe.saade@lau.edu"

RUN apt-get -y update
RUN apt-get install -y --no-install-recommends ffmpeg libsm6 libxext6

# We copy just the requirements.txt first to leverage Docker cache
COPY ./requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install -r requirements.txt
RUN pip install 'git+https://github.com/facebookresearch/detectron2.git'

COPY . /app
RUN mkdir -p /app/files/
RUN mkdir -p /app/static/

RUN wget "https://layoutlm.blob.core.windows.net/dit/dit-fts/publaynet_dit-b_cascade.pth" -o /app/ml/publaynet_dit-b_cascade.pth 
RUN python ml/models.py
ENTRYPOINT [ "python" ]
CMD [ "app.py" ]