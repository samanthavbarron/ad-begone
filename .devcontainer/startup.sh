#!/bin/bash

curl -LsSf https://astral.sh/uv/install.sh | sh
uv python install 3.12
sudo apt-get update
sudo apt-get install -y ffmpeg