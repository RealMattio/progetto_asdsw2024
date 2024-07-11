import sqlite3

# stampo tutte le righe del database keyvalue.db
def print_db():
    conn = sqlite3.connect('keyvalue.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM keyvalue')
    rows = cursor.fetchall()
    for row in rows:
        print(row['id'], row['key'], row['value'])
    conn.close()

if __name__ == '__main__':
    print_db()