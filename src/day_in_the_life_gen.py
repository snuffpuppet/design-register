W,H=1720,1250
C={'OI':('#e8f1fb','#1f5fa8'),'REQ':('#fff8e6','#c77d00'),'DEC':('#eef7ea','#3a7d2c'),'LIM':('#fdecec','#b83232'),'CR':('#e6f4f6','#1a7f8e'),'RSK':('#f3eefb','#6a3fa0'),'TRG':('#f3f3f3','#777')}
out=[]
def esc(s): return s.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
def wrap(t,n):
    words=t.split(); lines=[]; cur=''
    for w in words:
        if len(cur)+len(w)+1>n and cur: lines.append(cur); cur=w
        else: cur=(cur+' '+w).strip()
    if cur: lines.append(cur)
    return lines[:3]
NW,NH,PITCH=155,62,177
X0=290
def node(col,row_y,t,title,sub):
    x=X0+col*PITCH; y=row_y
    f,s=C[t]
    dash=' stroke-dasharray="5,3"' if t=='OI' else ''
    out.append(f'<rect x="{x}" y="{y}" width="{NW}" height="{NH}" rx="7" fill="{f}" stroke="{s}" stroke-width="1.6"{dash}/>')
    out.append(f'<text x="{x+NW/2}" y="{y+17}" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#222">{esc(title)}</text>')
    for i,l in enumerate(wrap(sub,28)):
        out.append(f'<text x="{x+NW/2}" y="{y+31+i*12}" text-anchor="middle" font-size="9.8" fill="#444">{esc(l)}</text>')
def arrow(c1,y1,c2,y2,color='#444',dash=False):
    x1=X0+c1*PITCH+NW; x2=X0+c2*PITCH
    da=' stroke-dasharray="5,3"' if dash else ''
    if y1==y2: d=f'M{x1},{y1+NH/2} L{x2},{y2+NH/2}'
    else:
        mx=(x1+x2)/2
        d=f'M{x1},{y1+NH/2} C{mx},{y1+NH/2} {mx},{y2+NH/2} {x2},{y2+NH/2}'
    out.append(f'<path d="{d}" stroke="{color}" stroke-width="1.5" fill="none"{da} marker-end="url(#arr)"/>')
def chain(row_y,steps,start=0):
    for i,(t,title,sub) in enumerate(steps):
        node(start+i,row_y,t,title,sub)
        if i>0: arrow(start+i-1,row_y,start+i,row_y)
def band(y,h,title,sub,color):
    out.append(f'<rect x="20" y="{y}" width="{W-40}" height="{h}" rx="8" fill="{color}" fill-opacity="0.18" stroke="none"/>')
    out.append(f'<text x="36" y="{y+24}" font-size="13" font-weight="bold" fill="#222">{esc(title)}</text>')
    yy=y+42
    for l in wrap(sub,40):
        out.append(f'<text x="36" y="{yy}" font-size="10.5" fill="#555">{esc(l)}</text>'); yy+=13

band(95,92,'1. Requirement raised','the row is the stakeholder\'s; the work to agree it is an open item',C['REQ'][1])
chain(110,[
 ('TRG','SME states a need','in a workshop, review or email'),
 ('REQ','REQ Draft','Raised on, Raised by, Owner = the SME, MoSCoW proposed'),
 ('OI','OI: agree it','owner: architect. Confirm MoSCoW and phase with stakeholders'),
 ('REQ','REQ Agreed','Phase set: this or next. The OI closes into this REQ'),
 ('REQ','REQ Designed','a design section covers it. DEC only if a real choice was made'),
 ('TRG','Vendor or team builds','per Implemented by. Vendor ref lines up their item'),
 ('REQ','REQ Delivered','OI: verify it with the SME'),
 ('REQ','REQ Verified','the owner confirms the need is met'),
])
band(200,300,'2. Limitation identified','a fact about the solution; assessed inside an open item; leaves by exactly one path',C['LIM'][1])
chain(215,[
 ('TRG','Discovery','the platform does not do what a REQ needs'),
 ('LIM','LIM Identified','Identified on, Raised by, constrains REQ-nnn'),
 ('OI','OI: assess it','owner named. Fill Impact. Talk to the vendor'),
 ('LIM','LIM Under assessment','Options listed with impact and phase; choose one'),
])
rows=[(215,'Accept','we live with it','DEC','DEC Accepted','Rationale, Consulted, Approved by, Decided on','LIM Accepted','Disposition record = the DEC'),
      (285,'Change now','fix it in this phase','CR','CR Proposed','continues on strip 4','LIM Change requested','status follows the CR'),
      (355,'Change later','fix it in a named phase','CR','CR Deferred','waits for phase planning; then strip 4','LIM Change requested','CR shows on the next-phase view'),
      (425,'Resolved','the vendor fixed it','TRG','Evidence noted','vendor item or design version','LIM Resolved','no further work')]
for y,ch,chs,t,rt,rs,lt,ls in rows:
    node(4,y,'TRG',ch,chs); node(5,y,t,rt,rs); node(6,y,'LIM',lt,ls)
    arrow(3,215,4,y,'#b83232'); arrow(4,y,5,y); arrow(5,y,6,y)
