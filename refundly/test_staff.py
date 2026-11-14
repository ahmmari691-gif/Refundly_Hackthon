import base64, json, shutil, tempfile, time, unittest
from pathlib import Path
import staff
from app import RULES, analyze
class Fake:
    def __init__(self,path='',headers=None):
        self.path=path;self.headers=headers or {};self.client_address=('127.0.0.1',1);self.result=None
    def respond(self,status,data):self.result=(status,data)
class StaffTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original=staff.DB_PATH;cls.temp=tempfile.TemporaryDirectory();cls.base=Path(cls.temp.name)/'seed.sqlite';staff.DB_PATH=cls.base;staff.initialize(RULES)
    @classmethod
    def tearDownClass(cls):staff.DB_PATH=cls.original;cls.temp.cleanup()
    def setUp(self):
        self.db=Path(self.temp.name)/'test.sqlite';shutil.copyfile(self.base,self.db);staff.DB_PATH=self.db
        with staff.connect() as c:self.admin=dict(c.execute("SELECT * FROM users WHERE role='admin'").fetchone());self.manager=dict(c.execute("SELECT * FROM users WHERE role='manager'").fetchone())
    def test_totp_rfc_vector(self):
        secret=base64.b32encode(b'12345678901234567890').decode();self.assertEqual(staff.otp(secret,59//30),'287082')
    def test_anonymous_denied(self):
        h=Fake('/api/staff/data');staff.handle(h,'GET');self.assertEqual(h.result[0],401)
    def test_manager_cannot_modify_admin_settings(self):
        for action in ['config','team_create','rule_publish','rule_restore','template_publish']:
            code,_=staff.modify(self.manager,{'action':action});self.assertEqual(code,403)
    def test_manager_payload_has_no_rules_or_audit_or_secrets(self):
        d=staff.get_data(self.manager);self.assertNotIn('rules',d);self.assertNotIn('audit',d);self.assertNotIn('config',d)
        self.assertNotIn('totp',json.dumps(d));self.assertNotIn('password',json.dumps(d))
    def test_manager_refund_once_and_full(self):
        code,_=staff.modify(self.manager,{'action':'refund','id':1,'amount_cents':100,'reason':'Other','comment':'Demo'});self.assertEqual(code,403)
        code,_=staff.modify(self.manager,{'action':'refund','id':1,'amount_cents':1900,'reason':'Other','comment':'Demo'});self.assertEqual(code,200)
        with self.assertRaises(ValueError):staff.modify(self.manager,{'action':'refund','id':1,'amount_cents':1900,'reason':'Other','comment':'Demo'})
    def test_admin_partial_refund_bound(self):
        staff.modify(self.admin,{'action':'refund','id':1,'amount_cents':500,'reason':'Other','comment':'Demo'})
        with self.assertRaises(ValueError):staff.modify(self.admin,{'action':'refund','id':1,'amount_cents':1500,'reason':'Other','comment':'Demo'})
    def test_append_only_audit(self):
        staff.modify(self.manager,{'action':'ticket','id':1,'status':'open'})
        with staff.connect() as c:
            with self.assertRaises(Exception):c.execute('DELETE FROM audit')
    def test_internal_note_and_assignee(self):
        staff.modify(self.manager,{'action':'message','id':1,'body':'Private synthetic note','internal':True})
        staff.modify(self.manager,{'action':'ticket','id':1,'assignee':self.manager['id']})
        t=next(t for t in staff.get_data(self.manager)['tickets'] if t['id']==1);self.assertTrue(t['messages'][-1]['internal']);self.assertEqual(t['assignee'],self.manager['id'])
    def test_draft_publish_restore_affects_engine(self):
        new={**RULES['CA'],'days':25,'enabled':True,'reviewed':'2026-11-14'}
        staff.modify(self.admin,{'action':'rule_save','state':'CA','data':new});self.assertEqual(staff.rules_snapshot(RULES)['CA']['days'],21)
        with staff.connect() as c:rid=c.execute("SELECT max(id) FROM rule_versions WHERE state='CA'").fetchone()[0]
        staff.modify(self.admin,{'action':'rule_publish','id':rid});self.assertEqual(staff.rules_snapshot(RULES)['CA']['days'],25)
        staff.modify(self.admin,{'action':'rule_restore','id':1});self.assertEqual(staff.rules_snapshot(RULES)['CA']['days'],21)
    def test_session_revoked_on_disable(self):
        h=Fake()
        with staff.connect() as c:staff.session_response(h,c,self.manager)
        cookie=h.extra_headers['Set-Cookie'].split(';')[0];self.assertIsNotNone(staff.current_session(Fake(headers={'Cookie':cookie})))
        staff.modify(self.admin,{'action':'team_update','id':self.manager['id'],'active':False});self.assertIsNone(staff.current_session(Fake(headers={'Cookie':cookie})))
    def test_csrf_and_cross_origin(self):
        h=Fake('/api/staff/action',{'Origin':'https://evil.example','Host':'127.0.0.1:8000','Content-Type':'application/json'});staff.handle(h,'POST',{'action':'config'});self.assertEqual(h.result[0],403)
        h=Fake()
        with staff.connect() as c:staff.session_response(h,c,self.admin)
        cookie=h.extra_headers['Set-Cookie'].split(';')[0]
        h=Fake('/api/staff/action',{'Origin':'http://127.0.0.1:8000','Host':'127.0.0.1:8000','Content-Type':'application/json','Cookie':cookie});staff.handle(h,'POST',{'action':'config'});self.assertEqual(h.result[0],403)
    def test_otp_replay(self):
        counter=int(time.time()//30);code=staff.otp(self.admin['totp'],counter)
        self.assertEqual(staff.verify_otp(self.admin['totp'],code),counter);self.assertIsNone(staff.verify_otp(self.admin['totp'],code,counter))
    def test_last_self_access_protection(self):
        with self.assertRaises(ValueError):staff.modify(self.admin,{'action':'team_update','id':self.admin['id'],'active':False})
    def test_demo_fixture_no_real_case_data(self):
        for t in staff.get_data(self.admin)['tickets']:self.assertTrue(t['data']['demo']);self.assertTrue(t['email'].endswith('@example.test'))
if __name__=='__main__':unittest.main()
