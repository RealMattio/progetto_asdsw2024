#!/usr/bin/bash

python3 coordinator_quorum.py &
python3 coordinator_sync.py &
python3 coordinator_async.py &