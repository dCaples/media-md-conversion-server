# Use Ubuntu 22.04, which has Python 3.10 by default
FROM ubuntu:22.04

# Prevent some apt interactive features
ENV DEBIAN_FRONTEND=noninteractive

# Just for consistent pip output (no buffering)
ENV PYTHONUNBUFFERED=1

# Create a working directory
WORKDIR /app

# 1. Update apt-get
# 2. Install Python 3 + pip + wget
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    wget \
 && rm -rf /var/lib/apt/lists/*

# (Optional) Upgrade pip if you want
RUN python3 -m pip install --upgrade pip

# Install your Python packages
# (Remove or modify if you don't need them.)
RUN pip install \
    magic-pdf[full] \
    huggingface_hub \
    rpyc \
    --extra-index-url https://wheels.myhloli.com

# Download whatever script you need
RUN wget https://github.com/opendatalab/MinerU/raw/master/scripts/download_models_hf.py -O download_models_hf.py
RUN python3 download_models_hf.py

RUN apt-get update && apt-get install -y libgl1 libglib2.0-0

RUN pip install docxpy==0.8.5


# Copy your server code into the container
COPY server.py .

# Expose the port if your server needs it
EXPOSE 18812

# Start your app
CMD ["python3", "server.py"]
# CMD ["tail", "-f", "/dev/null"]
