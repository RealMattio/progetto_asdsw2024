import requests
import time
import json
coordinator_quorum_url = 'http://127.0.0.1:5000/'
coordinator_sync_url = 'http://127.0.0.1:5001/'
coordinator_async_url = 'http://127.0.0.1:5002/'


def misura_performance(N,W, key=7357):
    h= {'Content-Type': 'application/json'}
    tempo_invio = time.time()
    response = requests.post(coordinator_quorum_url + f'put/{N}/{W}', json={"key": key, "value": "test_performance"}, headers=h)
    tempo_ricezione = time.time()
    tempo_trascorso_quorum = round(tempo_ricezione - tempo_invio, 4)
    print(f"Tempo impiegato dal quorum based coordinator: {tempo_trascorso_quorum} secondi")

    
    tempo_invio = time.time()
    response = requests.post(coordinator_sync_url + f'put/{N}', json={"key": key+1, "value": "test_performance"}, headers=h)
    tempo_ricezione = time.time()
    tempo_trascorso_sync = round(tempo_ricezione - tempo_invio, 4)
    print(f"Tempo impiegato dal sync coordinator: {tempo_trascorso_sync} secondi")

    
    tempo_invio = time.time()
    response = requests.post(coordinator_async_url + f'put/{N}', json={"key": key+2, "value": "test_performance"}, headers=h)
    tempo_ricezione = time.time()
    tempo_trascorso_async = round(tempo_ricezione - tempo_invio, 4)
    print(f"Tempo impiegato dall'async coordinator: {tempo_trascorso_async} secondi")

    return [tempo_trascorso_quorum, tempo_trascorso_sync, tempo_trascorso_async]


if __name__ == '__main__':
    # si vuole misurare il tempo che intercorre tra l'invio di una richiesta di put e la ricezione della risposta
    Ns = [3, 5, 8]
    risultati = []
    key = 7800
    keys = [key+40, key+40*2, key+40*3]
    for N,k in zip(Ns, keys):
        W=N-1
        for i in range(10):
            chiave = k+i*3
            tempi = misura_performance(N,W, key=chiave)
            ris = {"quorum": tempi[0], "sync": tempi[1], "async": tempi[2]}
            ris['iterazione'] = i
            ris['N'] = N
            ris['W'] = W
            ris['key_quorum'] = chiave
            ris['key_sync'] = chiave+1
            ris['key_async'] = chiave+2
            risultati.append(ris)
            time.sleep(2)

    with open(f"risultati.json", "w") as f:
            json.dump(risultati, f, indent=4)
    print("Risultati salvati su file")