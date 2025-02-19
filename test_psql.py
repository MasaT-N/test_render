# データベーステーブルに登録されたデータ確認用のスクリプトです。

import psycopg2
from psycopg2.extras import DictCursor
from psycopg2.extensions import connection
import os
from dotenv import load_dotenv
import json

# .envファイルを読み込みます
load_dotenv()

database_url = os.environ.get('DATABASE_URL')

def main():
    purchase_requisition = get_purchase_requisition_list()
    for row in purchase_requisition:
        print(row.document_id)

def get_connection():
    return psycopg2.connect(database_url)

# # データベースとのコネクションを確立します。
# with get_connection() as connection:
#     # カーソルをオープンします
#     with connection.cursor(cursor_factory=DictCursor) as cursor:
        # # テーブルを削除します。
        # sql = "Drop table if exists json_table;"
        # cursor.execute(sql)

        # # テーブル作成SQLを定義します
        # sql = "CREATE TABLE if not exists test_table (id SERIAL PRIMARY KEY, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
        # # SQLを実行します
        # cursor.execute(sql)

        # # テーブル作成SQLを定義します
        # sql = "INSERT INTO test_table (created_at) VALUES ('2025-02-16T22:25:30Z');"

        # # SQLを実行します
        # cursor.execute(sql)

        # データ取得します。
        # sql = """
        #     Select
        #         document_id, 
        #         document_number, 
        #         document_title, 
        #         request_user, 
        #         request_group, 
        #         request_factory, 
        #         -- amount, 
        #         -- flow_status, 
        #         end_date
        #     from purchase_requisition;
        # """

        # sql = "Select count(*) from purchase_requisition;"
        # cursor.execute(sql)
        # res = cursor.fetchall()
        # for row in res:
        #     print(row)
        

def get_purchase_requisition_list():
    with get_connection() as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            strSQL = """
                Select
                    document_id, 
                    document_number, 
                    document_title, 
                    request_user, 
                    request_group, 
                    request_factory, 
                    amount, 
                    flow_status, 
                    end_date
                from purchase_requisition;
            """
            cur.execute(strSQL)
            res = cur.fetchall()
            return res        

        # # テーブル作成SQLを定義します
        # sql = "CREATE TABLE if not exists json_table (id SERIAL PRIMARY KEY, data JSONB, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
        # # SQLを実行します
        # cursor.execute(sql)

        # # データ取得します。
        # sql = "Select * from json_table;"
        # cursor.execute(sql)
        # res = cursor.fetchone()
        # data = json.dumps(res['data'],ensure_ascii=False,indent=4) 
        # with open("test.json","w",encoding='utf-8') as f:
        #     f.write(data)
    
if __name__ == '__main__':
    main()


