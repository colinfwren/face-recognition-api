# syntax=docker/dockerfile:1
FROM python:3.9-slim-buster

# Set up dependent libraries for face_recognition library

RUN apt-get -y update
RUN apt-get install -y --fix-missing \
    build-essential \
    cmake \
    gfortran \
    git \
    wget \
    curl \
    graphicsmagick \
    libgraphicsmagick1-dev \
    libatlas-base-dev \
    libavcodec-dev \
    libavformat-dev \
    libgtk2.0-dev \
    libjpeg-dev \
    liblapack-dev \
    libswscale-dev \
    pkg-config \
    python3-dev \
    python3-numpy \
    software-properties-common \
    zip \
    && apt-get clean && rm -rf /tmp/* /var/tmp/*

RUN cd ~ && \
    mkdir -p dlib && \
    git clone -b 'v19.9' --single-branch https://github.com/davisking/dlib.git dlib/ && \
    cd  dlib/ && \
    python3 setup.py install --yes USE_AVX_INSTRUCTIONS

# Change to working directory for app
WORKDIR /python-docker
RUN mkdir "uploads"

# Copy over files to install and run app
COPY requirements.txt requirements.txt
COPY app.py app.py
# Copy over file to setup the database
COPY setup-db.py setup-db.py

# Install dependencies
RUN pip3 install -r requirements.txt

# Run app
CMD ["python3", "-m", "flask", "run", "--host=0.0.0.0"]