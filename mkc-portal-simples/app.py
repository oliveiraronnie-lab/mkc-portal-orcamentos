import os, sqlite3, secrets, smtplib, ssl, csv, io, re
from datetime import datetime, timezone
from email.message import EmailMessage
from functools import wraps
from flask import Flask, request, render_template, redirect, url_for, flash, session, Response, abort

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
DB = os.environ.get('DATABASE_PATH', 'solicitacoes.db')
FIELDS = ['tipo_pessoa','nome','documento','telefone','email','responsavel','imovel','endereco','bairro','cidade','cep','area','pavimentos','atividade','situacao','servico','avcb','vencimento','observacoes']

def conn():
    db=sqlite3.connect(DB)
    db.row_factory=sqlite3.Row
    return db

def init_db():
    with conn() as db:
        db.execute('CREATE TABLE IF NOT EXISTS solicitacoes (id INTEGER PRIMARY KEY AUTOINCREMENT, protocolo TEXT UNIQUE, criado_em TEXT, status TEXT DEFAULT "Recebido", '+', '.join(f'{f} TEXT' for f in FIELDS)+')')
init_db()

def send_notification(data):
    host=os.environ.get('SMTP_HOST'); user=os.environ.get('SMTP_USER'); pwd=os.environ.get('SMTP_PASSWORD'); target=os.environ.get('NOTIFY_EMAIL')
    if not all([host,user,pwd,target]): return False
    msg=EmailMessage(); msg['Subject']=f'Nova solicitação MKC — {data["protocolo"]}'; msg['From']=user; msg['To']=target
    msg.set_content('\n'.join(f'{k}: {v}' for k,v in data.items()))
    try:
        with smtplib.SMTP(host,int(os.environ.get('SMTP_PORT','587')),timeout=12) as smtp:
            smtp.starttls(context=ssl.create_default_context()); smtp.login(user,pwd); smtp.send_message(msg)
        return True
    except Exception:
        app.logger.exception('Falha ao enviar notificação SMTP'); return False

@app.after_request
def headers(resp):
    resp.headers['X-Content-Type-Options']='nosniff'
    resp.headers['X-Frame-Options']='DENY'
    resp.headers['Referrer-Policy']='strict-origin-when-cross-origin'
    resp.headers['Cache-Control']='no-store'
    return resp

@app.route('/')
def home(): return render_template('index.html')

@app.post('/solicitar')
def solicitar():
    if request.form.get('website'): abort(400)
    token=request.form.get('csrf_token','')
    if not secrets.compare_digest(token,session.get('csrf_token','')): abort(400)
    data={k:request.form.get(k,'').strip()[:1500 if k=='observacoes' else 200] for k in FIELDS}
    mandatory=['nome','documento','telefone','email','imovel','endereco','cidade','area','atividade','situacao','servico']
    if any(not data[k] for k in mandatory) or not request.form.get('consentimento'):
        flash('Preencha os campos obrigatórios e confirme a autorização de contato.','error'); return redirect(url_for('home'))
    if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',data['email']):
        flash('Informe um e-mail válido.','error'); return redirect(url_for('home'))
    try:
        area=float(data['area'].replace('.','').replace(',','.'))
        if area<=0 or area>100000000: raise ValueError()
    except ValueError:
        flash('Informe uma área construída válida.','error'); return redirect(url_for('home'))
    protocolo='MKC-'+datetime.now(timezone.utc).strftime('%Y%m%d')+'-'+secrets.token_hex(3).upper()
    data['protocolo']=protocolo
    with conn() as db:
        cols=['protocolo','criado_em']+FIELDS
        db.execute(f'INSERT INTO solicitacoes ({",".join(cols)}) VALUES ({",".join("?" for _ in cols)})',[protocolo,datetime.now(timezone.utc).isoformat()]+[data[k] for k in FIELDS])
    send_notification(data)
    return render_template('sucesso.html',protocolo=protocolo,telefone=data['telefone'])

def protected(fn):
    @wraps(fn)
    def wrapper(*args,**kwargs):
        if not session.get('admin'): return redirect(url_for('login'))
        return fn(*args,**kwargs)
    return wrapper

@app.route('/admin/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        if not secrets.compare_digest(request.form.get('csrf_token',''),session.get('csrf_token','')): abort(400)
        password=os.environ.get('ADMIN_PASSWORD','')
        if password and secrets.compare_digest(request.form.get('password',''),password):
            session.clear();session['admin']=True;return redirect(url_for('admin'))
        flash('Senha inválida ou acesso administrativo não configurado.','error')
    return render_template('login.html')

@app.get('/admin/logout')
def logout(): session.clear();return redirect(url_for('home'))

@app.get('/admin')
@protected
def admin():
    with conn() as db: items=db.execute('SELECT * FROM solicitacoes ORDER BY id DESC LIMIT 500').fetchall()
    return render_template('admin.html',items=items)

@app.post('/admin/status/<int:item_id>')
@protected
def status(item_id):
    if not secrets.compare_digest(request.form.get('csrf_token',''),session.get('csrf_token','')): abort(400)
    new=request.form.get('status','')
    if new not in ['Recebido','Em análise','Proposta enviada','Concluído']: abort(400)
    with conn() as db: db.execute('UPDATE solicitacoes SET status=? WHERE id=?',(new,item_id))
    return redirect(url_for('admin'))

@app.get('/admin/exportar')
@protected
def exportar():
    with conn() as db: items=db.execute('SELECT * FROM solicitacoes ORDER BY id DESC').fetchall()
    output=io.StringIO();w=csv.writer(output,delimiter=';');cols=['id','protocolo','criado_em','status']+FIELDS;w.writerow(cols)
    for item in items: w.writerow([item[k] for k in cols])
    return Response('\ufeff'+output.getvalue(),mimetype='text/csv; charset=utf-8',headers={'Content-Disposition':'attachment; filename=solicitacoes_mkc.csv'})

@app.context_processor
def inject_csrf():
    if 'csrf_token' not in session: session['csrf_token']=secrets.token_urlsafe(32)
    return {'csrf_token':session['csrf_token']}

if __name__=='__main__': app.run(debug=os.environ.get('FLASK_DEBUG')=='1',port=int(os.environ.get('PORT','5000')))
