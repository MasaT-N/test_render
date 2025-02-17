# データベーステーブルに登録されたデータ確認用のスクリプトです。

import psycopg2
from psycopg2.extras import DictCursor
from psycopg2.extensions import connection
import os
import json

database_url = os.environ.get('DATABASE_URL')

def get_connection():
    return psycopg2.connect(database_url)

# データベースとのコネクションを確立します。
with get_connection() as connection:
    # カーソルをオープンします
    with connection.cursor(cursor_factory=DictCursor) as cursor:
        # # テーブルを削除します。
        # sql = "Drop table if exists json_table;"
        # cursor.execute(sql)

        # # テーブル作成SQLを定義します
        # sql = "CREATE TABLE if not exists json_table (id SERIAL PRIMARY KEY, data JSONB, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
        # # SQLを実行します
        # cursor.execute(sql)

        # データ取得します。
        # sql = "Select count(*) from purchase_requisition;"

        sql = "SET timezone TO 'Asia/Tokyo';"
        cursor.execute(sql)

        sql = """
                SELECT
                    document_id, 
                    document_number, 
                    document_title, 
                    request_user, 
                    request_group, 
                    request_factory, 
                    amount, 
                    flow_status, 
                    (end_date AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Tokyo') as end_date,
                    (created_at AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Tokyo') as created_at
                FROM purchase_requisition;
            """
        cursor.execute(sql)
        res = cursor.fetchall()
        for row in res:
            
            print(row)
   


