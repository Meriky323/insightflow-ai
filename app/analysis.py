from __future__ import annotations

import re
from collections import Counter, defaultdict

ISSUES = {
    'Heat & safety': [r'overheat', r'over heating', r'heat', r'gets? hot', r'too hot', r'warm', r'temperature', r'thermal', r'burn', r'safety'],
    'Weight & thickness': [r'heavy', r'weight', r'bulky', r'thick', r'too big', r'pocket', r'slim', r'compact'],
    'Magnetic stability': [r'magnet', r'magnetic', r'magsafe', r'qi2', r'snap', r'grip', r'slide', r'slips?', r'falls? off', r'alignment'],
    'Charging speed': [r'slow', r'fast charg', r'charging speed', r'charge speed', r'takes too long', r'watt', r'\b15w\b', r'\b25w\b', r'\b30w\b', r'\b45w\b'],
    'Capacity / battery life': [r'capacity', r'mah', r'battery life', r'full charge', r'charges?', r'usable', r'conversion efficiency', r'drain'],
    'Compatibility': [r'compatible', r'compatibility', r'case on', r'phone case', r'iphone', r'android', r'camera bump', r'camera', r'fit'],
    'Build quality / durability': [r'broken', r'broke', r'loose', r'scratch', r'cheap', r'crack', r'durab', r'build quality', r'port'],
    'Price / value': [r'expensive', r'price', r'value', r'worth', r'cheaper', r'overpriced', r'discount'],
    'Service / delivery': [r'refund', r'support', r'customer service', r'shipping', r'delivery', r'warranty', r'replacement'],
}
DRIVERS = {
    'Magnetic convenience': [r'magnet', r'magnetic', r'snap', r'magsafe', r'qi2', r'no cable'],
    'Fast charging': [r'fast charg', r'quick charg', r'charges fast', r'\b30w\b', r'\b45w\b', r'\b65w\b'],
    'Portable / compact': [r'compact', r'slim', r'lightweight', r'light', r'pocket', r'portable'],
    'Battery display': [r'display', r'percentage', r'screen', r'charge left'],
    'Travel usefulness': [r'travel', r'flight', r'airplane', r'trip', r'airport'],
    'Built-in cable': [r'built.?in cable', r'integrated cable', r'attached cable'],
    'Design / feel': [r'premium', r'design', r'looks good', r'finish', r'texture'],
}
NEG = {'bad','worst','terrible','awful','hate','disappointed','useless','poor','problem','issue','slow','weak','hot','heavy','broken','expensive','return','refund'}
POS = {'great','good','excellent','love','amazing','perfect','useful','convenient','fast','strong','recommend','happy','compact','premium'}


def _contains(text: str, patterns: list[str]) -> bool:
    return any(re.search(p, text, flags=re.I) for p in patterns)


def sentiment(text: str, rating=None) -> str:
    if rating is not None:
        try:
            r=float(rating)
            if r <= 2: return 'negative'
            if r == 3: return 'neutral'
            if r >= 4: return 'positive'
        except Exception:
            pass
    words=re.findall(r"[a-zA-Z']+", text.lower())
    s=sum(w in POS for w in words)-sum(w in NEG for w in words)
    if s >= 2: return 'positive'
    if s <= -2: return 'negative'
    return 'neutral'


def issue(text: str) -> str | None:
    scores=[]
    for name, pats in ISSUES.items():
        score=sum(bool(re.search(p,text,re.I)) for p in pats)
        if score: scores.append((score,name))
    return max(scores)[1] if scores else None


def driver(text: str, sent: str) -> str | None:
    if sent != 'positive': return None
    scores=[]
    for name,pats in DRIVERS.items():
        score=sum(bool(re.search(p,text,re.I)) for p in pats)
        if score: scores.append((score,name))
    return max(scores)[1] if scores else None


def purchase_impact(text: str) -> str | None:
    t=text.lower()
    if re.search(r'\b(return|returned|returning|refund|refunded)\b',t): return 'Return / refund'
    if re.search(r'\b(switch|switched|another brand|different brand)\b',t): return 'Switch brand'
    if re.search(r'\b(wouldn.?t buy|would not buy|won.?t buy|avoid|dealbreaker|deal breaker|not purchase)\b',t): return 'Blocked purchase'
    if re.search(r'\b(recommend|recommended|would buy again|buy again|repurchase)\b',t): return 'Recommend / repeat'
    return None


