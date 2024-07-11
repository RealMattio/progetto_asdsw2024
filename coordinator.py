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

# questa funzione deve essere modificata affinché restituisca tutti gli N (scelto dall'utente) server nei quali salverò la chiave
# bisogna passargli sia la chiave che il numero di server da restituire
# bisogna scegliere la strategia con cui scegliere i server
def get_server(key, N): #Obiettivo: restituire una lista di N server in cui salvare la chiave
    server_hashes = {hash_function(server+'1'): server for server in servers} #mappa ogni server ad un ash
    for i in range(2,10):
        server_hashes.update({hash_function(server+str(i)): server for server in servers})
   
    sorted_hashes = sorted(server_hashes.keys()) #ordina gli ash
    
    key_hash = hash_function(key)
    selected_servers = [] #raccoglie i primi N server dalla lista ordinata
    
    for server_hash in sorted_hashes: #iterando sugli hash ordinati in modo crescente
        if len(selected_servers) < N: #se il numero dei server è inferiore o uguale a N (numero di repliche che voglio per la chiave specificata)
            selected_servers.append(server_hashes[server_hash]) #aggiungo il server corrispondente all'hash corrente, alla lista 'selected_servers'
        else:
            break
    print(selected_servers)
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
        resp = requests.get(app.url_defaults + 'get/' + str(key))
        r = requests.post(server_down + 'put', json=resp.json())
    #print(response.json(), type(response))
    return jsonify({"status" : f"server {server_down} updated"})




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

