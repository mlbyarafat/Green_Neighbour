from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3, os
from datetime import datetime
from urllib.parse import urlparse

app = Flask(__name__)
app.secret_key = "secret"  

DB_NAME = "database.db"

# Translations including action labels
translations = {
    "en": {
        "title":"Log Eco Action","name":"Your Name","select":"Select Action","qty":"Quantity","submit":"Submit",
        "dashboard":"Dashboard","about":"About",
        "plastic":"Plastic Recycle","compost":"Compost","bike":"Bike Travel"
    },
    "bn": {
        "title":"Eco অ্যাকশন লগ করুন","name":"আপনার নাম","select":"অ্যাকশন নির্বাচন করুন","qty":"পরিমাণ","submit":"জমা দিন",
        "dashboard":"ড্যাশবোর্ড","about":"অ্যাপ সম্পর্কে",
        "plastic":"প্লাস্টিক রিসাইকেল","compost":"কম্পোস্ট","bike":"সাইকেল ভ্রমণ"
    },
    "hi": {
        "title":"ईको एक्शन दर्ज करें","name":"आपका नाम","select":"कार्य चुनें","qty":"मात्रा","submit":"सबमिट करें",
        "dashboard":"डैशबोर्ड","about":"के बारे में",
        "plastic":"प्लास्टिक रीसायकल","compost":"कम्पोस्ट","bike":"बाइक यात्रा"
    },
    "ar": {
        "title":"سجل إجراء بيئي","name":"اسمك","select":"اختر إجراء","qty":"الكمية","submit":"إرسال",
        "dashboard":"لوحة التحكم","about":"حول",
        "plastic":"إعادة تدوير البلاستيك","compost":"تحويل إلى سماد","bike":"رحلة دراجة"
    },
    "zh": {
        "title":"记录环保行动","name":"您的名字","select":"选择行动","qty":"数量","submit":"提交",
        "dashboard":"仪表板","about":"关于",
        "plastic":"塑料回收","compost":"堆肥","bike":"骑行"
    },
    "ur": {
        "title":"ماحولیاتی عمل درج کریں","name":"آپ کا نام","select":"عمل منتخب کریں","qty":"مقدار","submit":"جمع کریں",
        "dashboard":"ڈیش بورڈ","about":"کے بارے میں",
        "plastic":"پلاسٹک ری سائیکل","compost":"کمپوسٹ","bike":"بائیسیکل سفر"
    },
    "es": {
        "title":"Registrar Acción Ecológica","name":"Tu Nombre","select":"Seleccionar acción","qty":"Cantidad","submit":"Enviar",
        "dashboard":"Tablero","about":"Acerca de",
        "plastic":"Reciclaje de plástico","compost":"Compostaje","bike":"Viaje en bici"
    },
    "fr": {
        "title":"Enregistrer une action éco","name":"Votre Nom","select":"Sélectionner l'action","qty":"Quantité","submit":"Soumettre",
        "dashboard":"Tableau de bord","about":"À propos",
        "plastic":"Recyclage plastique","compost":"Compost","bike":"Trajet à vélo"
    },
    "fa": {
        "title":"ثبت اقدام زیست محیطی","name":"نام شما","select":"اقدام را انتخاب کنید","qty":"مقدار","submit":"ارسال",
        "dashboard":"داشبورد","about":"درباره",
        "plastic":"بازیافت پلاستیک","compost":"کمپوست","bike":"سفر با دوچرخه"
    },
    "pt": {
        "title":"Registrar Ação Ecológica","name":"Seu Nome","select":"Selecionar Ação","qty":"Quantidade","submit":"Enviar",
        "dashboard":"Painel","about":"Sobre",
        "plastic":"Reciclagem de plástico","compost":"Compostagem","bike":"Viagem de bicicleta"
    },
}

def get_lang():
    return session.get("lang", "en")

def t(key):
    lang = get_lang()
    return translations.get(lang, translations["en"]).get(key, key)

def action_label(action_type):
    # action_type is e.g. 'plastic_recycle' or 'compost' or 'bike'
    lang = get_lang()
    mapping = {
        "plastic_recycle": "plastic",
        "compost": "compost",
        "bike": "bike"
    }
    word = mapping.get(action_type, action_type)
    return translations.get(lang, translations["en"]).get(word, word)

def init_db():
    if not os.path.exists(DB_NAME):
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("CREATE TABLE actions (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, action_type TEXT, quantity REAL, co2_saved REAL, timestamp TEXT)")
            conn.commit()

def calc_co2(action, q):
    const={"plastic_recycle":2.0,"compost":0.5,"bike":0.12}
    return const.get(action,0)*q

@app.route('/setlang/<lang>')
def setlang(lang):
    # Only accept known languages
    if lang in translations:
        session["lang"] = lang
    ref = request.referrer
    if ref:
        try:
            ref_parsed = urlparse(ref)
            return redirect(ref_parsed.path or "/")
        except:
            pass
    return redirect('/')

@app.route('/')
def index():
    return render_template('index.html', tfunc=t, lang=get_lang())

@app.route('/log_action', methods=['POST'])
def log_action():
    name=request.form.get("name","Anon")
    action=request.form["action_type"]
    try:
        q=float(request.form["quantity"])
    except:
        q=0.0
    co2=calc_co2(action,q)
    ts=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with sqlite3.connect(DB_NAME) as conn:
        c=conn.cursor()
        c.execute("INSERT INTO actions(name,action_type,quantity,co2_saved,timestamp) VALUES (?,?,?,?,?)",(name,action,q,co2,ts))
        conn.commit()
    return redirect('/dashboard')

@app.route('/dashboard')
def dashboard():
    with sqlite3.connect(DB_NAME) as conn:
        c=conn.cursor()
        c.execute("SELECT name,action_type,quantity,co2_saved,timestamp FROM actions ORDER BY id DESC")
        actions=c.fetchall()
        c.execute("SELECT SUM(co2_saved) FROM actions")
        total=c.fetchone()[0] or 0
    return render_template("dashboard.html", actions=actions, total=round(total,2), tfunc=t, action_label=action_label, lang=get_lang())

@app.route('/about')
def about():
    return render_template("about.html", tfunc=t, lang=get_lang())

if __name__=="__main__":
    init_db()
    app.run(debug=True)
