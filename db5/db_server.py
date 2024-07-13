from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

host = '0.0.0.0'
port = 6004

def get_db_connection():
    conn = sqlite3.connect('keyvalue.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS keyvalue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT NOT NULL  
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/put', methods=['POST'])
def put():
    data = request.json
    key  = data.get('key')
    value = data.get('value')

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if the URL already exists in the database
    result = cursor.execute('SELECT value FROM keyvalue WHERE key = ?', (key,)).fetchone()
    # If it does, update the URL
    if result:
        cursor.execute('UPDATE keyvalue SET value = ? WHERE key = ?', (value, key,))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "key": key, "value": result['value']}), 201
    
    # If not, insert new URL into the database
    try:
        cursor.execute('INSERT INTO keyvalue (key, value) VALUES (?,?)', (key, value,))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "key": key, "value": value}), 201
    except sqlite3.IntegrityError:  # Catch uniqueness constraint violation
        conn.close()
        return jsonify({"error": "URL already exists"}), 409

@app.route('/get/<int:key>', methods=['GET'])
def get(key):
    # If not in cache, query the database
    conn = get_db_connection()
    stringa = 'SELECT * FROM keyvalue WHERE key = ' + str(key)
    data = conn.execute(stringa).fetchone()
    #print(data)
    conn.close()
    if data is None:
        return jsonify({"error": "Not found"}), 404

    return jsonify({"key": data['key'], "value": data['value']})

# rotta per ottenere tutti i valori dal database affinchè possa essere aggiornato dopo il down
@app.route('/get_all', methods=['GET'])
def get_all():
    # Connettersi al database
    conn = get_db_connection()
    cursor = conn.cursor()

    # Eseguire la query per ottenere tutti i valori dalla tabella
    cursor.execute('SELECT key FROM keyvalue')
    # Recuperare tutti i risultati della query
    rows = cursor.fetchall()
    rows_list = []
    # Chiudere la connessione al database
    conn.close()
    for row in rows:
        rows_list.append(row['key'])
    return jsonify(rows_list)

@app.route('/status', methods=['GET'])
def status():
    return jsonify({"status": "OK"})

def run_flask():
    init_db()  # Ensure the database is initialized before starting the app
    app.run(host=host, port=port)

if __name__ == '__main__':
   run_flask()