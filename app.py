from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
DB_PATH = "inventory.db"

# --- デバッグ用 ---
print("📂 Flaskが参照しているDBファイルのパス:", os.path.abspath(DB_PATH))

# 材料一覧取得
def get_items():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM item')
    rows = cursor.fetchall()
    conn.close()
    return rows

# ログ一覧取得
def get_logs():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT stock_logs.id, item.name, stock_logs.change_type, stock_logs.quantity, stock_logs.timestamp
        FROM stock_logs
        JOIN item ON stock_logs.item_id = item.id
        ORDER BY stock_logs.timestamp DESC
    ''')
    logs = cursor.fetchall()
    conn.close()
    return logs

# トップページ
@app.route('/')
def index():
    items = get_items()
    return render_template('index.html', items=items)

# 材料追加
@app.route('/add-item', methods=['GET', 'POST'])
def add_item():
    if request.method == 'POST':
        name = request.form['name']
        unit = request.form['unit']
        initial_stock = int(request.form['initial_stock'])

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO item (name, unit, initial_stock) VALUES (?, ?, ?)',
                       (name, unit, initial_stock))
        item_id = cursor.lastrowid
        cursor.execute('INSERT INTO stock_logs (item_id, change_type, quantity) VALUES (?, ?, ?)',
                       (item_id, '登録', initial_stock))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    return render_template('add_item.html')

# 材料編集
@app.route('/edit/<int:item_id>', methods=['GET', 'POST'])
def edit_item(item_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if request.method == 'POST':
        new_name = request.form['name']
        new_unit = request.form['unit']
        new_stock = int(request.form['initial_stock'])

        cursor.execute('SELECT initial_stock FROM item WHERE id = ?', (item_id,))
        old_stock = cursor.fetchone()[0]
        diff = new_stock - old_stock

        cursor.execute('UPDATE item SET name = ?, unit = ?, initial_stock = ? WHERE id = ?',
                       (new_name, new_unit, new_stock, item_id))

        if diff != 0:
            cursor.execute('INSERT INTO stock_logs (item_id, change_type, quantity) VALUES (?, ?, ?)',
                           (item_id, '編集', diff))

        conn.commit()
        conn.close()
        return redirect(url_for('index'))

    cursor.execute('SELECT * FROM item WHERE id = ?', (item_id,))
    item = cursor.fetchone()
    conn.close()
    return render_template('edit_item.html', item=item)

# 材料削除
@app.route('/delete/<int:item_id>', methods=['POST'])
def delete_item(item_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('SELECT initial_stock FROM item WHERE id = ?', (item_id,))
    stock = cursor.fetchone()
    if stock:
        cursor.execute('INSERT INTO stock_logs (item_id, change_type, quantity) VALUES (?, ?, ?)',
                       (item_id, '削除', -stock[0]))

    cursor.execute('DELETE FROM item WHERE id = ?', (item_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

# ログページ
@app.route('/logs')
def logs():
    logs = get_logs()
    return render_template('logs.html', logs=logs)

# アプリ起動
if __name__ == '__main__':
    app.run(debug=True, port=5001)
