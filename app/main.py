from __future__ import annotations

import json
import re
import threading
import httpx
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import db
from .analysis import annotate_fallback, apply_llm_extraction, summarize
from .collectors.serpapi import SerpApiClient
from .config import clear_settings, config_status, get, save_settings
from .llm import analyze_review_batch, ask_llm, generate_decision_brief, llm_enabled, normalize_topic_labels, test_llm_connection
from .reports import write_csv, write_docx, write_pdf
from .importers import parse_evidence_file
from .demo import seed_portfolio_demo

ROOT=Path(__file__).resolve().parents[1]
STATIC=ROOT/'static'

app=FastAPI(title='InsightFlow AI',version='2.0.0')
db.init_db()


class SettingsIn(BaseModel):
    serpapi_api_key: str | None = None
    llm_api_key: str | None = None
    llm_base_url: str | None = None
    llm_model: str | None = None


class SettingsClearIn(BaseModel):
    fields: list[Literal['serpapi','llm']] = Field(default_factory=list)


class ResearchIn(BaseModel):
    keyword: str = Field(min_length=2,max_length=160)
    markets: list[str] = Field(default_factory=lambda:['US'])
    days: int = Field(default=180,ge=7,le=1825)
    sources: list[Literal['shopping','walmart','youtube','trends','community']] = Field(default_factory=lambda:['shopping','walmart','youtube','trends','community'])
    objective: Literal['gtm','product_launch','competitor','content'] = 'gtm'
    depth: Literal['quick','standard','deep','custom'] = 'standard'
    shopping_limit: int = Field(default=20,ge=1,le=50)
    walmart_products: int = Field(default=2,ge=1,le=8)
    walmart_review_pages: int = Field(default=1,ge=1,le=10)
    youtube_videos_per_market: int = Field(default=2,ge=1,le=8)
    youtube_comment_pages: int = Field(default=1,ge=1,le=5)


class AskIn(BaseModel):
    question: str = Field(min_length=2,max_length=1000)
    language: Literal['en','zh'] = 'en'


@app.get('/api/health')
def health():
    return {'ok':True,'version':'2.0.0','real_data_only':True,'portfolio_demo':True,'bilingual_ui':True,'community_discovery':True,'evidence_thread':True}


@app.get('/api/config')
def cfg():
    return config_status()


@app.post('/api/demo/load')
def demo_load():
    # Static, curated and traceable evidence only: no SerpApi/LLM quota is consumed.
    return seed_portfolio_demo(force=False)


@app.post('/api/settings')
def settings(payload: SettingsIn):
    try:
        save_settings(payload.model_dump())
    except PermissionError as e:
        raise HTTPException(403, str(e))
    return config_status()


@app.get('/api/connections/test')
def connection_test():
    c=config_status()
    if c['public_deployment']:
        raise HTTPException(403,'Connector diagnostics are disabled in the public recruiter demo.')
    result={'serpapi':{'ok':False,'message':'SerpApi is not configured'},'llm':test_llm_connection()}
    key=get('SERPAPI_API_KEY')
    if key:
        try:
            with httpx.Client(timeout=20) as client:
                r=client.get('https://serpapi.com/account.json',params={'api_key':key})
                if r.status_code>=400:
                    result['serpapi']={'ok':False,'message':f'HTTP {r.status_code}: {r.text[:180]}'}
                else:
                    data=r.json()
                    result['serpapi']={
                        'ok':True,'message':'SerpApi account reachable',
                        'plan_name':data.get('plan_name'),'searches_per_month':data.get('searches_per_month'),
                        'this_month_usage':data.get('this_month_usage'),'searches_left':data.get('total_searches_left') if data.get('total_searches_left') is not None else data.get('plan_searches_left')
                    }
        except Exception as e:
            result['serpapi']={'ok':False,'message':f'{type(e).__name__}: {e}'}
    return result


@app.post('/api/settings/clear')
def settings_clear(payload: SettingsClearIn):
    try:
        clear_settings(payload.fields)
    except PermissionError as e:
        raise HTTPException(403, str(e))
    return config_status()


def _research_payload(r: dict) -> dict:
    out=dict(r)
    for key,new_key in [('markets_json','markets'),('sources_json','sources'),('source_status_json','source_status'),('decision_json','decision')]:
        raw=out.pop(key, None)
        try: out[new_key]=json.loads(raw or ('{}' if key in {'source_status_json','decision_json'} else '[]'))
        except Exception: out[new_key]={} if key in {'source_status_json','decision_json'} else []
    return out


def _portfolio_visible(r: dict) -> bool:
    try:
        decision=json.loads(r.get('decision_json') or '{}') if 'decision_json' in r else (r.get('decision') or {})
    except Exception:
        decision={}
    meta=(decision.get('demo_meta') or {}) if isinstance(decision,dict) else {}
    return bool(meta.get('portfolio_demo') or meta.get('portfolio_demo_baseline'))


def _require_research(rid: int) -> dict:
    r=db.get_research(rid)
    if not r:
        raise HTTPException(404,'research not found')
    c=config_status()
    if c['public_deployment'] and not c['allow_public_live_research'] and not _portfolio_visible(r):
        # Do not reveal whether a non-demo local research ID exists on the public deployment.
        raise HTTPException(404,'research not found')
    return r


