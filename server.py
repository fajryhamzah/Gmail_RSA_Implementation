from flask import Flask
from flask_mail import Mail, Message
from flask import render_template
import imaplib
import email
import redis
from flask import Flask, request, redirect, flash, url_for
from Crypto.PublicKey import RSA
import json
import base64


app = Flask(__name__)
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = None
app.config['MAIL_PASSWORD'] = None
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

r = redis.Redis()

def kosong():
    if not app.config['MAIL_USERNAME']:
        return redirect("/")
    else:
        return None

def kirim_email(to,subjek,isi):
    msg = Message(subjek, sender = app.config["MAIL_USERNAME"], recipients = [to])
    msg.body = isi
    mail = Mail(app)
    mail.send(msg)

@app.template_filter('decode')
def decode(s):
    return base64.b64decode(s)

#main login
@app.route('/',methods=["post","get"])
def index():
    if not kosong(): return redirect("/home")

    #login using gmail
    if request.method == "POST":
        app.config['MAIL_USERNAME'] = request.form.get("mail")
        app.config['MAIL_PASSWORD'] = request.form.get("pass")
        return redirect("/home")


    return render_template('home.html')

@app.route('/home',methods=["post","get"])
def home():
    if kosong(): return kosong()

    encrypt = r.get(str(app.config['MAIL_USERNAME'])+"_pubkey")
    if encrypt:
        encrypt = json.loads(encrypt)
    else:
        encrypt = {}

    if request.method == "POST":
        to = request.form.get("tujuan")
        sub = request.form.get("judul")
        isi = request.form.get("isi")
        en = request.form.get("en")
        pesan = isi

        if en != "1":
            public = base64.b64decode(encrypt[en])
            enc = RSA.importKey(public)
            pesan = base64.b64encode(enc.encrypt(isi.encode('utf-8'),None)[0])

        kirim_email(to,sub,pesan)


    key = encrypt.keys()

    return render_template('send.html',info=key)

@app.route('/encrypt_key',methods=["post","get"])
def encrypt():
    if kosong(): return kosong()
    encrypt = r.get(str(app.config['MAIL_USERNAME'])+"_enckey")
    if encrypt:
        encrypt = json.loads(encrypt)

    if request.method == "POST":
        if not encrypt:
            encrypt = {}

        name = request.form.get("name")
        private = request.form.get("private")
        public = request.form.get("public")


        new = {name:{"private":base64.b64encode(private),"public":base64.b64encode(public)}}

        encrypt.update(new)

        r.set(str(app.config['MAIL_USERNAME'])+"_enckey",json.dumps(encrypt))

    return render_template('key_list.html',info=encrypt)

@app.route('/read',methods=["post","get"])
def read():
    if kosong(): return kosong()

    if request.method == "POST":
        name = request.form.get("name")
        try:
            mail = imaplib.IMAP4_SSL(app.config["MAIL_SERVER"])

            mail.login(app.config["MAIL_USERNAME"],app.config["MAIL_PASSWORD"])
            mail.select('inbox')

            type, data = mail.search(None, '(FROM "'+name+'")')
            #type, data = mail.search(None, 'ALL')
            mail_ids = data[0]

            id_list = mail_ids.split()
            first_email_id = int(id_list[0])
            latest_email_id = int(id_list[-1])
            rng = range(first_email_id,latest_email_id+1) if first_email_id != latest_email_id else [first_email_id]
            email_list = []

            for i in rng:
                typ, data = mail.fetch(i, '(RFC822)' )

                for response_part in data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_string(response_part[1])
                        email_subject = msg['subject'] if msg['subject'] else "tidak ada subjek"
                        email_from = msg['from']
                        email_date = msg['date']

                        email_list.append([i,email_subject,email_from,email_date])
            email_list.reverse()
            return render_template('read.html',info=email_list)

        except Exception, e:
            print str(e)

    return render_template('read.html')

@app.route('/read_mail/<id>',methods=["post","get"])
def read_mail(id):
    if kosong(): return kosong()

    encrypt = r.get(str(app.config['MAIL_USERNAME'])+"_enckey")
    if encrypt:
        encrypt = json.loads(encrypt)
    else:
        encrypt = {}

    key = encrypt.keys()


    mail = imaplib.IMAP4_SSL(app.config["MAIL_SERVER"])
    mail.login(app.config["MAIL_USERNAME"],app.config["MAIL_PASSWORD"])
    mail.select('inbox')

    typ, data = mail.fetch(id, '(RFC822)' )
    email_list = []

    for response_part in data:
        if isinstance(response_part, tuple):
            msg = email.message_from_string(response_part[1])
            email_subject = msg['subject'] if msg['subject'] else "tidak ada subjek"
            email_from = msg['from']
            email_date = msg['date']
            email_msg = msg.get_payload()[0].get_payload() if type(msg.get_payload()) is not str else msg.get_payload()

            email_list = [email_subject,email_from,email_date,email_msg]

    if request.method == "POST":
        name = request.form.get("en")
        encrypt = r.get(str(app.config['MAIL_USERNAME'])+"_enckey")
        if encrypt:
            encrypt = json.loads(encrypt)
        keys = base64.b64decode(encrypt[name]["private"])
        enc = RSA.importKey(keys)

        try:
            decrypt = enc.decrypt(base64.b64decode(email_msg)).decode('utf-8').lstrip()
        except Exception, e:
            decrypt = "Key Salah"

        return render_template('read_mail.html',info=email_list,key=key,decrypt=decrypt)

    return render_template('read_mail.html',info=email_list,key=key)

@app.route('/public_key',methods=["post","get"])
def public():
    if kosong(): return kosong()
    encrypt = r.get(str(app.config['MAIL_USERNAME'])+"_pubkey")
    if encrypt:
        encrypt = json.loads(encrypt)

    if request.method == "POST":
        if not encrypt:
            encrypt = {}

        name = request.form.get("name")
        public = request.form.get("public")

        new = {name:base64.b64encode(public)}

        encrypt.update(new)

        r.set(str(app.config['MAIL_USERNAME'])+"_pubkey",json.dumps(encrypt))

    return render_template('pubkey_list.html',info=encrypt)

@app.route("/exit")
def logout():
    app.config['MAIL_USERNAME'] = None
    app.config['MAIL_PASSWORD'] = None

    return kosong()

@app.route("/api/generate")
def generate():
    key = RSA.generate(2048)
    public = key.publickey().exportKey('PEM').decode('ascii')
    private = key.exportKey('PEM').decode('ascii')

    the_key = {"private":private,"public":public}

    return json.dumps(the_key)

if __name__ == '__main__':
   app.run(debug = True)
