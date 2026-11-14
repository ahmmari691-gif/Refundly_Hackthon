"""Local Refundly demo. Python 3.9+, standard library only."""
import argparse
import json
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
ROOT = Path(__file__).resolve().parent
RULES = {
'CA': dict(name='California', days=21, law='California Civil Code § 1950.5', url='https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=CIV&sectionNum=1950.5.', note='Generally 21 days to account for the deposit and return the balance. Receipt, estimate, and photo requirements and exceptions need review.', remedy='Bad-faith retention may support additional damages up to twice the deposit. A court decides; this is not automatic.'),
'NY': dict(name='New York', days=14, law='N.Y. General Obligations Law § 7-108', url='https://www.nysenate.gov/legislation/laws/GOB/7-108', note='Covered tenancies: itemization and balance within 14 days. Rent-regulated and other excluded housing need separate review.', remedy='Willful violations may support punitive damages up to twice the deposit, in addition to actual damages.'),
'TX': dict(name='Texas', days=30, law='Texas Property Code §§ 92.103–92.109', url='https://statutes.capitol.texas.gov/Docs/PR/htm/PR.92.htm#92.103', note='Generally 30 days after surrender. A written forwarding address is required before the refund duty applies. Unpaid-rent exceptions affect itemization.', remedy='Bad-faith retention may support $100 plus three times the amount wrongfully withheld and reasonable attorney fees.'),
'FL': dict(name='Florida', days=30, law='Florida Statutes § 83.49', url='https://www.leg.state.fl.us/statutes/index.cfm?App_mode=Display_Statute&URL=0000-0099/0083/Sections/0083.49.html', note='15 days for return with no claim; 30 days for compliant claim notice after termination. Object within 15 days of receipt. Early departure and notice exceptions need review.', remedy='No automatic damages multiplier. Late notice can forfeit use of the deposit, without eliminating a separate damages claim. Court costs and attorney fees may apply.'),
'IL': dict(name='Illinois', days=30, law='765 ILCS 710/1', url='https://www.ilga.gov/Legislation/ILCS/Articles?ActID=2202&Chapter=PROPERTY&ChapterID=62&MajorTopic=RIGHTS+AND+REMEDIES', note='Damage itemization generally within 30 days of vacancy or end of possession, whichever is later. Without required documentation, full return within 45 days. Receipt exceptions and local rules may apply.', remedy='Specified refusal or bad-faith failures may support liability equal to twice the deposit due, plus court costs and reasonable attorney fees.')}

def money(value):
    try:
        n=Decimal(str(value))
        if not n.is_finite() or n<0 or n>1000000 or n!=n.quantize(Decimal('.01')): raise ValueError()
        return n
    except (InvalidOperation,ValueError): raise ValueError('Enter a non-negative amount with at most two decimal places.')

def day(value):
    try: return date.fromisoformat(value)
    except (TypeError,ValueError): raise ValueError('Enter valid dates.')

def analyze(d):
    if not isinstance(d,dict) or d.get('state') not in RULES: raise ValueError('Select a supported state.')
    rule=RULES[d['state']]; start,end=day(d.get('move_in')),day(d.get('move_out'))
    if start>end or end>date.today(): raise ValueError('Move-out must follow move-in and cannot be in the future.')
    deposit,returned=money(d.get('deposit')),money(d.get('returned',0))
    if not deposit or returned>deposit: raise ValueError('Check the deposit and returned amounts.')
    received=day(d['received']) if d.get('received') else None
    if received and (received<end or received>date.today()): raise ValueError('Notice receipt must be between move-out and today.')
    rows=d.get('deductions',[])
    if not isinstance(rows,list) or len(rows)>50: raise ValueError('Use at most 50 deductions.')
    results=[]; total=Decimal(0)
    for r in rows:
        amount=money(r.get('amount')); kind=r.get('kind'); condition=r.get('condition')
        if not amount: raise ValueError('Each deduction must be greater than zero.')
        if kind not in ['Painting','Carpet','Cleaning','Repair','Unpaid rent','Other']: raise ValueError('Invalid deduction type.')
        if condition not in ['wear','preexisting','damage','unknown']: raise ValueError('Invalid condition.')
        age=r.get('age','')
        if age!='' and (not str(age).isdigit() or not 0<=int(age)<=100): raise ValueError('Age must be 0–100 whole years.')
        total+=amount; status='Questionable'; reason='Request evidence of tenant responsibility and reasonable cost.'
        if condition in ['wear','preexisting'] and kind!='Unpaid rent':
            status='Likely unlawful' if d['state'] in ['CA','NY','TX'] else 'Questionable'
            reason='You reported ordinary wear or a pre-existing condition. Ask for evidence that this charge relates to damage you caused.'
        elif condition=='damage' and r.get('receipt') and kind not in ['Painting','Carpet']:
            status='Likely lawful'; reason='You reported tenant-caused damage with cost documentation. Reasonableness and procedural compliance still matter.'
        if kind in ['Painting','Carpet'] and age!='': reason+=f' The item was {age} years old. Request its installation history and allowance for prior use; no statutory useful life is assumed.'
        if r.get('photo'): reason+=' Keep your move-in photos as evidence.'
        results.append(dict(kind=kind,amount=float(amount),status=status,reason=reason,description=str(r.get('description',''))[:500]))
    held=deposit-returned
    if total>held: raise ValueError('Deductions cannot exceed the deposit still withheld.')
    deadline=end+timedelta(days=rule['days'])
    procedure='Check dispatch date and delivery method; receipt alone does not establish late dispatch.'
    if not d.get('itemized'): procedure+=' No itemized statement reported: request one and check exceptions.'
    if (received and received>deadline) or (not received and date.today()>deadline): procedure+=' A timing issue may exist.'
    if d['state']=='CA' and total>125 and any(not r.get('receipt') for r in rows): procedure+=' Check missing receipts, permitted estimates, and documentation exceptions.'
    uncertain=d['state']=='TX' and not d.get('forwarding')
    if uncertain: procedure='Texas deadline needs individual review: confirm when the written forwarding address was provided.'
    return dict(rule=rule,rows=results,disputed=float(sum(Decimal(str(r['amount'])) for r in results if r['status']!='Likely lawful')),withheld=float(held),unaccounted=float(held-total),deadline=None if uncertain else str(deadline),procedure=procedure,objection_deadline=str(received+timedelta(days=15)) if d['state']=='FL' and received else None)

