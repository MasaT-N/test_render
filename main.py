from flask import Flask,request
app = Flask(__name__)


@app.route("/")
def hello():
    return "Hello World!"

@app.route('/post_data', methods=['GET', 'POST'])
def check():
    if request.method == 'POST':
        data = f"POSTデータは「{request.json['key']}」です！"
    else:
        data = 'no data'
    return data

if __name__ == "__main__":
    # webサーバー立ち上げ
    app.run()
