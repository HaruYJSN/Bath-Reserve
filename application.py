from flask import *
import datetime
import hashlib
import pyodbc
import random
import json
import os
import numpy as np

from server_settings import server, database, username, password, driver 
from timetable import gen_timetable

app = Flask(__name__)
app.secret_key = str(random.randrange(9999999999999999))
app.jinja_env.add_extension("jinja2.ext.loopcontrols")
tz_jst = datetime.timezone(datetime.timedelta(hours=9))

# 入浴時間リスト
# 七宝寮
times_cloisonne = gen_timetable("17:00", "22:50", "25")
# 紫雲寮
# 入浴時間が点呼とかぶらない・浴室利用可能時間を超えないように
avoid = [{"time":"21:00","type":"restart"}, {"time":"23:00", "type":"shorten"}]
times_purple = gen_timetable("17:00", "22:50", "45", avoid=avoid)

# favicon設定
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, "img"), "favicon.ico", mimetype='image/vnd.microsoft.icon')

# ログインページへの遷移
@app.route("/", methods=["GET", "POST"])
def hello():
    return render_template("index.html", Error=0)

# 予約入力画面への遷移
@app.route("/reserve", methods=["GET", "POST"])
def login_manager():
    # ユーザ変数取得
    print(request)
    userid = request.form["userid"]
    userpassword = request.form["password"]
    # DB接続
    cnxn = pyodbc.connect('DRIVER='+driver+';SERVER='+server+';PORT=1433;DATABASE='+database+';UID='+username+';PWD='+password)
    cursor = cnxn.cursor()
    # DBからパスワード取得
    sql = "SELECT userpassword FROM users WHERE userid = ?"
    cursor.execute(sql, userid)
    result = cursor.fetchone()
    # パスワード認証
    i = 0
    while i<10:
        userpassword = hashlib.sha256(userpassword.encode()).hexdigest()
        i += 1
    if userid == "" or userpassword == "":
        return render_template("index.html", Error=1)
    elif result == None:
        return render_template("index.html", Error=4)
    elif result[0] != userpassword:
        return render_template("index.html", Error=2)
    # 寮取得
    sql = "SELECT dormitory_type FROM users WHERE userid = ?"
    cursor.execute(sql, userid)
    result = cursor.fetchone()
    dormitory_type = result[0]
    # DBから予約状況取得
    now = datetime.datetime.now(tz_jst)
    today = now.strftime("%Y_%m_%d ")
    nowtime = datetime.datetime.strptime(now.strftime("%H:%M"),"%H:%M")
    # 七宝寮 or 紫雲寮
    sql = "SELECT "
    i = 0
    while i < len(times_cloisonne)-1:
        sql = sql + "SUM(CASE WHEN date = '" + today + times_cloisonne[i] + "' THEN 1 ELSE 0 END), "
        i += 1
    sql_small = sql[:-2] +" FROM reserve WHERE bath_type = 0"
    sql_large = sql[:-2] +" FROM reserve WHERE bath_type = 1"
    cursor.execute(sql_small)
    reservation_small = cursor.fetchone()
    cursor.execute(sql_large)
    reservation_large = cursor.fetchone()
    sql = "SELECT "
    i = 0
    while i < len(times_purple)-1:
        sql = sql + "SUM(CASE WHEN date = '" + today + times_purple[i] + "' THEN 1 ELSE 0 END), "
        i += 1
        if i == 5:
            i += 1
    sql_purple = sql[:-2] +"FROM reserve WHERE bath_type = 2"
    cursor.execute(sql_purple)
    reservation_purple = cursor.fetchone()
    # 既存の自身の予約を確認
    sql = "SELECT bath_type, date FROM reserve WHERE userid=? AND date LIKE ?"
    cursor.execute(sql, userid, today+"%")
    result = cursor.fetchone()
    if result == None:
        bath_type = ""
        bath_time = ""
        reserved = False
    else:
        bath_type = result[0]
        bath_time = str(result[1])[11:]
        reserved = True
    # DB切断
    cursor.close()
    cnxn.close()
    # 返却処理
    session['userid'] = userid
    session['login_flag'] = True
    session['reserved'] = reserved
    session['dormitory_type'] = dormitory_type
    if dormitory_type == 0:
        timeover = 0
        for i in range(len(times_cloisonne)):
            if nowtime >= datetime.datetime.strptime(times_cloisonne[i], "%H:%M"):
                timeover = i
        responce = make_response(render_template("reserve.html",today=now.strftime("%m/%d") ,userid=userid, times=times_cloisonne, times_len=len(times_cloisonne), reservation_small=reservation_small, reservation_large=reservation_large, reservation_purple=reservation_purple,bath_type=bath_type, bath_time=bath_time, dormitory_type=dormitory_type, timeover=timeover))
        return responce
    elif dormitory_type == 1:
        timeover = len(times_purple)
        for i in range(len(times_purple)):
            if nowtime >= datetime.datetime.strptime(times_purple[i], "%H:%M"):
                timeover = i
        responce = make_response(render_template("reserve.html",today=now.strftime("%m/%d") ,userid=userid, times=times_purple, times_len=len(times_purple), reservation_small=reservation_small, reservation_large=reservation_large, reservation_purple=reservation_purple, bath_type=bath_type, bath_time=bath_time, dormitory_type=dormitory_type, timeover=timeover))
        return responce

