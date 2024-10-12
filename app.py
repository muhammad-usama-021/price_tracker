from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os
from dotenv import load_dotenv

app = Flask(__name__)

# Load environment variables from .env file
load_dotenv()

# Set the secret key from the environment variable
app.secret_key = os.getenv('SECRET_KEY')

def initialize_database():
    if not os.path.exists('database.db'):
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        # Create 'products' table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                url TEXT NOT NULL UNIQUE,
                target_price REAL NOT NULL
            );
        ''')

        # Create 'price_history' table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER,
                price REAL,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(product_id) REFERENCES products(id)
            );
        ''')

        conn.commit()
        conn.close()
        print("Database initialized successfully.")

def get_db_connection():
    base_dir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(base_dir, 'database.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products').fetchall()
    conn.close()
    return render_template('index.html', products=products)

@app.route('/add', methods=('GET', 'POST'))
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        url = request.form['url']
        target_price = request.form['target_price']

        if not name or not url or not target_price:
            flash('All fields are required!')
            return redirect(url_for('add_product'))

        try:
            target_price = float(target_price)
        except ValueError:
            flash('Target price must be a number.')
            return redirect(url_for('add_product'))

        conn = get_db_connection()
        try:
            conn.execute(
                'INSERT INTO products (name, url, target_price) VALUES (?, ?, ?)',
                (name, url, target_price)
            )
            conn.commit()
            flash('Product added successfully!')
        except sqlite3.IntegrityError:
            flash('Product with this URL already exists.')
        finally:
            conn.close()
        
        return redirect(url_for('index'))

    return render_template('add.html')

@app.route('/history/<int:product_id>')
def history(product_id):
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    if product is None:
        flash('Product not found.')
        conn.close()
        return redirect(url_for('index'))

    price_history = conn.execute(
        'SELECT * FROM price_history WHERE product_id = ? ORDER BY date DESC',
        (product_id,)
    ).fetchall()
    conn.close()
    return render_template('history.html', product=product, price_history=price_history)

if __name__ == '__main__':
    initialize_database()
    app.run(debug=True)