band(515,300,'3. Decision by an SME or stakeholder','a choice between options, or a constraint accepted. Approval is ours',C['DEC'][1])
chain(530,[
 ('TRG','SME picks an option','or accepts a platform constraint'),
 ('DEC','DEC Proposed','Raised by = the SME. Rationale names the rejected option'),
 ('OI','OI: confirm and approve','consult the vendor and SMEs; take it to the approver'),
 ('DEC','DEC Accepted','Consulted, Approved by, Decided on. Immutable from here'),
])
cons=[(530,'REQ','addresses REQ-nnn','only if a real choice was made; REQ moves to Designed'),
      (600,'LIM','introduces a LIM?','start strip 2'),
      (670,'RSK','raises a RSK?','start strip 5'),
      (740,'DEC','Change of mind later','new DEC supersedes; old one marked Superseded, never edited')]
for y,t,title,sub in cons:
    node(4,y,t,title,sub); arrow(3,530,4,y,'#3a7d2c',dash=(y==740))
band(830,160,'4. Change request','raised only once a limitation or requirement chose to ask for a change; one row for its whole life',C['CR'][1])
chain(845,[
 ('TRG','LIM or REQ chose change','strip 2 said fix it, now or in a named phase'),
 ('CR','CR Proposed','Reason, Raised by, Raised on, Phase, triggered by'),
 ('CR','CR Options','ways to make the change, each with impact and phase'),
 ('CR','CR For approval','Consulted; stakeholders pick an option'),
 ('CR','CR Approved > Submitted','Chosen option, Approved by. Vendor ref when vendor'),
])
node(5,845,'CR','CR Delivered','built. Linked REQ moves to Delivered'); arrow(4,845,5,845,'#1a7f8e')
node(1,915,'CR','CR Deferred','created here for a later phase; reopens at phase planning'); arrow(0,845,1,915,'#1a7f8e'); arrow(1,915,2,845,'#888',dash=True)
node(4,915,'CR','CR Withdrawn or Rejected','LIM back to assessment; usually Accepted with a DEC'); arrow(3,845,4,915,'#1a7f8e')
band(1005,92,'5. Risk raised','a record with a review date; the weekly routine keeps it honest',C['RSK'][1])
chain(1020,[
 ('TRG','Review raises a risk','or an assumption that would hurt if wrong'),
 ('RSK','RSK Identified','Identified on, Raised by, Likelihood, Impact'),
 ('TRG','Weekly routine','set Trigger, Mitigation and the review Due'),
 ('RSK','RSK Mitigating','mitigation actions are open items'),
 ('OI','OI: mitigate','owner, next action, due'),
 ('TRG','Review Due passes','routine updates L/I and Due, or Retires it with a reason'),
 ('RSK','Trigger seen: Realised','raise an OI at once'),
 ('OI','OI resolves into','a LIM, a CR or a DEC'),
])
band(1110,92,'6. Weekly meeting','one page, top to bottom; nothing leaves without an owner and a date',C['OI'][1])
chain(1125,[
 ('TRG','Open the Outstanding page','OIs by owner and due; LIMs in assessment; risks past review'),
 ('OI','Walk each OI','new next action and due, or close it into a record'),
 ('TRG','Blocked?','Blocked by is on the row; unblock or escalate'),
 ('LIM','LIMs over 14 days','disposition now, or a new due on their OI'),
 ('TRG','New items','id, Raised by, and an owner before the meeting ends'),
 ('TRG','Phase planning','next-phase view: deferred CRs by phase, then next-phase REQs'),
])
lx=290
for t,name in [('TRG','trigger or event'),('REQ','requirement'),('DEC','decision'),('LIM','limitation'),('RSK','risk'),('CR','change request'),('OI','open item (the work)')]:
    f,s=C[t]; dash=' stroke-dasharray="5,3"' if t=='OI' else ''
    out.append(f'<rect x="{lx}" y="1222" width="16" height="12" rx="3" fill="{f}" stroke="{s}"{dash}/>')
    out.append(f'<text x="{lx+22}" y="1232" font-size="11" fill="#333">{esc(name)}</text>')
    lx+=160
body='\n'.join(out)
svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Helvetica, Arial, sans-serif">
<defs><marker id="arr" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L8,4 L0,8 z" fill="#444"/></marker></defs>
<rect width="{W}" height="{H}" fill="#ffffff"/>
<text x="20" y="44" font-size="24" font-weight="bold" fill="#222">A day in the life of the design register</text>
<text x="20" y="66" font-size="13" fill="#666">Six things that happen on the project, and how each one runs through the registers. Dashed blue boxes are open items: the only rows with an owner, a next action and a due date, apart from requirements which keep their owner.</text>
{body}
</svg>'''
open('daylife.svg','w').write(svg)
sq=svg.replace(f'width="{W}" height="{H}" viewBox="0 0 {W} {H}"',f'width="{W}" height="{W}" viewBox="0 0 {W} {W}"').replace(f'<rect width="{W}" height="{H}" fill="#ffffff"/>',f'<rect width="{W}" height="{W}" fill="#ffffff"/><g transform="translate(0,{(W-H)//2})">').replace('</svg>','</g></svg>')
open('daylife-sq.svg','w').write(sq)
print('ok')