def _attach_decisions(summary: dict, r: dict) -> dict:
    rr=_research_payload(r)
    decision=rr.get('decision') or {}
    decision_map={x.get('name'):x for x in (decision.get('opportunities') or []) if x.get('name')}
    for item in summary.get('opportunities') or []:
        if item.get('name') in decision_map:
            item['decision']=decision_map[item['name']]
    summary['research']=rr
    return summary


@app.get('/api/researches')
def researches():
    rows=[_research_payload(r) for r in db.list_researches()]
    c=config_status()
    if c['public_deployment'] and not c['allow_public_live_research']:
        # Keep the recruiter deployment scoped to the built-in portfolio snapshots.
        rows=[r for r in rows if (r.get('decision') or {}).get('demo_meta',{}).get('portfolio_demo') or (r.get('decision') or {}).get('demo_meta',{}).get('portfolio_demo_baseline')]
    return rows


@app.post('/api/research')
def research_create(payload: ResearchIn):
    c=config_status()
    if c['public_deployment'] and not c['allow_public_live_research']:
        raise HTTPException(403,'Public demo mode does not allow live API-consuming research. Use a saved research snapshot or run locally.')
    if payload.sources and not get('SERPAPI_API_KEY'):
        raise HTTPException(400,'SERPAPI_API_KEY 未配置。先在 Settings 填入 SerpApi key；如果只导入 CSV/JSON，可以取消所有在线数据源。')
    markets=[]
    for m in payload.markets:
        m=m.upper()
        if m not in {'US','AU','UK','CA'}: continue
        if m not in markets: markets.append(m)
    if not markets: markets=['US']
    rid=db.create_research(payload.keyword.strip(),markets,payload.days,list(payload.sources),payload.objective)
    if not payload.sources:
        db.set_research_status(rid,'completed',100,'Research shell created. Import CSV/JSON evidence from Consumer Voice.')
        return {'id':rid,'status':'completed','estimated_serpapi_calls':0,'depth':payload.depth}
    thread=threading.Thread(target=_run_research,args=(rid,payload,markets),daemon=True)
    thread.start()
    return {'id':rid,'status':'queued','estimated_serpapi_calls':estimate_calls(payload,markets),'depth':payload.depth}


@app.get('/api/research/{rid}')
def research_status(rid:int):
    r=_require_research(rid)
    return _research_payload(r)


@app.get('/api/research/{rid}/summary')
def research_summary(rid:int):
    r=_require_research(rid)
    markets=json.loads(r['markets_json'])
    products=db.rows_for(rid,'products');reviews=db.rows_for(rid,'reviews');trends=db.rows_for(rid,'trends')
    out=_attach_decisions(summarize(products,reviews,trends,markets),r)
    rr=out['research']
    baseline=db.find_previous_comparable_research(rid,r['keyword'],markets,r['days'],json.loads(r['sources_json']))
    if baseline:
        bmarkets=json.loads(baseline['markets_json'])
        bproducts=db.rows_for(baseline['id'],'products');breviews=db.rows_for(baseline['id'],'reviews');btrends=db.rows_for(baseline['id'],'trends')
        common_sources=sorted((set(x.get('source') for x in reviews) & set(x.get('source') for x in breviews)) - {None})
        cr=[x for x in reviews if x.get('source') in common_sources]
        br=[x for x in breviews if x.get('source') in common_sources]
        cs=summarize(products,cr,trends,markets)
        bs=summarize(bproducts,br,btrends,bmarkets)
        out['historical_delta']=_summary_delta(cs,bs,rr,_research_payload(baseline),common_sources)
    else:
        out['historical_delta']=None
    return out


@app.get('/api/research/{rid}/products')
def research_products(rid:int):
    _require_research(rid)
    return db.rows_for(rid,'products')


@app.get('/api/research/{rid}/reviews')
def research_reviews(rid:int,limit:int=Query(500,ge=1,le=5000),offset:int=Query(0,ge=0),source:str|None=None,market:str|None=None,sentiment:str|None=None,issue:str|None=None,q:str|None=None):
    _require_research(rid)
    rows=db.rows_for(rid,'reviews')
    def ok(x):
        if source and x.get('source')!=source:return False
        if market and x.get('market')!=market:return False
        if sentiment and x.get('sentiment')!=sentiment:return False
        if issue:
            try: topics=json.loads(x.get('topics_json') or '[]')
            except Exception: topics=[]
            if x.get('issue')!=issue and issue not in topics:return False
        if q and q.lower() not in (' '.join(str(x.get(k) or '') for k in ['title','text','issue','driver','barrier','scenario'])).lower():return False
        return True
    rows=[x for x in rows if ok(x)]
    return {'total':len(rows),'rows':rows[offset:offset+limit],'offset':offset,'limit':limit,'has_more':offset+limit<len(rows)}


