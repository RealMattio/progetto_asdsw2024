#!/usr/bin/bash

#python3 coordinator.py &

cd db1
python3 db_server.py &
cd ..

cd db2
python3 db_server.py &
cd ..

cd db3
python3 db_server.py &
cd ..

cd db4
python3 db_server.py &
cd ..

cd db5
python3 db_server.py &
cd ..

cd db6
python3 db_server.py &
cd ..

cd db7
python3 db_server.py &
cd ..

cd db8
python3 db_server.py &
cd ..

cd db9
python3 db_server.py &
cd ..

cd db10
python3 db_server.py &
cd ..

