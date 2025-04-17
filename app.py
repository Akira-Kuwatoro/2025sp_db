from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

app = Flask(__name__)
DB_PATH = "inventory.db"

print("📂 Flaskが参照しているDBファイルのパス:", os.path.abspath(DB_PATH))

# 材料一覧の取得（検索・並び替え対応）
def get_items(keyword="", sort_column="id", sort_order="asc"):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    base_query = "SELECT * FROM item"
    params = []

    if keyword:
        base_query += " WHERE name LIKE ? OR unit LIKE ? OR initial_stock LIKE ?"
        keyword_pattern = f"%{keyword}%"
        params = [keyword_pattern, keyword_pattern, keyword_pattern]

    if sort_column in ["id", "name", "unit", "initial_stock"] and sort_order in ["asc", "desc"]:
        base_query += f" ORDER BY {sort_column} {sort_order}"

    cursor.execute(base_query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows

# トップページ：一覧表示
@app.route('/')
def index():
    keyword = request.args.get('keyword', '')
    sort_column = request.args.get('sort', 'id')
    sort_order = request.args.get('order', 'asc')
    items = get_items(keyword, sort_column, sort_order)
    return render_template('index.html', items=items, keyword=keyword, sort_column=sort_column, sort_order=sort_order)

# 材料追加
@app.route('/add-item', methods=['GET', 'POST'])
def add_item():
    if request.method == 'POST':
        name = request.form['name']
        unit = request.form['unit']
        initial_stock = request.form['initial_stock']

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO item (name, unit, initial_stock) VALUES (?, ?, ?)', (name, unit, initial_stock))
        item_id = cursor.lastrowid
        cursor.execute('INSERT INTO stock_logs (item_id, change_type, quantity) VALUES (?, ?, ?)', (item_id, '登録', initial_stock))
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
        name = request.form['name']
        unit = request.form['unit']
        new_stock = int(request.form['initial_stock'])

        cursor.execute('SELECT initial_stock FROM item WHERE id = ?', (item_id,))
        old_stock = cursor.fetchone()[0]
        diff = new_stock - old_stock

        cursor.execute('UPDATE item SET name=?, unit=?, initial_stock=? WHERE id=?', (name, unit, new_stock, item_id))

        if diff != 0:
            cursor.execute('INSERT INTO stock_logs (item_id, change_type, quantity) VALUES (?, ?, ?)',
                           (item_id, '入庫' if diff > 0 else '出庫', abs(diff)))

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
    row = cursor.fetchone()
    if row:
        quantity = row[0]
        cursor.execute('INSERT INTO stock_logs (item_id, change_type, quantity) VALUES (?, ?, ?)', (item_id, '削除', quantity))

    cursor.execute('DELETE FROM item WHERE id = ?', (item_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

# 履歴ログページ
@app.route('/logs')
def show_logs():
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
    return render_template('logs.html', logs=logs)

if __name__ == '__main__':
    app.run(port=5001, debug=True)