@app.post('/api/research/{rid}/import')
async def research_import(rid:int,file:UploadFile=File(...),max_rows:int=Query(1000,ge=1,le=5000)):
    r=_require_research(rid)
    c=config_status()
    if c['public_deployment'] and not c['allow_public_live_research']:
        raise HTTPException(403,'Public demo mode does not allow evidence uploads or AI-consuming imports.')
    if file.content_type and file.content_type not in {'text/csv','application/csv','application/json','text/plain','application/vnd.ms-excel'} and not (file.filename or '').lower().endswith(('.csv','.json','.tsv','.txt')):
        raise HTTPException(400,'Upload a CSV/TSV or JSON evidence file.')
    content=await file.read()
    if len(content)>12*1024*1024: raise HTTPException(413,'File is too large. Maximum 12 MB.')
    try: rows,meta=parse_evidence_file(content,file.filename or 'evidence.csv',max_rows=max_rows)
    except Exception as e: raise HTTPException(400,f'Import parse failed: {e}')
    if not rows: return {'imported':0,'meta':meta,'message':'No rows with a usable text/comment/review field.'}
    rows,dropped,unknown=_apply_time_window(rows,r['days'])
    existing=[]
    for row in rows:
        if not db.review_exists(rid,row.get('source') or '',row.get('review_external_id') or ''):
            existing.append(row)
    clean=_dedupe_reviews(existing)
    clean,mode,warnings=_analyze_reviews(clean,r['keyword'])
    db.insert_reviews(rid,clean)
    rr=_research_payload(db.get_research(rid));status=rr.get('source_status') or {}
    name=f'Imported evidence · {file.filename or "file"}'
    status[name]={'status':'ok' if clean else 'partial','count':len(clean),'message':f'{dropped} older rows removed; {unknown} dates unverified; analysis={mode}'}
    final_mode='hybrid' if rr.get('analysis_mode') not in {mode,'pending','none'} else mode
    db.set_research_meta(rid,source_status=status,analysis_mode=final_mode)
    if llm_enabled() and clean:
        try:
            products=db.rows_for(rid,'products');all_reviews=db.rows_for(rid,'reviews');trends=db.rows_for(rid,'trends');markets=json.loads(r['markets_json'])
            temp_summary=summarize(products,all_reviews,trends,markets)
            decision=generate_decision_brief(r['keyword'],r.get('objective') or 'gtm',temp_summary,_representative_reviews(all_reviews,temp_summary,48))
            db.set_research_meta(rid,decision=decision)
        except Exception as e:
            warnings.append(f'Decision brief refresh: {type(e).__name__}: {e}')
    return {'imported':len(clean),'dropped_old':dropped,'date_unknown':unknown,'analysis_mode':mode,'warnings':warnings,'meta':meta}


@app.get('/api/research/{rid}/trends')
def research_trends(rid:int):
    _require_research(rid)
    return db.rows_for(rid,'trends')


@app.get('/api/research/{rid}/compare/{baseline_id}')
def research_compare(rid:int,baseline_id:int):
    a=_require_research(rid);b=_require_research(baseline_id)
    sa=summarize(db.rows_for(rid,'products'),db.rows_for(rid,'reviews'),db.rows_for(rid,'trends'),json.loads(a['markets_json']))
    sb=summarize(db.rows_for(baseline_id,'products'),db.rows_for(baseline_id,'reviews'),db.rows_for(baseline_id,'trends'),json.loads(b['markets_json']))
    return _summary_delta(sa,sb,_research_payload(a),_research_payload(b))