def scenario(text: str) -> str | None:
    t=text.lower()
    if re.search(r'travel|flight|airport|trip|airplane',t): return 'Travel / flight'
    if re.search(r'commut|every day|daily|pocket',t): return 'Daily commute'
    if re.search(r'office|meeting|workday|work day',t): return 'Office / meetings'
    if re.search(r'camp|outdoor|festival|hiking',t): return 'Outdoor'
    if re.search(r'gaming|game|heavy use|high load',t): return 'Gaming / heavy use'
    if re.search(r'emergency|backup|power outage',t): return 'Emergency backup'
    return None


def annotate(row: dict) -> dict:
    text=(row.get('title') or '')+' '+(row.get('text') or '')
    sent=sentiment(text,row.get('rating'))
    row['sentiment']=sent
    row['issue']=issue(text) if sent != 'positive' else issue(text)
    row['driver']=driver(text,sent)
    row['purchase_impact']=purchase_impact(text)
    row['scenario']=scenario(text)
    return row


def summarize(products: list[dict], reviews: list[dict], trends: list[dict]) -> dict:
    n=len(reviews)
    sc=Counter(r.get('sentiment') or 'unknown' for r in reviews)
    issues=Counter(r.get('issue') for r in reviews if r.get('issue'))
    drivers=Counter(r.get('driver') for r in reviews if r.get('driver'))
    impacts=Counter(r.get('purchase_impact') for r in reviews if r.get('purchase_impact'))
    sources=Counter(r.get('source') for r in reviews)
    markets=Counter(r.get('market') for r in reviews)
    issue_details=[]
    for name,count in issues.most_common():
        rows=[r for r in reviews if r.get('issue')==name]
        impacted=sum(1 for r in rows if r.get('purchase_impact'))
        avg_rating=sum(float(r['rating']) for r in rows if r.get('rating') is not None) / max(1,sum(1 for r in rows if r.get('rating') is not None))
        issue_details.append({'name':name,'count':count,'share':round(count*100/max(1,n),1),'purchase_impact_rate':round(impacted*100/max(1,count),1),'avg_rating':round(avg_rating,2)})

    prod_text=' '.join((p.get('title','')+' '+(p.get('raw_json') or '')) for p in products).lower()
    coverage_terms={
        'Heat & safety':['cooling','thermal','temperature','heat'],
        'Weight & thickness':['slim','compact','lightweight','thin'],
        'Magnetic stability':['magnet','magnetic','qi2','magsafe','grip'],
        'Charging speed':['25w','30w','45w','65w','fast charge'],
        'Capacity / battery life':['5000mah','10000mah','20000mah','capacity'],
        'Compatibility':['iphone','android','compatible','case'],
    }
    opportunities=[]
    max_issue=max([x['count'] for x in issue_details], default=1)
    for x in issue_details[:8]:
        terms=coverage_terms.get(x['name'],[])
        covered=sum(1 for t in terms if t in prod_text)
        coverage=covered/max(1,len(terms)) if terms else .5
        volume=x['count']/max_issue
        impact=x['purchase_impact_rate']/100
        score=round(100*(.5*volume+.3*impact+.2*(1-coverage)))
        opportunities.append({**x,'benchmark_coverage':round(coverage*100),'opportunity_score':score,'label':'Validation hypothesis'})
    opportunities.sort(key=lambda z:z['opportunity_score'], reverse=True)

    return {
      'review_count':n,'product_count':len(products),'trend_points':len(trends),
      'sentiment':dict(sc),'issues':issue_details,'drivers':[{'name':k,'count':v,'share':round(v*100/max(1,n),1)} for k,v in drivers.most_common()],
      'impacts':dict(impacts),'sources':dict(sources),'markets':dict(markets),
      'opportunities':opportunities,
      'top_products':products[:20],
      'trends':trends,
    }
