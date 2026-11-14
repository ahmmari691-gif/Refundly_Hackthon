"""Local staff accounts and demonstration operations. Never stores renter submissions."""
import base64, hashlib, hmac, json, os, re, secrets, sqlite3, struct, time
from pathlib import Path
from http.cookies import SimpleCookie
from urllib.parse import quote

DB_PATH = Path(os.environ.get('REFUNDLY_DB', str(Path(__file__).parent / '.local' / 'staff.sqlite3')))

def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    c=sqlite3.connect(str(DB_PATH), timeout=20);c.row_factory=sqlite3.Row
    c.execute('PRAGMA foreign_keys=ON')
    return c

def digest(token): return hashlib.sha256(token.encode()).hexdigest()
def pack(value): return json.dumps(value,ensure_ascii=False)
def password_hash(password,salt): return hashlib.pbkdf2_hmac('sha256',password.encode(),bytes.fromhex(salt),600000).hex()
def otp(secret,counter):
    raw=hmac.new(base64.b32decode(secret),struct.pack('>Q',counter),hashlib.sha1).digest();offset=raw[-1]&15
    return str((struct.unpack('>I',raw[offset:offset+4])[0]&0x7fffffff)%1000000).zfill(6)
def verify_otp(secret,code,last=-1):
    counter=int(time.time()//30)
    for n in [counter-1,counter,counter+1]:
        if n>last and hmac.compare_digest(otp(secret,n),str(code)): return n
    return None

def audit(c,actor,action,target,before=None,after=None):
    c.execute('INSERT INTO audit(actor,action,target,before_value,after_value,created) VALUES(?,?,?,?,?,?)',(actor,action,str(target),pack(before),pack(after),int(time.time())))

def create_user(c,email,name,role,password):
    if role not in ['admin','manager'] or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',email) or len(password)<12: raise ValueError('Use a valid email, role, and a password of at least 12 characters.')
    salt=secrets.token_hex(16);secret=base64.b32encode(secrets.token_bytes(20)).decode()
    return c.execute('INSERT INTO users(email,name,role,salt,password,totp) VALUES(?,?,?,?,?,?)',(email.lower(),name[:80],role,salt,password_hash(password,salt),secret)).lastrowid

def initialize(rules):
    with connect() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,email TEXT UNIQUE,name TEXT,role TEXT,salt TEXT,password TEXT,totp TEXT,enrolled INTEGER DEFAULT 0,last_counter INTEGER DEFAULT -1,active INTEGER DEFAULT 1);
        CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY,user_id INTEGER REFERENCES users(id),csrf TEXT,expires INTEGER,kind TEXT);
        CREATE TABLE IF NOT EXISTS attempts(key TEXT PRIMARY KEY,count INTEGER,expires INTEGER);
        CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY,actor TEXT,action TEXT,target TEXT,before_value TEXT,after_value TEXT,created INTEGER);
        CREATE TRIGGER IF NOT EXISTS audit_no_delete BEFORE DELETE ON audit BEGIN SELECT RAISE(ABORT,'Audit records are append-only'); END;
        CREATE TRIGGER IF NOT EXISTS audit_no_update BEFORE UPDATE ON audit BEGIN SELECT RAISE(ABORT,'Audit records are append-only'); END;
        CREATE TABLE IF NOT EXISTS config(key TEXT PRIMARY KEY,value TEXT);
        CREATE TABLE IF NOT EXISTS rule_versions(id INTEGER PRIMARY KEY,state TEXT,data TEXT,status TEXT,created INTEGER,actor TEXT);
        CREATE TABLE IF NOT EXISTS tickets(id INTEGER PRIMARY KEY,name TEXT,email TEXT,state TEXT,subject TEXT,kind TEXT,status TEXT,assignee INTEGER,created INTEGER,data TEXT,messages TEXT,qc TEXT DEFAULT 'pending',refund_cents INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS templates(id INTEGER PRIMARY KEY,title TEXT,body TEXT,status TEXT,author TEXT);
        ''')
        for key,value in {'price_cents':1900,'payments_enabled':True,'headline':'Your deposit.','headline_em':'Your right to clarity.','announcement':'Demo workspace: all cases and payments here are synthetic.','maintenance':False}.items():
            c.execute('INSERT OR IGNORE INTO config VALUES(?,?)',(key,pack(value)))
        for state,rule in rules.items():
            if not c.execute('SELECT 1 FROM rule_versions WHERE state=?',(state,)).fetchone():
                c.execute('INSERT INTO rule_versions(state,data,status,created,actor) VALUES(?,?,?,?,?)',(state,pack({**rule,'enabled':True,'reviewed':'2026-11-14'}),'published',int(time.time()),'system'))
        if not c.execute('SELECT 1 FROM users').fetchone() and os.environ.get('REFUNDLY_HOSTED') == '1':
            email=os.environ.get('REFUNDLY_ADMIN_EMAIL', '').strip()
            password=os.environ.get('REFUNDLY_ADMIN_PASSWORD', '')
            if not email or len(password)<16:
                raise RuntimeError('Set REFUNDLY_ADMIN_EMAIL and REFUNDLY_ADMIN_PASSWORD (at least 16 characters).')
            create_user(c,email,'Administrator','admin',password)
        if not c.execute('SELECT 1 FROM users').fetchone():
            access=['REFUNDLY — LOCAL DEMO STAFF ACCOUNTS','Open http://127.0.0.1:8000/staff.html','First sign-in: add the displayed setup key to an authenticator app, then enter its 6-digit code.','These passwords are local to this computer. This file is not included in source archives.','']
            for email,name,role in [('admin@refundly.demo','Demo Administrator','admin'),('manager@refundly.demo','Demo Manager','manager')]:
                password=secrets.token_urlsafe(18);create_user(c,email,name,role,password)
                access.extend([role.upper(),email,'Password: '+password,''])
            access_path=DB_PATH.parent/'staff-access.txt';access_path.write_text('\n'.join(access));access_path.chmod(0o600)
        if not c.execute('SELECT 1 FROM tickets').fetchone():
            for i,(name,state,subject,kind,status,amount,age) in enumerate([('Alex Example','CA','Question about a repainting charge','question','new',650,2),('Jordan Sample','NY','Please review my letter','quality','open',420,36),('Taylor Demo','TX','Request a refund of the demo order','refund','new',900,28)],1):
                data={'demo':True,'case_id':f'DEMO-{1000+i}','deposit':2200,'disputed':amount,'payment_id':f'demo_pay_{i}','paid_cents':1900,'letter':'DEMO LETTER — illustrative record only.\nPlease review the disputed deduction and provide documentation. This is synthetic test data.','deductions':[{'kind':'Painting','amount':amount,'status':'Questionable'}]}
                c.execute('INSERT INTO tickets VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',(i,name,name.lower().split()[0]+'@example.test',state,subject,kind,status,None,int(time.time())-age*3600,pack(data),pack([{'author':name,'body':'This is a synthetic support request for trying the manager workspace.','internal':False,'created':int(time.time())-age*3600}]),'pending',0))
            for title,body in [('Request evidence','Hi {name}, please keep your lease, itemization, move-in photos, and delivery records for case {case_id} in {state}.'),('Refund information','Hi {name}, we have reviewed the request for case {case_id}. This demonstration does not process real payments.')]:
                c.execute('INSERT INTO templates(title,body,status,author) VALUES(?,?,?,?)',(title,body,'published','system'))
    DB_PATH.chmod(0o600)

def rules_snapshot(fallback):
    if not DB_PATH.exists(): return fallback
    with connect() as c:
        rows=c.execute("SELECT state,data FROM rule_versions WHERE status='published' ORDER BY id").fetchall()
    result={}
    for row in rows: result[row['state']]=json.loads(row['data'])
    return {k:v for k,v in result.items() if v.get('enabled',True)} or {}

def configuration():
    with connect() as c:return {r['key']:json.loads(r['value']) for r in c.execute('SELECT * FROM config')}

def current_session(handler):
    cookie=SimpleCookie()
    try:cookie.load(handler.headers.get('Cookie',''));raw=cookie['refundly_staff'].value
    except (KeyError,ValueError):return None
    with connect() as c:
        row=c.execute("SELECT users.id,users.email,users.name,users.role,sessions.csrf FROM sessions JOIN users ON user_id=users.id WHERE token=? AND expires>? AND kind='session' AND active=1",(digest(raw),int(time.time()))).fetchone()
    return dict(row) if row else None

def session_response(handler,c,user):
    token=secrets.token_urlsafe(32);csrf=secrets.token_urlsafe(32)
    c.execute('DELETE FROM sessions WHERE expires<?',(int(time.time()),))
    c.execute('INSERT INTO sessions VALUES(?,?,?,?,?)',(digest(token),user['id'],csrf,int(time.time())+8*3600,'session'))
    audit(c,user['email'],'sign_in','session')
    handler.extra_headers={'Set-Cookie':f'refundly_staff={token}; Path=/; HttpOnly; SameSite=Strict; Max-Age=28800' + ('; Secure' if os.environ.get('REFUNDLY_HOSTED') == '1' else '')}
    return {'user':{k:user[k] for k in ['id','email','name','role']},'csrf':csrf}

def login(handler,d):
    email=str(d.get('email','')).strip().lower();key=digest(email+'|'+handler.client_address[0]);now=int(time.time())
    with connect() as c:
        c.execute('BEGIN IMMEDIATE')
        attempt=c.execute('SELECT * FROM attempts WHERE key=?',(key,)).fetchone()
        if attempt and attempt['expires']>now and attempt['count']>=8: return 429,{'error':'Too many attempts. Try again in 15 minutes.'}
        c.execute('INSERT INTO attempts VALUES(?,?,?) ON CONFLICT(key) DO UPDATE SET count=CASE WHEN expires<? THEN 1 ELSE count+1 END,expires=CASE WHEN expires<? THEN ? ELSE expires END',(key,1,now+900,now,now,now+900))
        user=c.execute('SELECT * FROM users WHERE email=?',(email,)).fetchone()
        check=password_hash(str(d.get('password',''))[:1024],user['salt'] if user else '00'*16)
        if not user or not user['active'] or not hmac.compare_digest(check,user['password']):return 401,{'error':'Invalid sign-in details.'}
        if not user['enrolled']:
            token=secrets.token_urlsafe(32)
            c.execute("DELETE FROM sessions WHERE user_id=? AND kind='enroll'",(user['id'],))
            c.execute('INSERT INTO sessions VALUES(?,?,?,?,?)',(digest(token),user['id'],'',now+600,'enroll'))
            return 200,{'enrollment':token,'secret':user['totp'],'uri':f'otpauth://totp/Refundly:{quote(email)}?secret={user["totp"]}&issuer=Refundly','message':'Add this setup key to your authenticator. Then enter its current six-digit code.'}
        counter=verify_otp(user['totp'],d.get('code',''),user['last_counter'])
        if counter is None:return 401,{'error':'Enter a fresh authenticator code. Codes cannot be reused.'}
        changed=c.execute('UPDATE users SET last_counter=? WHERE id=? AND last_counter<?',(counter,user['id'],counter)).rowcount
        if not changed:return 401,{'error':'This code has already been used.'}
        c.execute('DELETE FROM attempts WHERE key=?',(key,));return 200,session_response(handler,c,user)

def enroll(handler,d):
    with connect() as c:
        c.execute('BEGIN IMMEDIATE')
        user=c.execute("SELECT users.* FROM sessions JOIN users ON user_id=users.id WHERE token=? AND expires>? AND kind='enroll' AND enrolled=0 AND active=1",(digest(str(d.get('enrollment',''))),int(time.time()))).fetchone()
        if not user:return 401,{'error':'Setup expired. Sign in again.'}
        key='enroll:'+str(user['id']);now=int(time.time());attempt=c.execute('SELECT * FROM attempts WHERE key=?',(key,)).fetchone()
        if attempt and attempt['count']>=8 and attempt['expires']>now:return 429,{'error':'Too many setup attempts. Try again later.'}
        c.execute('INSERT INTO attempts VALUES(?,?,?) ON CONFLICT(key) DO UPDATE SET count=CASE WHEN expires<? THEN 1 ELSE count+1 END,expires=?',(key,1,now+900,now,now+900))
        counter=verify_otp(user['totp'],d.get('code',''))
        if counter is None:return 401,{'error':'The authenticator code is incorrect.'}
        c.execute('UPDATE users SET enrolled=1,last_counter=? WHERE id=?',(counter,user['id']));c.execute("DELETE FROM sessions WHERE user_id=? AND kind='enroll'",(user['id'],))
        audit(c,user['email'],'enable_2fa',user['id']);return 200,session_response(handler,c,user)

def get_data(user):
    with connect() as c:
        tickets=[]
        for row in c.execute('SELECT * FROM tickets ORDER BY created DESC'):
            item=dict(row);item['data']=json.loads(item['data']);item['messages']=json.loads(item['messages']);item['email']=item['email'][0]+'***@example.test';tickets.append(item)
        team=[dict(r) for r in c.execute('SELECT id,name,email,role,active,enrolled FROM users')]
        result={'user':{k:user[k] for k in ['id','email','name','role']},'tickets':tickets,'templates':[dict(r) for r in c.execute("SELECT * FROM templates WHERE status='published' OR author=? OR ?='admin'",(user['email'],user['role']))],'team':[{'id':r['id'],'name':r['name'],'active':r['active']} for r in team],'announcement':configuration()['announcement']}
        if user['role']=='admin':
            result.update(team=team,config=configuration(),rules=[{**dict(r),'data':json.loads(r['data'])} for r in c.execute('SELECT * FROM rule_versions ORDER BY id DESC')],audit=[dict(r) for r in c.execute('SELECT * FROM audit ORDER BY id DESC LIMIT 300')])
        return result

def modify(user,d):
    action=d.get('action');actor=user['email'];admin=user['role']=='admin'
    with connect() as c:
        c.execute('BEGIN IMMEDIATE')
        if action in ['team_create','team_update','config','rule_save','rule_publish','rule_restore','template_publish'] and not admin:return 403,{'error':'Administrator access required.'}
        if action=='team_create':
            password=secrets.token_urlsafe(18)
            uid=create_user(c,str(d.get('email','')).strip(),str(d.get('name','Staff member')),d.get('role'),password)
            audit(c,actor,'team_create',uid,None,{'email':d['email'],'role':d['role']})
            return 200,{'message':'Account created. Share the temporary password privately; 2FA setup is required at first sign-in. No email was sent.','password':password}
        if action=='team_update':
            uid=int(d['id']);before=c.execute('SELECT id,role,active FROM users WHERE id=?',(uid,)).fetchone()
            if not before:raise ValueError('Employee not found.')
            if uid==user['id']:raise ValueError('Use another administrator to change your own access.')
            role=d.get('role',before['role']);active=int(bool(d.get('active',before['active'])))
            if role not in ['admin','manager']:raise ValueError('Invalid role.')
            c.execute('UPDATE users SET role=?,active=? WHERE id=?',(role,active,uid));c.execute('DELETE FROM sessions WHERE user_id=?',(uid,));audit(c,actor,'team_update',uid,dict(before),{'role':role,'active':active})
        elif action=='config':
            changes=d.get('values',{})
            if not isinstance(changes,dict):raise ValueError('Invalid settings.')
            allowed={'price_cents','payments_enabled','headline','headline_em','announcement','maintenance'}
            if not set(changes)<=allowed:raise ValueError('Unsupported setting.')
            for key,value in changes.items():
                if key=='price_cents' and (type(value)!=int or not 0<=value<=100000):raise ValueError('Price must be between 0 and 100000 cents.')
                if key in ['payments_enabled','maintenance'] and type(value)!=bool:raise ValueError('Expected an on/off value.')
                if key in ['headline','headline_em','announcement'] and (not isinstance(value,str) or not 1<=len(value)<=500):raise ValueError('Text must contain 1–500 characters.')
                before=json.loads(c.execute('SELECT value FROM config WHERE key=?',(key,)).fetchone()[0]);c.execute('UPDATE config SET value=? WHERE key=?',(pack(value),key));audit(c,actor,'config',key,before,value)
        elif action=='rule_save':
            state=d.get('state');rule=d.get('data')
            if state not in ['CA','NY','TX','FL','IL'] or not isinstance(rule,dict):raise ValueError('Choose one of the five supported states.')
            if type(rule.get('days'))!=int or not 1<=rule['days']<=365:raise ValueError('Deadline must be 1–365 days.')
            for key in ['name','law','url','note','remedy','reviewed']:
                if not isinstance(rule.get(key),str) or not 1<=len(rule[key])<=3000:raise ValueError('Fill all rule fields.')
            if not rule['url'].startswith('https://'):raise ValueError('Use an HTTPS official source.')
            if type(rule.get('enabled'))!=bool:raise ValueError('Choose whether the state is enabled.')
            from datetime import date
            date.fromisoformat(rule['reviewed'])
            rid=c.execute('INSERT INTO rule_versions(state,data,status,created,actor) VALUES(?,?,?,?,?)',(state,pack(rule),'draft',int(time.time()),actor)).lastrowid;audit(c,actor,'rule_draft',rid,None,rule)
        elif action in ['rule_publish','rule_restore']:
            version=c.execute('SELECT * FROM rule_versions WHERE id=?',(int(d['id']),)).fetchone()
            if not version:raise ValueError('Version not found.')
            if action=='rule_publish' and version['status']!='draft':raise ValueError('Only drafts can be published.')
            current=c.execute("SELECT * FROM rule_versions WHERE state=? AND status='published'",(version['state'],)).fetchone()
            if not json.loads(version['data']).get('enabled',True) and c.execute("SELECT COUNT(*) FROM rule_versions WHERE status='published' AND json_extract(data,'$.enabled')=1").fetchone()[0]<=1:raise ValueError('Keep at least one state enabled.')
            c.execute("UPDATE rule_versions SET status='archived' WHERE state=? AND status='published'",(version['state'],))
            if action=='rule_restore':c.execute('INSERT INTO rule_versions(state,data,status,created,actor) VALUES(?,?,?,?,?)',(version['state'],version['data'],'published',int(time.time()),actor))
            else:c.execute("UPDATE rule_versions SET status='published' WHERE id=?",(version['id'],))
            audit(c,actor,action,version['state'],json.loads(current['data']) if current else None,json.loads(version['data']))
        elif action in ['ticket','message','refund','quality']:
            row=c.execute('SELECT * FROM tickets WHERE id=?',(int(d['id']),)).fetchone()
            if not row:raise ValueError('Demo ticket not found.')
            if action=='ticket':
                status=d.get('status',row['status']);assignee=d.get('assignee',row['assignee'])
                if status not in ['new','open','waiting','resolved','escalated']:raise ValueError('Invalid status.')
                if assignee is not None and not c.execute('SELECT 1 FROM users WHERE id=? AND active=1',(int(assignee),)).fetchone():raise ValueError('Assignee not found.')
                c.execute('UPDATE tickets SET status=?,assignee=? WHERE id=?',(status,assignee,row['id']));audit(c,actor,'ticket_update',row['id'],{'status':row['status'],'assignee':row['assignee']},{'status':status,'assignee':assignee})
            elif action=='message':
                text=str(d.get('body','')).strip()
                if not 1<=len(text)<=5000:raise ValueError('Message must contain 1–5000 characters.')
                messages=json.loads(row['messages']);messages.append({'author':user['name'],'body':text,'internal':bool(d.get('internal')),'created':int(time.time())});c.execute('UPDATE tickets SET messages=? WHERE id=?',(pack(messages),row['id']));audit(c,actor,'internal_note' if d.get('internal') else 'demo_reply',row['id'],None,{'body':text})
            elif action=='quality':
                status=d.get('status')
                if status not in ['passed','wrong_amount','wrong_law','other']:raise ValueError('Choose a review outcome.')
                c.execute('UPDATE tickets SET qc=?,status=? WHERE id=?',(status,'escalated' if status!='passed' else row['status'],row['id']));audit(c,actor,'quality_review',row['id'],row['qc'],status)
            else:
                paid=json.loads(row['data'])['paid_cents'];amount=d.get('amount_cents');comment=str(d.get('comment','')).strip();reason=d.get('reason')
                if type(amount)!=int or amount<=0 or amount>paid-row['refund_cents']:raise ValueError('Refund cannot exceed the remaining paid amount.')
                if not admin and (row['refund_cents'] or amount!=paid):return 403,{'error':'Managers may issue one full demo refund only.'}
                if reason not in ['Letter unsuitable','Service error','Duplicate payment','Other'] or not comment:raise ValueError('Choose a reason and add a comment.')
                c.execute('UPDATE tickets SET refund_cents=refund_cents+? WHERE id=?',(amount,row['id']));audit(c,actor,'demo_refund',row['id'],row['refund_cents'],{'total':row['refund_cents']+amount,'reason':reason,'comment':comment[:3000]})
        elif action=='template_propose':
            title=str(d.get('title','')).strip();body=str(d.get('body','')).strip()
            if not title or not body or len(body)>5000:raise ValueError('Provide a title and a template of up to 5000 characters.')
            tid=c.execute('INSERT INTO templates(title,body,status,author) VALUES(?,?,?,?)',(title[:150],body,'draft',actor)).lastrowid;audit(c,actor,'template_propose',tid,None,{'title':title,'body':body})
        elif action=='template_publish':
            row=c.execute('SELECT * FROM templates WHERE id=?',(int(d['id']),)).fetchone()
            if not row:raise ValueError('Template not found.')
            c.execute("UPDATE templates SET status='published' WHERE id=?",(row['id'],));audit(c,actor,'template_publish',row['id'],'draft','published')
        else:raise ValueError('Unknown action.')
    return 200,{'message':'Saved.'}

def handle(handler,method,d=None):
    path=handler.path
    if not path.startswith('/api/staff/'):return False
    try:
        if method=='POST':
            expected=(os.environ.get('PUBLIC_BASE_URL') or os.environ.get('RENDER_EXTERNAL_URL') or f'http://{handler.headers.get("Host", "")}').rstrip('/')
            if handler.headers.get('Origin')!=expected or not handler.headers.get('Content-Type','').startswith('application/json'):
                handler.respond(403,{'error':'Same-origin JSON requests are required.'});return True
        if path=='/api/staff/login' and method=='POST':status,result=login(handler,d)
        elif path=='/api/staff/enroll' and method=='POST':status,result=enroll(handler,d)
        else:
            user=current_session(handler)
            if not user:handler.respond(401,{'error':'Please sign in.'});return True
            if method=='POST' and not hmac.compare_digest(handler.headers.get('X-CSRF-Token',''),user['csrf']):handler.respond(403,{'error':'Invalid session token.'});return True
            if path=='/api/staff/me' and method=='GET':status,result=200,{'user':user,'csrf':user['csrf']}
            elif path=='/api/staff/data' and method=='GET':status,result=200,get_data(user)
            elif path=='/api/staff/action' and method=='POST':status,result=modify(user,d)
            elif path=='/api/staff/logout' and method=='POST':
                with connect() as c:c.execute('DELETE FROM sessions WHERE user_id=?',(user['id'],));audit(c,user['email'],'sign_out','all_sessions')
                handler.extra_headers={'Set-Cookie':'refundly_staff=; Path=/; HttpOnly; SameSite=Strict; Max-Age=0' + ('; Secure' if os.environ.get('REFUNDLY_HOSTED') == '1' else '')};status,result=200,{'message':'Signed out.'}
            else:status,result=404,{'error':'Not found.'}
        handler.respond(status,result)
    except (ValueError,TypeError,KeyError,sqlite3.IntegrityError) as e:handler.respond(400,{'error':str(e)})
    return True
