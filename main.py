from flask import Flask,request, jsonify
import json
import psycopg2
from psycopg2.extras import DictCursor

import os

app = Flask(__name__)
database_url = os.environ.get('DATABASE_URL')

@app.route("/")
def hello():
    return "Hello World!"

@app.route('/post_data', methods=['GET', 'POST'])
def check():
    if request.method == 'POST':
        data = request.json
        create_table()
        insert_data(data)
    else:
        data = 'no data'
    return data

def create_table():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("CREATE TABLE if not exists json_table (id SERIAL PRIMARY KEY, data JSONB, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")

def insert_data(data):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("INSERT INTO json_table (data) VALUES (%s)", (json.dumps(data),))

def get_connection():
    return psycopg2.connect(database_url)

if __name__ == "__main__":
    # webサーバー立ち上げ
    app.run()
