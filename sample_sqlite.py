import sqlite3

conn = sqlite3.connect('inventory.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    stock INTEGER NOT NULL,
    unit TEXT
)
''')

cursor.execute('INSERT INTO items (name, stock, unit) VALUES (?, ?, ?)',
               ('コーヒー豆', 5, 'kg'))

cursor.execute('SELECT * FROM items')
rows = cursor.fetchall()

print('📦 現在の在庫一覧：')
for row in rows:
    print(row)

conn.commit()
conn.close()
