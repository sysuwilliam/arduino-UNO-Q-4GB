#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
python3 python/debian_opencv_server.py