def _retrieve_for_question(question:str,reviews:list[dict],summary:dict,limit:int=48)->list[dict]:
    """Lightweight retrieval over saved evidence before sending context to the LLM.

    This keeps Ask InsightFlow grounded in the rows most related to the question while still
    preserving source diversity. It is intentionally deterministic and dependency-free.
    """
    qtokens={w for w in re.findall(r'[a-zA-Z0-9\u4e00-\u9fff]+',question.lower()) if len(w)>=2}
    scored=[]
    topic_names=[x.get('name','') for x in summary.get('issues') or []]
    for r in reviews:
        try:topics=json.loads(r.get('topics_json') or '[]')
        except Exception:topics=[]
        hay=' '.join(str(r.get(k) or '') for k in ['text','title','issue','driver','barrier','scenario']).lower()+' '+' '.join(topics).lower()
        score=sum(2 for t in qtokens if t in hay)
        for topic in topic_names:
            if topic and topic.lower() in question.lower() and topic.lower() in hay: score+=5
        if r.get('purchase_impact'): score+=0.6
        if r.get('helpful'): score+=min(1.5,float(r.get('helpful') or 0)/20)
        scored.append((score,r))
    scored.sort(key=lambda x:x[0],reverse=True)
    selected=[];seen=set();per_source=defaultdict(int)
    for score,r in scored:
        if score<=0 and len(selected)>=min(12,limit):break
        key=(r.get('source'),r.get('review_external_id') or (r.get('text') or '')[:120])
        if key in seen:continue
        src=r.get('source') or 'Unknown'
        if per_source[src]>=max(6,limit//3):continue
        seen.add(key);per_source[src]+=1;selected.append(r)
        if len(selected)>=limit:break
    if len(selected)<min(16,limit):
        for r in _representative_reviews(reviews,summary,limit):
            key=(r.get('source'),r.get('review_external_id') or (r.get('text') or '')[:120])
            if key not in seen:
                seen.add(key);selected.append(r)
            if len(selected)>=limit:break
    return selected


@app.post('/api/research/{rid}/ask')
def research_ask(rid:int,payload:AskIn):
    r=_require_research(rid)
    products=db.rows_for(rid,'products');reviews=db.rows_for(rid,'reviews');trends=db.rows_for(rid,'trends')
    markets=json.loads(r['markets_json'])
    summary=_attach_decisions(summarize(products,reviews,trends,markets),r)
    c=config_status()
    # Public recruiter mode must never spend the owner's LLM quota. The Ask surface
    # remains usable through deterministic grounded answers over the saved evidence.
    if llm_enabled() and not (c['public_deployment'] and not c['allow_public_live_research']):
        context={
            'research':_research_payload(r),
            'summary':{k:v for k,v in summary.items() if k not in {'trends','top_products'}},
            'representative_evidence':_retrieve_for_question(payload.question,reviews,summary,60),
            'products':products[:40],
            'trend_summary':summary.get('trend_summary'),
        }
        prompt = ("请使用简体中文回答，并严格依据提供的 evidence；如果证据不足，请明确说明。\n\n" if payload.language == 'zh' else "Answer in English and stay strictly grounded in the supplied evidence; say explicitly when evidence is insufficient.\n\n") + payload.question
        try:return {'mode':'llm-grounded','answer':ask_llm(prompt,context)}
        except Exception as e:return {'mode':'local-fallback','answer':_local_answer(payload.question,summary,reviews,products,payload.language),'warning':str(e)}
    return {'mode':'local','answer':_local_answer(payload.question,summary,reviews,products,payload.language)}


@app.get('/api/research/{rid}/export/{kind}')
def export(rid:int,kind:str):
    r=_require_research(rid)
    markets=json.loads(r['markets_json'])
    summary=_attach_decisions(summarize(db.rows_for(rid,'products'),db.rows_for(rid,'reviews'),db.rows_for(rid,'trends'),markets),r)
    if kind=='csv':p=write_csv(db.rows_for(rid,'reviews'),rid);media='text/csv'
    elif kind=='docx':p=write_docx(r,summary);media='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    elif kind=='pdf':p=write_pdf(r,summary);media='application/pdf'
    else:raise HTTPException(400,'kind must be csv/docx/pdf')
    return FileResponse(p,media_type=media,filename=p.name)


def _depth_values(p:ResearchIn) -> tuple[int,int,int,int]:
    if p.depth=='quick': return 1,1,1,1
    if p.depth=='standard': return 2,1,2,1
    if p.depth=='deep': return 3,2,3,1
    return p.walmart_products,p.walmart_review_pages,p.youtube_videos_per_market,p.youtube_comment_pages


def estimate_calls(p:ResearchIn, markets:list[str])->int:
    wm_products,wm_pages,yt_videos,yt_pages=_depth_values(p)
    calls=0
    if 'shopping' in p.sources:calls+=len(markets)
    if 'trends' in p.sources:calls+=len(markets)
    if 'community' in p.sources:calls+=1
    if 'walmart' in p.sources and 'US' in markets:calls+=1+wm_products*wm_pages
    if 'youtube' in p.sources:calls+=len(markets)*(1+yt_videos*yt_pages)
    return calls


def _parse_review_date(value) -> datetime | None:
    if value is None:return None
    if isinstance(value,(int,float)):
        try:return datetime.fromtimestamp(float(value),tz=timezone.utc)
        except Exception:return None
    s=str(value).strip()
    if not s:return None
    low=s.lower()
    now=datetime.now(timezone.utc)
    if low in {'today','just now'}:return now
    if low=='yesterday':return now-timedelta(days=1)
    # Google Discussions/Forums commonly returns compact ages such as 4w, 3mo, 1y.
    short=re.fullmatch(r'(\d+)\s*(m|h|d|w|mo|y)',low)
    if short:
        n=int(short.group(1));unit=short.group(2)
        days={'m':n/1440,'h':n/24,'d':n,'w':7*n,'mo':30*n,'y':365*n}[unit]
        return now-timedelta(days=days)
    m=re.search(r'(\d+)\s*(minute|hour|day|week|month|year)s?\s+ago',low)
    if m:
        n=int(m.group(1));unit=m.group(2)
        days={'minute':n/1440,'hour':n/24,'day':n,'week':7*n,'month':30*n,'year':365*n}[unit]
        return now-timedelta(days=days)
    try:
        dt=datetime.fromisoformat(s.replace('Z','+00:00'))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:pass
    for fmt in ('%m/%d/%Y','%Y-%m-%d','%b %d, %Y','%B %d, %Y','%d %b %Y'):
        try:return datetime.strptime(s,fmt).replace(tzinfo=timezone.utc)
        except Exception:pass
    try:
        dt=parsedate_to_datetime(s)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:return None


def _apply_time_window(rows:list[dict],days:int)->tuple[list[dict],int,int]:
    cutoff=datetime.now(timezone.utc)-timedelta(days=days)
    kept=[];dropped=0;unknown=0
    for r in rows:
        dt=_parse_review_date(r.get('review_date'))
        if dt is None:
            r['window_status']='unknown';unknown+=1;kept.append(r);continue
        if dt>=cutoff:
            r['window_status']='in_window';kept.append(r)
        else:
            dropped+=1
    return kept,dropped,unknown


def _dedupe_reviews(rows:list[dict])->list[dict]:
    seen=set();clean=[]
    for x in rows:
        text=' '.join((x.get('text') or '').split())
        if not text:continue
        key=(x.get('source'),x.get('review_external_id') or text[:220])
        if key in seen:continue
        seen.add(key);x['text']=text;clean.append(x)
    return clean


def _dedupe_products(rows:list[dict])->list[dict]:
    out=[];seen=set()
    for x in rows:
        k=(x.get('source'),x.get('external_id') or x.get('url') or x.get('title'))
        if k in seen:continue
        seen.add(k);out.append(x)
    return out


def _analyze_reviews(rows:list[dict],category:str)->tuple[list[dict],str,list[str]]:
    if not rows:return rows,'none',[]
    warnings=[]
    if not llm_enabled():
        return [annotate_fallback(r) for r in rows],'local-fallback',warnings
    llm_count=0;fallback_count=0
    for start in range(0,len(rows),32):
        batch=rows[start:start+32]
        try:
            extracted=analyze_review_batch(batch,category)
        except Exception as e:
            extracted={};warnings.append(f'LLM batch {start//32+1}: {type(e).__name__}: {e}')
        for i,row in enumerate(batch):
            if i in extracted:
                apply_llm_extraction(row,extracted[i]);llm_count+=1
            else:
                annotate_fallback(row);fallback_count+=1
    if llm_count:
        labels=[]
        for r in rows:
            try:labels.extend(json.loads(r.get('topics_json') or '[]'))
            except Exception:pass
        try:
            mapping=normalize_topic_labels(labels,category)
            for r in rows:
                try:topics=json.loads(r.get('topics_json') or '[]')
                except Exception:topics=[]
                topics=[mapping.get(x,x) for x in topics]
                r['topics_json']=json.dumps(topics,ensure_ascii=False)
                if topics:r['issue']=topics[0]
        except Exception as e:
            warnings.append(f'Topic normalization: {type(e).__name__}: {e}')
    mode='llm' if llm_count and not fallback_count else 'hybrid' if llm_count else 'local-fallback'
    return rows,mode,warnings


def _run_research(rid:int,p:ResearchIn,markets:list[str]):
    source_status={};warnings=[]
    def mark(name,status,count=0,message=''):
        source_status[name]={'status':status,'count':count,'message':message}
        db.set_research_meta(rid,source_status=source_status)
    try:
        db.clear_research_data(rid);db.set_research_status(rid,'running',2,'Starting real-data collection')
        client=SerpApiClient(get('SERPAPI_API_KEY'))
        products=[];reviews=[];trends=[]
        wm_products_n,wm_pages,yt_videos_n,yt_pages=_depth_values(p)

        if 'shopping' in p.sources:
            for i,m in enumerate(markets,1):
                name=f'Google Shopping · {m}';db.set_research_status(rid,'running',6+2*i,f'Collecting {name}')
                try:
                    rows=client.google_shopping(p.keyword,m,p.shopping_limit);products.extend(rows);mark(name,'ok',len(rows))
                except Exception as e:
                    msg=f'{type(e).__name__}: {e}';warnings.append(f'{name}: {msg}');mark(name,'failed',0,msg)

        walmart_products=[]
        if 'walmart' in p.sources and 'US' in markets:
            name='Walmart products · US';db.set_research_status(rid,'running',24,'Collecting Walmart products')
            try:
                walmart_products=client.walmart_search(p.keyword,max(wm_products_n,8));products.extend(walmart_products);mark(name,'ok',len(walmart_products))
            except Exception as e:
                msg=f'{type(e).__name__}: {e}';warnings.append(f'{name}: {msg}');mark(name,'failed',0,msg)
            if walmart_products:
                got=0;fails=0
                for i,prod in enumerate(walmart_products[:wm_products_n],1):
                    db.set_research_status(rid,'running',28+int(15*i/max(1,wm_products_n)),f'Walmart reviews {i}/{wm_products_n}')
                    try:
                        rs=client.walmart_reviews(prod,wm_pages);reviews.extend(rs);got+=len(rs)
                    except Exception as e:
                        fails+=1;warnings.append(f"Walmart reviews · {prod.get('title','product')[:50]}: {type(e).__name__}: {e}")
                mark('Walmart reviews · US','partial' if fails else 'ok',got,f'{fails} product(s) failed' if fails else '')

        if 'community' in p.sources:
            # Community discovery is intentionally one global evidence call. The requested market only biases
            # the search result set; author geography is not inferred from it.
            name='Community discussions · GLOBAL';db.set_research_status(rid,'running',44,'Discovering Reddit / forum discussions')
            try:
                community_market=markets[0] if markets else 'US'
                rs=client.community_discussions(p.keyword,community_market,24 if p.depth=='deep' else 16 if p.depth=='standard' else 10)
                reviews.extend(rs);mark(name,'ok' if rs else 'partial',len(rs),'Public discussion/answer snippets discovered via Google Discussions & Forums; geography remains GLOBAL.')
            except Exception as e:
                msg=f'{type(e).__name__}: {e}';warnings.append(f'{name}: {msg}');mark(name,'failed',0,msg)

        if 'youtube' in p.sources:
            for mi,m in enumerate(markets,1):
                name=f'YouTube discovery · {m}';db.set_research_status(rid,'running',48+int(8*mi/max(1,len(markets))),f'YouTube search · {m}')
                try:
                    vids=client.youtube_search(p.keyword,m,yt_videos_n);mark(name,'ok',len(vids))
                except Exception as e:
                    vids=[];msg=f'{type(e).__name__}: {e}';warnings.append(f'{name}: {msg}');mark(name,'failed',0,msg)
                got=0;fails=0
                for vid in vids:
                    try:
                        rs=client.youtube_comments(vid,yt_pages);reviews.extend(rs);got+=len(rs)
                    except Exception as e:
                        fails+=1;warnings.append(f"YouTube comments · {vid.get('title','video')[:50]}: {type(e).__name__}: {e}")
                if vids:mark(f'YouTube comments · discovered via {m}','partial' if fails else 'ok',got,f'{fails} video(s) failed' if fails else f'GLOBAL comments; not attributed to {m}')

        if 'trends' in p.sources:
            for mi,m in enumerate(markets,1):
                name=f'Google Trends · {m}';db.set_research_status(rid,'running',64+int(8*mi/max(1,len(markets))),f'Google Trends · {m}')
                try:
                    rows=client.google_trends(p.keyword,m,p.days);trends.extend(rows);mark(name,'ok',len(rows),'Normalized within each market; absolute levels are not cross-market volume.')
                except Exception as e:
                    msg=f'{type(e).__name__}: {e}';warnings.append(f'{name}: {msg}');mark(name,'failed',0,msg)

        db.set_research_status(rid,'running',76,'Applying time window and deduplicating evidence')
        reviews,dropped,unknown=_apply_time_window(reviews,p.days)
        mark('Time-window validation','partial' if unknown else 'ok',len(reviews),f'{dropped} older rows removed; {unknown} rows have unknown/unparseable date')
        clean=_dedupe_reviews(reviews)
        ps=_dedupe_products(products)

        db.set_research_status(rid,'running',82,'AI structuring: topics, drivers, barriers and scenarios')
        clean,analysis_mode,analysis_warnings=_analyze_reviews(clean,p.keyword)
        warnings.extend(analysis_warnings)
        db.set_research_meta(rid,source_status=source_status,analysis_mode=analysis_mode)

        db.set_research_status(rid,'running',92,'Saving auditable evidence')
        db.insert_products(rid,ps);db.insert_reviews(rid,clean);db.insert_trends(rid,trends)
        decision={}
        if llm_enabled() and clean:
            try:
                temp_summary=summarize(ps,clean,trends,markets)
                decision=generate_decision_brief(p.keyword,p.objective,temp_summary,_representative_reviews(clean,temp_summary,48))
                db.set_research_meta(rid,decision=decision)
            except Exception as e:
                warnings.append(f'Decision brief: {type(e).__name__}: {e}')
        total=len(ps)+len(clean)+len(trends)
        if total==0:
            db.set_research_status(rid,'failed',100,'No real evidence was collected. Check connector errors and API configuration.')
            return
        suffix=f' · {len(warnings)} warning(s)' if warnings else ''
        db.set_research_status(rid,'completed',100,f'Completed: {len(ps)} products, {len(clean)} consumer voices, {len(trends)} trend points · analysis={analysis_mode}{suffix}')
    except Exception as e:
        db.set_research_meta(rid,source_status=source_status)
        db.set_research_status(rid,'failed',100,f'{type(e).__name__}: {e}')


def _representative_reviews(reviews:list[dict],summary:dict,limit:int)->list[dict]:
    selected=[];seen=set()
    def add(row):
        key=row.get('id') or (row.get('source'),row.get('review_external_id'),row.get('text','')[:100])
        if key not in seen and len(selected)<limit:
            seen.add(key);selected.append(row)
    # First cover major topics across multiple sources.
    for topic in (summary.get('issues') or [])[:10]:
        candidates=[]
        for r in reviews:
            try:topics=json.loads(r.get('topics_json') or '[]')
            except Exception:topics=[]
            if topic['name'] in topics or r.get('issue')==topic['name']:candidates.append(r)
        by_source=defaultdict(list)
        for r in candidates:by_source[r.get('source')].append(r)
        for rows in by_source.values():
            for r in rows[:3]:add(r)
    # Then ensure each source appears.
    by_source=defaultdict(list)
    for r in reviews:by_source[r.get('source')].append(r)
    for rows in by_source.values():
        for r in rows[:8]:add(r)
    for r in reviews:
        add(r)
        if len(selected)>=limit:break
    return selected


def _summary_delta(current:dict,baseline:dict,current_research:dict,baseline_research:dict,common_sources:list[str]|None=None)->dict:
    def topic_map(x): return {z['name']:z for z in x.get('issues') or []}
    a=topic_map(current);b=topic_map(baseline)
    changes=[]
    for name in set(a)|set(b):
        av=(a.get(name) or {}).get('share',0);bv=(b.get(name) or {}).get('share',0)
        delta=round(av-bv,1)
        cur=(a.get(name) or {})
        stage='Accelerating' if delta>=5 and av>=3 else 'Emerging' if delta>=2 else 'Cooling' if delta<=-2 else 'Stable'
        changes.append({
            'name':name,'current_share':av,'baseline_share':bv,'delta_pp':delta,'stage':stage,
            'current_count':cur.get('count',0),'confidence':cur.get('confidence','Low')
        })
    changes.sort(key=lambda x:(0 if x['stage']=='Stable' else 1,abs(x['delta_pp'])),reverse=True)
    ctm={x['market']:x for x in current.get('trend_summary') or []}
    btm={x['market']:x for x in baseline.get('trend_summary') or []}
    momentum=[]
    for market in set(ctm)|set(btm):
        cv=(ctm.get(market) or {}).get('relative_growth_pct');bv=(btm.get(market) or {}).get('relative_growth_pct')
        momentum.append({
            'market':market,'current_growth_pct':cv,'baseline_growth_pct':bv,
            'delta_pp':round(cv-bv,1) if cv is not None and bv is not None else None
        })
    comparable=bool(common_sources) and current.get('review_count',0)>=10 and baseline.get('review_count',0)>=10
    return {
        'current':current_research,'baseline':baseline_research,
        'common_sources':common_sources or [],'comparable':comparable,
        'sample_delta':current.get('review_count',0)-baseline.get('review_count',0),
        'product_delta':current.get('product_count',0)-baseline.get('product_count',0),
        'topic_changes':changes[:12],'search_momentum_changes':momentum,
        'note':'Historical topic deltas use only consumer-voice sources present in both runs. They are descriptive, not population incidence.',
    }


def _local_answer(question:str,summary:dict,reviews:list[dict],products:list[dict],language:str='en')->str:
    q=question.lower()
    zh=language=='zh'
    research=summary.get('research') or {}
    demo=(research.get('decision') or {}).get('demo_meta') or {}
    opportunities=summary.get('opportunities') or []
    decisions=[x for x in opportunities if (x.get('decision') or {}).get('insight')]

    if any(k in q for k in ['us and au','us vs au','us/au','美国','澳洲','澳大利亚','market comparison','compare market']):
        mc=summary.get('market_comparison') or {}
        if not mc.get('available'):
            reason=mc.get('reason') or 'consumer-voice source coverage is not comparable'
            if zh:
                return f'当前证据不支持 US 与 AU 的消费者偏好比较。\n\n原因：{reason}\n\n可以比较两地的商品与搜索信号，但不能把 GLOBAL Reddit / YouTube 等消费者声音硬归因到某个国家。这个限制是为了避免制造漂亮但错误的市场结论。'
            return f'The current evidence does not support a US-vs-AU consumer-preference comparison.\n\nReason: {reason}\n\nProduct and search signals can still be compared, but GLOBAL Reddit / YouTube voice cannot be reassigned to a country without reliable geography.'
        lines='\n'.join(f"{m}: n={v.get('sample',0)}; top topics="+', '.join(x['name'] for x in (v.get('top_topics') or [])[:4]) for m,v in (mc.get('markets') or {}).items())
        return ('当前可比消费者来源：' if zh else 'Comparable consumer sources: ')+', '.join(mc.get('common_sources') or [])+'。\n'+lines

    if any(k in q for k in ['weak','弱','不足','confidence','可信','证据质量','evidence quality']):
        conf=summary.get('evidence_confidence') or {};issues=summary.get('issues') or []
        low=[x for x in issues if x.get('confidence')=='Low'][:5];mc=summary.get('market_comparison') or {}
        if zh:
            parts=[f"整体 evidence confidence：{conf.get('label','—')} ({conf.get('score','—')}/100)。"]
            if low: parts.append('低置信度主题：'+'；'.join(f"{x['name']} ({x['count']} rows, {x['source_count']} source)" for x in low))
            if not mc.get('available'): parts.append('跨市场消费者比较仍被阻断：'+str(mc.get('reason') or 'coverage gap'))
            if summary.get('window_unknown_count'): parts.append(f"另有 {summary['window_unknown_count']} 条证据日期无法验证。")
            parts.append('下一步优先增加独立来源和可比市场样本，而不是让模型把同一批数据总结得更长。')
            return '\n\n'.join(parts)
        parts=[f"Overall evidence confidence: {conf.get('label','—')} ({conf.get('score','—')}/100)."]
        if low: parts.append('Low-confidence topics: '+'; '.join(f"{x['name']} ({x['count']} rows, {x['source_count']} source)" for x in low))
        if not mc.get('available'): parts.append('Cross-market consumer comparison remains blocked: '+str(mc.get('reason') or 'coverage gap'))
        if summary.get('window_unknown_count'): parts.append(f"{summary['window_unknown_count']} evidence rows also have unverified dates.")
        parts.append('The best next step is to add independent sources and comparable market samples, not to ask the model to summarize the same evidence more aggressively.')
        return '\n\n'.join(parts)

    if any(k in q for k in ['product team','产品团队','产品优先','validate first','验证 first','先验证']):
        if decisions:
            x=decisions[0];d=x['decision']
            if zh:return f"第一优先：{x['name']}。\n\n证据解释：{d.get('insight','—')}\n\nProduct Action：{d.get('product_action','—')}\n\nNext Validation：{d.get('next_validation','—')}\n\nConfidence：{x.get('confidence','—')}；这仍是验证优先级，不是市场规模结论。"
            return f"First priority: {x['name']}.\n\nEvidence interpretation: {d.get('insight','—')}\n\nProduct Action: {d.get('product_action','—')}\n\nNext Validation: {d.get('next_validation','—')}\n\nConfidence: {x.get('confidence','—')}. This is a validation priority, not a market-size claim."
        return '当前没有足够的 evidence-backed decision。先增加消费者样本与 competitor benchmark。' if zh else 'There is not enough evidence for a decision yet. Add consumer samples and competitor evidence first.'

    if any(k in q for k in ['gtm message','message','定位','传播','卖点','marketing','gtm']):
        if decisions:
            x=decisions[0];d=x['decision']
            if zh:return f"当前最有证据支持的 GTM 方向来自「{x['name']}」：\n\n{d.get('gtm_action','—')}\n\n为什么：{d.get('insight','—')}\n\n建议把它写成可证明的 proof point，而不是泛化成“用户都更喜欢”。"
            return f"The strongest evidence-backed GTM direction comes from “{x['name']}”:\n\n{d.get('gtm_action','—')}\n\nWhy: {d.get('insight','—')}\n\nTreat it as a proof point that must be demonstrated, not as a broad claim that all users prefer it."
        drivers=summary.get('drivers') or []
        if zh:return '当前可用 positive drivers：\n'+'\n'.join(f"- {x['name']} ({x['count']})" for x in drivers[:5]) if drivers else '当前正面驱动证据不足。'
        return 'Current positive drivers:\n'+'\n'.join(f"- {x['name']} ({x['count']})" for x in drivers[:5]) if drivers else 'Positive-driver evidence is currently weak.'

    if not reviews and any(k in q for k in ['review','评论','痛点','consumer']):
        return '当前研究没有真实消费者文本。系统不会用 synthetic 数据补空。' if zh else 'This research currently has no real consumer text. The system will not fill that gap with synthetic reviews.'

    if any(k in q for k in ['痛点','问题','barrier','issue','最值得']):
        xs=summary.get('issues',[])[:5]
        if not xs:return '当前真实样本中没有识别出足够稳定的消费者主题。' if zh else 'The current real sample does not contain stable enough consumer topics.'
        body='\n'.join(f"{i+1}. {x['name']}: {x['count']} rows, sample share {x['share']}%, decision-impact {x['purchase_impact_rate']}%, confidence {x['confidence']}" for i,x in enumerate(xs))
        return ('当前 Top topics / barriers：\n'+body+'\n\n请点击 Consumer Voice 回看来源再下结论。') if zh else ('Top topics / barriers in the current sample:\n'+body+'\n\nOpen Consumer Voice to inspect source evidence before making a decision.')

    if any(k in q for k in ['正面','driver','为什么买']):
        xs=summary.get('drivers',[])[:5]
        if zh:return 'Top positive drivers：\n'+'\n'.join(f"{i+1}. {x['name']}：{x['count']} 条" for i,x in enumerate(xs)) if xs else '当前样本里正面驱动信号不足。'
        return 'Top positive drivers:\n'+'\n'.join(f"{i+1}. {x['name']}: {x['count']} rows" for i,x in enumerate(xs)) if xs else 'Positive-driver evidence is currently weak.'

    if any(k in q for k in ['机会','opportunity','新品','做什么']):
        xs=opportunities[:5]
        if not xs:return '当前 evidence 不足以生成 opportunity hypothesis。' if zh else 'There is not enough evidence to generate opportunity hypotheses.'
        lines=[]
        for i,x in enumerate(xs):
            d=x.get('decision') or {};lines.append(f"{i+1}. {x['name']}: priority {x['opportunity_score']}/100; {x['confidence']} confidence"+(f"; next={d.get('next_validation')}" if d.get('next_validation') else ''))
        return ('Opportunity hypotheses（不是市场空白证明）：\n'+'\n'.join(lines)+'\n\n优先级用于决定下一步验证资源，不代表 TAM / revenue。') if zh else ('Opportunity hypotheses (not proof of whitespace):\n'+'\n'.join(lines)+'\n\nPriority is for allocating validation effort; it is not TAM or revenue.')

    if any(k in q for k in ['销量','畅销','best seller','产品']):
        xs=products[:10];body='\n'.join(f"{i+1}. [{x.get('source')}] {x.get('title')} | price={x.get('price')} {x.get('currency') or ''} | rating={x.get('rating')} | reviews={x.get('review_count')}" for i,x in enumerate(xs))
        return ('系统不会把 review count 冒充销量。当前可展示的是商品事实/零售信号：\n'+body) if zh else ('The system never treats review count as unit sales. Available evidence is limited to product facts / retail signals:\n'+body)

    if demo.get('executive_recommendation'):
        if zh:return f"当前决策摘要：{demo['executive_recommendation']}\n\nEvidence confidence：{summary.get('evidence_confidence',{}).get('label','—')}。你可以继续问：产品先验证什么、GTM message、US vs AU 是否可比、证据哪里最弱。"
        return f"Current decision summary: {demo['executive_recommendation']}\n\nEvidence confidence: {summary.get('evidence_confidence',{}).get('label','—')}. You can ask what product should validate first, the strongest GTM message, whether US/AU can be compared, or where evidence is weakest."
    return (f"当前研究已收集 {summary['review_count']} 条消费者证据、{summary['product_count']} 个商品结果、{summary['trend_points']} 个趋势点。Evidence confidence: {summary['evidence_confidence']['label']}。" if zh else f"This research contains {summary['review_count']} consumer evidence rows, {summary['product_count']} product signals and {summary['trend_points']} trend points. Evidence confidence: {summary['evidence_confidence']['label']}.")


app.mount('/',StaticFiles(directory=STATIC,html=True),name='static')
