FROM joyzoursky/python-chromedriver:3.7-selenium
WORKDIR /app
COPY requirements.txt requirements.txt
RUN apt update && apt install git -y
RUN /usr/local/bin/python -m pip install --upgrade pip
RUN pip3 install -r requirements.txt

RUN apt install software-properties-common -y && \
  apt install ffmpeg -y