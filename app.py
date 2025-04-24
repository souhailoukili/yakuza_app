from flask import Flask, render_template, request, redirect, session, url_for
import firebase_admin
from firebase_admin import credentials, firestore
import requests
import uuid

# إعداد Flask
app = Flask(__name__)
app.secret_key = "souhail@200320"  # ⚠️ بدّلها بشي سرّ آمن

# إعداد Firebase
cred = credentials.Certificate("yakuza-team-56772-firebase-adminsdk-fbsvc-e279d8df04.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# إعداد Telegram Bot
BOT_TOKEN = "8138821973:AAE12GvrxhlS1kpJHDi6M4MgBSw9iwyBM-A"  # ⚠️ غيّرو بالتوكن ديالك
CHAT_ID = "-1002697339023"  # ⚠️ ID ديال الجروب (بصيغة سالبة)

ADMIN_PASSWORD = "yakuzapass"

def is_logged_in():
    return session.get('logged_in', False)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user_ref = db.collection("users").where("username", "==", username).limit(1).stream()
        user = next(user_ref, None)

        if user:
            data = user.to_dict()
            if data.get("role") == "admin" and password == ADMIN_PASSWORD:
                session['logged_in'] = True
                session['username'] = username
                return redirect(url_for('dashboard'))

        return render_template('login.html', error="❌ اسم المستخدم أو كلمة السر غير صحيحة")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/')
def dashboard():
    if not is_logged_in():
        return redirect('/login')

    users_ref = db.collection("users")
    users = [doc.to_dict() for doc in users_ref.stream()]
    return render_template('dashboard.html', users=users)

@app.route('/block/<user_id>')
def block_user(user_id):
    if not is_logged_in():
        return redirect('/login')
    db.collection("users").document(str(user_id)).update({"blocked": True})
    return redirect('/')

@app.route('/unblock/<user_id>')
def unblock_user(user_id):
    if not is_logged_in():
        return redirect('/login')
    db.collection("users").document(str(user_id)).update({"blocked": False})
    return redirect('/')

@app.route('/send', methods=['GET', 'POST'])
def send_message():
    if not is_logged_in():
        return redirect('/login')

    if request.method == 'POST':
        message = request.form.get('message')
        if message:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            data = {
                "chat_id": CHAT_ID,
                "text": message,
                "parse_mode": "HTML"
            }
            response = requests.post(url, data=data)
            if response.status_code == 200:
                return render_template('send.html', success="✅ تم إرسال الرسالة إلى الجروب بنجاح")
            else:
                return render_template('send.html', error="❌ فشل في إرسال الرسالة: " + response.text)

    return render_template('send.html')

@app.route('/add_user', methods=['GET', 'POST'])
@app.route('/add-user', methods=['GET', 'POST'])  # إضافة مسار بديل بشرطة عادية
def add_user():
    if not is_logged_in():
        return redirect('/login')
        
    if request.method == 'POST':
        username = request.form.get('username')
        role = request.form.get('role', 'user')  # القيمة الافتراضية هي 'user'
        
        # التحقق من وجود اسم المستخدم
        if not username:
            return render_template('add_user.html', error="❌ يرجى إدخال اسم المستخدم")
            
        # التحقق مما إذا كان اسم المستخدم موجودًا بالفعل
        existing_user = db.collection("users").where("username", "==", username).limit(1).get()
        if len(existing_user) > 0:
            return render_template('add_user.html', error="❌ اسم المستخدم موجود بالفعل")
            
        # إنشاء معرف فريد للمستخدم
        user_id = str(uuid.uuid4().int)[:10]  # استخدام أول 10 أرقام من UUID
        
        # إنشاء بيانات المستخدم
        user_data = {
            "username": username,
            "role": role,
            "user_id": user_id,
            "blocked": False,
            "daily_requests": 0,
            "likes_given": 0,
            "last_request": ""
        }
        
        # إضافة المستخدم إلى قاعدة البيانات
        db.collection("users").document(user_id).set(user_data)
        
        return render_template('add_user.html', success=f"✅ تم إضافة المستخدم {username} بنجاح")
        
    return render_template('add_user.html')

if __name__ == '__main__':
    app.run(debug=True)

# إضافة هذا السطر للتوافق مع Vercel
app = app
