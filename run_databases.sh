#!/usr/bin/bash
flask --app coordinator.py run --port=5000 --host=0.0.0.0 &

cd db1
flask --app simple_db.py run --port=6000 --host=0.0.0.0 &
cd ..

cd db2
flask --app simple_db.py run --port=6001 --host=0.0.0.0 &
cd ..

cd db3
flask --app simple_db.py run --port=6002 --host=0.0.0.0 &
cd ..
