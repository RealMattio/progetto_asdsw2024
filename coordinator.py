from flask import Flask, request, jsonify
import requests
import hashlib
import threading, time

app = Flask(__name__)

servers = [
    "http://localhost:6000/",
    "http://localhost:6001/",
    "http://localhost:6002/"
]
#listcomprehension che crea un dizionario con chiave ogni server e valore 0
active_servers = {server:0 for server in servers} 


def hash_function(key):
    return int(hashlib.md5(key.encode()).hexdigest(), 16)

def get_server(key):
    server_hashes = {hash_function(server+'1'): server for server in servers}
    for i in range(2,10):
        server_hashes.update({hash_function(server+str(i)): server for server in servers})
   
    sorted_hashes = sorted(server_hashes.keys())
    
    key_hash = hash_function(key)
    
    for server_hash in sorted_hashes:
        if key_hash < server_hash:
            return server_hashes[server_hash]
    
    return server_hashes[sorted_hashes[0]]

@app.route('/get/<int:key>', methods=['GET'])
def get(key):
    server_url = get_server(str(key)) + 'get/' + str(key)

    try:
        response = requests.get(server_url)
        if response.status_code == 200:
            result = response.json()
            result['server'] = server_url
            return jsonify(result), 200
        else:
            return jsonify({'error': 'Failed to get the (key,value) element', 'server': server_url}), 500
    except requests.exceptions.RequestException:
        return jsonify({'error': 'Backend server error', 'server': server_url}), 500


@app.route('/put', methods=['POST'])
def put():
    d = request.json
    key = d["key"]
    h = {'Content-Type': 'application/json'};
    r = requests.post(get_server(str(key)) + 'put', json=d, headers=h)
    return d

def status():
    global active_servers
    global servers
    while True:
        check_status()
        for server in active_servers:
            if active_servers[server] == 0 and server in servers:
                servers.remove(server)
            elif active_servers[server] == 1 and server not in servers:
                servers.append(server)
        print(active_servers, servers)
        time.sleep(5)

def check_status():
    global active_servers
    for server in active_servers:
        try:
            response = requests.get(server + 'status')
            if response.status_code == 200:
                active_servers[server] = 1
            else:
                active_servers[server] = 0
        except requests.exceptions.RequestException:
            active_servers[server] = 0
    #return jsonify(active_servers)

if __name__ == '__main__':
    # Start the Flask app in a separate thread
    threading.Thread(target=app.run).start()
    #app.run(debug=True)

    # Start the status monitoring in a separate thread
    threading.Thread(target=status).start()

