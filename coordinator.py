from flask import Flask, request, jsonify
import requests
import hashlib
import threading, time

app = Flask(__name__)
host = '127.0.0.1'
port = 5000
coordinator_url = f'http://{host}:{port}/'

servers = [
    "http://localhost:6000/",
    "http://localhost:6001/",
    "http://localhost:6002/"
]
#listcomprehension che crea un dizionario con chiave ogni server e valore 0
active_servers = {server:0 for server in servers} 


def hash_function(key):
    return int(hashlib.md5(key.encode()).hexdigest(), 16)

# questa funzione deve essere modificata affinché restituisca tutti gli N (scelto dall'utente) server nei quali salverò la chiave
# bisogna passargli sia la chiave che il numero di server da restituire
# bisogna scegliere la strategia con cui scegliere i server
def get_server(key, N): 
    # Mappa ogni server a un hash
    server_hashes = {hash_function(server + '1'): server for server in servers} 
    
    # Ordina gli hash
    sorted_hashes = list(sorted(server_hashes.keys())) 
    
    key_hash = hash_function(key)
    selected_servers = [] # Raccoglie i primi N server dalla lista ordinata in ordine crescente
        
    for server_hash in sorted_hashes:
        if key_hash < server_hash:
            indice = sorted_hashes.index(server_hash) # indice del primo server con hash maggiore dell'hash della chiave

            # se l'indice è minore di len(sorted_hashes) - N, allora prenderò tutti gli N server che seguono il server trovato
            if indice < len(sorted_hashes) - N:
                selected_servers.append(server_hashes[server_hash])
                for i in range(1, N):
                    selected_servers.append(server_hashes[sorted_hashes[indice + i]])
                return selected_servers # restituisco la lista di server selezionati
            
            # altrimenti prendo i server rimanenti fino alla fine della lista e poi ricomincio dall'inizio
            else:
                selected_servers.extend([server_hashes[sorted_hashes[j]] for j in range(indice, len(sorted_hashes))])
                h = N - (len(sorted_hashes) - indice+1)
                selected_servers.extend([server_hashes[sorted_hashes[j]] for j in range(h+1)])
                return selected_servers 

    # Se non è stato trovato un server con hash maggiore dell'hash della chiave
    for i in range(0, N):
        selected_servers.append(server_hashes[sorted_hashes[i]])
    return selected_servers
   

# deve essere modificata affinché la ricerca venga fatta su tutti i server e restituisca il valore della chiave
# in funzione della max membership rule
# 
@app.route('/get/<int:key>', methods=['GET'])
def get(key):
    key = str(key)
    responses = {}

    # Iterate over all servers
    for server in servers:
        server_url = server + 'get/' + key
        try:
            response = requests.get(server_url)
            if response.status_code == 200:
                result = response.json()
                value = result.get('value')
                if value in responses:
                    responses[value] += 1
                else:
                    responses[value] = 1
        except requests.exceptions.RequestException:
            continue

    if not responses:
        return jsonify({'error': 'Failed to get the (key,value) element from any server'}), 500

    # Determine the value based on the max membership quorum rule
    max_value = max(responses, key=responses.get)
    max_count = responses[max_value]

    return jsonify({'key': key, 'value': max_value, 'count': max_count}), 200


# deve essere modificata affinché la chiave venga salvata in tutti i server restituiti da get_server
# aggiungere la verifica del quorum in scrittura
@app.route('/put/<int:N>/<int:W>', methods=['POST'])
def put(N, W): 
    d = request.json
    print(f'd: {d}')
    key = d["key"]
    h = {'Content-Type': 'application/json'}
    server_su_cui_scrivere = get_server(str(key), N) # restituisce la lista dei server in cui salvare la chiave
    success_count = 0
    for server in server_su_cui_scrivere :
        
        try:
            r = requests.post(server + 'put', json=d, headers=h)
            if r.status_code == 200:
                success_count += 1
        except requests.exceptions.RequestException:
            continue

    if success_count >= W:
        return jsonify({'message': 'Write successful', 'key': key, 'value': d['value']}), 200
    else:
        return jsonify({'error': 'Failed to achieve write quorum'}), 500
   

# aggiorna il server che è tornato attivo con i valori degli altri server
def update(server_down):
    # ottengo tutti i valori che sono salvati nel server che è tornato attivo
    response = requests.get(server_down + 'get_all')
    data = response.json()
    for key in data:
        #per ogni valore nel server tornato up faccio un get dagli altri server e un put sul server tornato up per aggiornare il valore
        #faccio una richiest a se stesso per ottenere il valore
        resp = requests.get(coordinator_url + 'get/' + str(key)).json()
        
        message = {"key": resp['key'], "value": resp['value']}
        header = {'Content-Type': 'application/json'}

        try :
            r = requests.post(server_down + 'put', json=message, headers=header)
            if r.status_code == 200:
                print(f"key {key} updated in server {server_down}\n")
        except requests.exceptions.RequestException:
            print(f"key {key} not updated in server {server_down}\n")
            continue
    return 

def status():
    global active_servers
    global servers
    while True:
        check_status()
        for server in active_servers:
            if active_servers[server] == 0 and server in servers:
                servers.remove(server)
            elif active_servers[server] == 1 and server not in servers: #server che da down diventa up
                update(server)
                servers.append(server)
                # aggiornare il server che è tornato attivo con i nuovi valori
        print(servers)
        #print(active_servers, servers)
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

def run():
    app.run(host=host, port=port)


if __name__ == '__main__':
    # Start the Flask app in a separate thread
    threading.Thread(target=run).start()
    #threading.Thread(target=app.run(host=host, port=port)).start()
    #app.run(debug=True)

    # Start the status monitoring in a separate thread
    threading.Thread(target=status).start()

