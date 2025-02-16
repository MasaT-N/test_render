# データベーステーブルに登録されたデータ確認用のスクリプトです。

import psycopg2
from psycopg2.extras import DictCursor
from psycopg2.extensions import connection
import os

database_url = os.environ.get('DATABASE_URL')

def get_connection():
    return psycopg2.connect(database_url)

# データベースとのコネクションを確立します。
with get_connection() as connection:
    # カーソルをオープンします
    with connection.cursor(cursor_factory=DictCursor) as cursor:
        # テーブルを削除します。
        # sql = "Drop table if exists json_table;"
        # cursor.execute(sql)

        # テーブル作成SQLを定義します
        sql = "CREATE TABLE if not exists json_table (id SERIAL PRIMARY KEY, data JSONB, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
        # SQLを実行します
        cursor.execute(sql)

        # データ取得します。
        sql = "Select * from json_table;"
        cursor.execute(sql)
        res = cursor.fetchall()
        print(res)


