# Simple and Basic Deepfloyd IF API

# Why
Because I was planning on serving it via a discord bot until I realized at how *disgustingly slow* it is and that it DEFINETLY is not worth the time and resources over LDM models

# Usage

## API (First)

- Install the dependencies on `requirements.txt`
- Then go to `api/` and `python3 main.py`
- API will be hosted on port `4020` by default, configure it by editing `api/config.json`

## Worker Node

- Install the dependencies on `requirements.txt` and `worker/requirements.txt`
- Go to `worker/` and edit `config.json` with wathever you need
- Execute `python3 main.py --gpu 0` where 0 is the gpu index

You can run this on multiple machines as long as they can connect to the api
They will just use socketio

# FAQ

## Why not use Kubernetes/any other software
Because I don't want to

## This sucks
I know

## Workers disconnect out of nowhere
If you are using NGINX make sure to increase the max request size in the configuration
Also make sure `max_http_buffer_size` is set to some ridiculously high number,
Ideally `1024*1024*30``(as is)