from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
import psycopg2
import json
import os
import yaml
from datetime import datetime, timedelta
from dateutil import parser, tz
from typing import List, Dict, Any
from pydantic import BaseModel, Field
import dotenv

app = FastAPI()

# .envファイルが存在する場合は読み込む
if os.path.exists(".env"):
    dotenv.load_dotenv()

# 設定ファイルから設定を読み込む
def load_config(config_file="config.yaml"):
    """Loads configuration from a YAML file.

    Args:
        config_file (str): Path to the YAML configuration file.

    Returns:
        dict: Configuration data loaded from the file.
    """
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        print(f"Error: Configuration file not found at {config_file}")
        return {}
    except yaml.YAMLError as e:
        print(f"Error: Invalid YAML format in {config_file}: {e}")
        return {}

# 設定ファイルから設定を取得
config = load_config()
SECRET_KEY = os.environ.get("SECRET_KEY", "your_secret_key_here")
DEFAULT_DAYS = config.get("DEFAULT_DAYS", 30)
ROOT_URL = config.get("ROOT_URL", "http://127.0.0.1:10000")
SUBMIT_URL = config.get("SUBMIT_URL", "/submit")
GET_DOCUMENT_LIST_URL = config.get("GET_DOCUMENT_LIST_URL", "/get_document_list")
UPDATE_DOWNLOADED_URL = config.get("UPDATE_DOWNLOADED_URL", "/update_downloaded")
INIT_DB_URL = "/init_db"


# Pydantic モデルの定義
class User(BaseModel):
    name: str

class Group(BaseModel):
    name: str

class Content(BaseModel):
    fid16: Dict[str, str]
    fid3: Dict[str, Any]

class Document(BaseModel):
    document_id: int = Field(..., description="文書ID")
    document_number: str = Field(..., description="文書番号")
    document_title: str = Field(..., description="文書タイトル")
    request_user: User = Field(..., description="申請ユーザー")
    request_group: Group = Field(..., description="申請グループ")
    contents: Content = Field(..., description="文書内容")
    flow_status: str = Field(..., description="フロー状態")
    end_date: str = Field(..., description="終了日付")

class AuthData(BaseModel):
    key: str

class UpdateDownloadedData(BaseModel):
    key: str
    document_id: int
    downloaded: int = Field(..., ge=0, le=1, description="downloadedは0か1")

# PostgreSQLデータベースに接続する関数
def get_db_connection():
    DATABASE_URL = os.environ.get("DATABASE_URL")
    conn = psycopg2.connect(DATABASE_URL)
    return conn

# テーブル作成関数
def create_table(force: bool = False):
    conn = get_db_connection()
    cursor = conn.cursor()
    if force:
        cursor.execute("DROP TABLE IF EXISTS purchase_requisition")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS purchase_requisition(
            document_id INTEGER PRIMARY KEY,
            document_number TEXT,
            document_title TEXT,
            request_user TEXT,
            request_group TEXT,
            request_factory TEXT,
            amount INTEGER DEFAULT 0,
            flow_status TEXT,
            end_date TEXT,
            downloaded INTEGER DEFAULT 0,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()

# データを挿入する関数
def insert_data(data: Document):
    conn = get_db_connection()
    cur = conn.cursor()

    # end_date の日付書式を変換（dateutilを使用）
    try:
        utc_dt = parser.parse(data.end_date)
        jst_tz = tz.gettz('Asia/Tokyo')
        jst_dt = utc_dt.astimezone(jst_tz)
        formatted_end_date = jst_dt.strftime('%Y/%m/%d %H:%M:%S')
    except (ValueError, TypeError) as e:
        print(f"Error: Invalid date format for end_date: {data.end_date}. Error message:{e}")
        # 日付変換に失敗した場合、元の値をそのまま格納する
        formatted_end_date = data.end_date

    i_data = {
        'document_id': data.document_id,
        'document_number': data.document_number,
        'document_title': data.document_title,
        'request_user': data.request_user.name,
        'request_group': data.request_group.name,
        'request_factory': data.contents.fid16['label'],
        'amount': data.contents.fid3['value'],
        'flow_status': data.flow_status,
        'end_date': formatted_end_date,  # 変換後の日付を使用
    }

    insert_tuple = tuple(i_data.values())

    strSQL = """
        INSERT INTO purchase_requisition(document_id, document_number, document_title, request_user, 
        request_group, request_factory, amount, flow_status, end_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (document_id) DO NOTHING;
    """

    cur.execute(strSQL, insert_tuple)
    conn.commit()
    conn.close()

# セキュリティキーチェック用の依存性関数
def check_secret_key(auth_data: AuthData):
    if auth_data.key != SECRET_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return auth_data

# POSTエンドポイントを定義
@app.post(SUBMIT_URL, response_model=Dict)
async def submit(data: Document):
    insert_data(data)
    return {"message": f"document_id {data.document_id} Data inserted successfully"}

# データのリストを取得するエンドポイント
@app.post(GET_DOCUMENT_LIST_URL, dependencies=[Depends(check_secret_key)], response_model=List[Dict])
async def get_document_list(auth_data: AuthData):
    conn = get_db_connection()
    cur = conn.cursor()

    # 現在時刻を取得
    now = datetime.now(tz=tz.tzutc())
    # 設定ファイルから取得した日数を使用
    days = int(DEFAULT_DAYS)
    # 指定された日数前の日付を計算
    past_date = now - timedelta(days=days)

    # SQLクエリの作成
    strSQL = """
        SELECT * FROM purchase_requisition
        WHERE (downloaded = 0)
           OR (downloaded = 1 AND created_at >= %s)
        ORDER BY created_at DESC
    """

    cur.execute(strSQL, (past_date,))
    rows = cur.fetchall()
    conn.close()

    document_list = []
    for row in rows:
        document = {}
        for i, col in enumerate(cur.description):
            document[col.name] = row[i]
        document_list.append(document)

    return document_list

# downloaded列を更新するエンドポイント
@app.post(UPDATE_DOWNLOADED_URL, dependencies=[Depends(check_secret_key)], response_model=Dict)
async def update_downloaded(data: UpdateDownloadedData):
    conn = get_db_connection()
    cur = conn.cursor()

    strSQL = """
        UPDATE purchase_requisition
        SET downloaded = %s
        WHERE document_id = %s
    """

    cur.execute(strSQL, (data.downloaded, data.document_id))

    if cur.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="document_id not found")

    conn.commit()
    conn.close()

    return {"message": f"downloaded updated for document_id {data.document_id} to {data.downloaded}"}

# テーブルを初期化するエンドポイント
@app.post(INIT_DB_URL, dependencies=[Depends(check_secret_key)], response_model=Dict)
async def init_db(auth_data: AuthData):
    create_table(force=True)
    return {"message": "Database initialized."}

# ルートエンドポイントを定義
@app.get("/")
async def index():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM purchase_requisition")
    total_count = cur.fetchone()[0]
    conn.close()

    return {"message": f"Service is Active. Total documents count: {total_count}"}

if __name__ == "__main__":
    create_table()
    import uvicorn
    ENV_PORT = int(os.environ.get("PORT"))
    uvicorn.run(app)
    # ENV_PORT = int(os.environ.get("PORT"))
    # uvicorn.run(app,host="0.0.0.0", port=ENV_PORT)