def letter(d,r):
    disputed=[x for x in r['rows'] if x['status']!='Likely lawful']
    if not disputed and not r['unaccounted']: raise ValueError('No disputed deductions or unexplained amounts to include.')
    field=lambda k,default:str(d.get(k) or default)[:500]
    lines=[str(date.today()),'',field('tenant','[Your name]'),field('forward_address','[Your forwarding address]'),'','To: '+field('landlord','[Landlord name and address]'),'',('Follow-up: ' if d.get('followup') else '')+'Request for security deposit review','Property: '+field('property','[Rental address]'),'','Dear '+field('landlord','[Landlord]')+',','',f'I vacated the property on {d["move_out"]}. My security deposit was ${float(money(d["deposit"])):,.2f}. I dispute the following charges and request review:']
    for x in disputed:
        explanation=x['reason'].replace('You reported', 'I reported').replace('Ask for evidence that this charge relates to damage you caused.', 'Please provide evidence that this charge relates to damage I caused.').replace('Request evidence of tenant responsibility and reasonable cost.', 'Please provide evidence of my responsibility and the reasonable cost.').replace('Request its installation history and allowance for prior use; no statutory useful life is assumed.', 'Please provide its installation history and explain any allowance for prior use.').replace('Keep your move-in photos as evidence.', 'I have move-in photographs for comparison.')
        lines.append(f'• {x["kind"]}: ${x["amount"]:,.2f}. {x["description"]} {explanation}')
    if r['unaccounted']: lines.append(f'• Please account for the additional ${r["unaccounted"]:,.2f} withheld without listed deductions.')
    lines+=['',f'Please return any improperly withheld amount and provide supporting documentation under {r["rule"]["law"]}.',r['rule']['url'],'','Please respond in writing within 14 days of this letter. This is my requested response period, not a statutory deadline. Please send your response and any refund to my forwarding address.','','Sincerely,',field('tenant','[Your name]')]
    return '\n'.join(lines)

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*a,**kw): super().__init__(*a,directory=str(ROOT/'static'),**kw)
    def end_headers(self):
        self.send_header('Cache-Control','no-store'); self.send_header('X-Content-Type-Options','nosniff'); super().end_headers()
    def respond(self,status,data):
        raw=json.dumps(data).encode(); self.send_response(status); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(raw))); self.end_headers(); self.wfile.write(raw)
    def do_GET(self):
        if self.path=='/api/rules': return self.respond(200,RULES)
        if self.path=='/health': return self.respond(200,{'ok':True})
        return super().do_GET()
    def do_POST(self):
        if self.path not in ['/api/analyze','/api/letter']: return self.respond(404,{'error':'Not found'})
        try:
            size=int(self.headers.get('Content-Length',0))
            if not 0<size<=100000: raise ValueError('Invalid request size.')
            d=json.loads(self.rfile.read(size)); r=analyze(d)
            self.respond(200,{'letter':letter(d,r)} if self.path=='/api/letter' else r)
        except (ValueError,TypeError,AttributeError,KeyError) as e: self.respond(400,{'error':str(e) or 'Invalid input.'})
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--port',type=int,default=8000); a=p.parse_args()
    print(f'Refundly: http://127.0.0.1:{a.port}',flush=True)
    ThreadingHTTPServer(('127.0.0.1',a.port),Handler).serve_forever()