# 予約の実行，予約完了画面への遷移
@app.route("/reserve_resister", methods=["GET", "POST"])
def reserve_register():
    # ユーザ変数取得
    userid = session['userid']
    desired_time = request.form["desired_time"]
    now = datetime.datetime.now()
    today = now.strftime("%Y_%m_%d ")
    nowtime = datetime.datetime.strptime(now.strftime("%H:%M"),"%H:%M")
    bath_type = int(desired_time)//100
    if session['dormitory_type'] == 0:
        desired_time = now.strftime("%Y_%m_%d ") + times_cloisonne[int(desired_time)%100]
    elif session['dormitory_type'] == 1:
        desired_time = now.strftime("%Y_%m_%d ") + times_purple[int(desired_time)%100]
    if now > datetime.datetime.strptime(desired_time, "%Y_%m_%d %H:%M"):
        responce = make_response(render_template("index.html", Error=3))
        return responce
    # DB接続
    cnxn = pyodbc.connect('DRIVER='+driver+';SERVER='+server+';PORT=1433;DATABASE='+database+';UID='+username+';PWD='+password)
    cursor = cnxn.cursor()
    # セッション認証
    if session['login_flag']:
        # 予約状況再確認
        sql = "SELECT SUM(CASE WHEN date = ? THEN 1 ELSE 0 END) FROM reserve WHERE bath_type=?"
        cursor.execute(sql, desired_time, bath_type)
        result = cursor.fetchone()
        print(result)
        if (result[0] >= 9 and bath_type == 1) or (result[0] >= 4 and bath_type == 0) or (result[0] >= 6 and bath_type == 2):
            return render_template("index.html", Error=3)
        if session['reserved']:
            # DBの予約を更新
            sql = "UPDATE reserve SET bath_type=?, date=? WHERE userid=? AND date LIKE ?"
            cursor.execute(sql, str(bath_type), desired_time, session['userid'], today+"%")
            cnxn.commit()
        else:
            # DBに予約登録
            sql = "INSERT INTO reserve VALUES(?, ?, ?)"
            cursor.execute(sql, session["userid"], str(bath_type), desired_time)
            cnxn.commit()
    else:
        render_template("index.html", Error=3)
    # DB切断
    cursor.close()
    cnxn.close()
    #返却処理
    session.pop('userid', None)
    session.pop('login_flag', None)
    session.pop('reserved', None)
    session.pop('dormitory_type', None)
    return render_template("reserve_success.html", desired_time=desired_time, userid=userid)
    
# ユーザー登録への遷移
@app.route("/user_regist_form", methods=["GET", "POST"])
def user_regist_form():
    return render_template("user_regist_form.html")

# ユーザー登録の実行，登録完了画面への遷移
@app.route("/user_register", methods=["GET","POST"])
def user_resister():
    # ユーザ変数取得
    userid = request.form["userid"]
    userpassword = request.form["password"]
    # DB接続
    cnxn = pyodbc.connect('DRIVER='+driver+';SERVER='+server+';PORT=1433;DATABASE='+database+';UID='+username+';PWD='+password)
    cursor = cnxn.cursor()
    # DBに学籍番号の存在を問い合わせ
    sql = "SELECT userid FROM users WHERE userid=?"
    cursor.execute(sql, userid)
    result = cursor.fetchone()
    if(result == None):
        return render_template("user_regist_form.html", Error=1)
    # DBにパスワードがすでに登録されているかを確認
    sql = "SELECT userpassword FROM users WHERE userid=?"
    cursor.execute(sql, userid)
    result = cursor.fetchone()
    if(result[0] != ""):
        return render_template("user_regist_form.html", Error=2)
    # パスワードストレッチング
    i = 0
    while i<10:
        userpassword = hashlib.sha256(userpassword.encode()).hexdigest()
        i += 1
    # DBにパスワードを登録
    sql = "UPDATE users SET userpassword=? WHERE userid=?"
    cursor.execute(sql, userpassword, userid)
    cnxn.commit()
    # DB切断
    cursor.close()
    cnxn.close()
    # 返却処理
    return render_template("user_regist_success.html")

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000, threaded=True)