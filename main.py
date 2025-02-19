from flask import Flask,request, jsonify,render_template
import json
import psycopg2
from psycopg2.extras import DictCursor
import yaml
import datetime

import os

app = Flask(__name__)
database_url = os.environ.get('DATABASE_URL')

@app.route("/")
def hello():
    purchase_requisitions = get_purchase_requisition_list() 
    purchase_requisition_count = get_purchase_requisition_count()
    return render_template('index.html', purchase_requisitions=purchase_requisitions, purchase_requisition_count = purchase_requisition_count)

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
            # テーブル作成SQLを構築する
            strSQL = """    
                CREATE TABLE if not exists purchase_requisition( 
                    document_id integer PRIMARY KEY, 
                    document_number varchar(30),
                    document_title varchar(50),
                    request_user varchar(30),
                    request_group varchar(30),
                    request_factory varchar(30),
                    amount integer default 0,
                    flow_status varchar(10),
                    end_date timestamp,    
                    json_data JSONB, 
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            cur.execute(strSQL)

def insert_data(data):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            # データを辞書型変数に格納する
            i_data = {}
            i_data.setdefault('document_id',data['document_id'])
            i_data.setdefault('document_number',data['document_number'])
            i_data.setdefault('document_title',data['document_title'])
            i_data.setdefault('request_user',data['request_user']['name'])
            i_data.setdefault('request_group',data['request_group']['name'])
            i_data.setdefault('request_factory',data['contents']['fid16']['label'])
            i_data.setdefault('amount',data['contents']['fid3']['value'])
            i_data.setdefault('flow_status',data['flow_status'])
            i_data.setdefault('end_date',data['end_date'])

            # データをタプル型変数に格納する
            insert_tuple = tuple(i_data.values()) + (json.dumps(data,ensure_ascii=False), ) 

            # データを挿入するSQLを構築する
            strSQL = """
                INSERT 
                    INTO purchase_requisition( 
                        document_id, 
                        document_number, 
                        document_title, 
                        request_user, 
                        request_group, 
                        request_factory, 
                        amount, 
                        flow_status, 
                        end_date, 
                        json_data
                    ) 
                    SELECT
                        * 
                    FROM
                        ( 
                            VALUES ( 
                                %s, 
                                '%s', 
                                '%s', 
                                '%s', 
                                '%s', 
                                '%s', 
                                %s, 
                                '%s', 
                                TIMESTAMP '%s', 
                                '%s' ::json
                            )
                        ) AS new ( 
                            document_id, 
                            document_number, 
                            document_title, 
                            request_user, 
                            request_group, 
                            request_factory, 
                            amount, 
                            flow_status, 
                            end_date, 
                            json_data
                        ) 
                    WHERE
                        NOT EXISTS ( 
                            SELECT
                                * 
                            FROM
                                purchase_requisition 
                            WHERE
                                document_id = new.document_id
                        );
                """
            strSQL = strSQL % insert_tuple
            cur.execute(strSQL)

def get_purchase_requisition_list():
    with get_connection() as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            setting = read_setting('setting.yaml')
            strSQL = f"""
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
                from purchase_requisition
                order by end_date desc
                limit {setting['limit']};
            """
            cur.execute(strSQL)
            res = cur.fetchall()
            td = datetime.timedelta(hours=9)
            for row in res:
                row['end_date'] = (row['end_date'] + td).strftime("%Y-%m-%d %H:%M:%S")
            return res 
        
def get_purchase_requisition_count():
    with get_connection() as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            setting = read_setting('setting.yaml')
            strSQL = f"""
                Select
                    count(*)
                from purchase_requisition;
            """
            cur.execute(strSQL)
            res = cur.fetchone()
            return res[0]         

def read_setting(yaml_path):
    with open(yaml_path,'r',encoding='utf-8') as f:       
        return yaml.safe_load(f)
            
def get_connection():
    return psycopg2.connect(database_url)

if __name__ == "__main__":
    # webサーバー立ち上げ
    app.run()
