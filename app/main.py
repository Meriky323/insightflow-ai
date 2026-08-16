from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import db
from .analysis import annotate, summarize
from .collectors.serpapi import SerpApiClient, SerpApiError
from .config import config_status, get, save_settings
from .llm import ask_llm, llm_enabled
from .reports import write_csv, write_docx, write_pdf

ROOT=Path(__file__).resolve().parents[1]
STATIC=ROOT/'static'

app=FastAPI(title='InsightFlow AI',version='1.0.0')
db.init_db()

class SettingsIn(BaseModel):
    serpapi_api_key: str | None = None
    llm_api_key: str | None = None
    llm_base_url: str | None = None
    llm_model: str | None = None

class ResearchIn(BaseModel):
    keyword: str = Field(min_length=2,max_length=160)
    markets: list[str] = Field(default_factory=lambda:['US'])
    days: int = Field(default=180,ge=7,le=1825)
    sources: list[Literal['shopping','walmart','youtube','trends']] = Field(default_factory=lambda:['shopping','walmart','youtube','trends'])
    shopping_limit: int = Field(default=20,ge=1,le=50)
    walmart_products: int = Field(default=3,ge=1,le=8)
    walmart_review_pages: int = Field(default=2,ge=1,le=10)
    youtube_videos_per_market: int = Field(default=3,ge=1,le=8)
    youtube_comment_pages: int = Field(default=1,ge=1,le=5)

class AskIn(BaseModel):
    question: str = Field(min_length=2,max_length=1000)

@app.get('/api/health')
def health():
    return {'ok':True,'version':'1.0.0','real_data_only':True}

@app.get('/api/config')
def cfg():
    return config_status()

@app.post('/api/settings')
def settings(payload: SettingsIn):
    try:
        save_settings(payload.model_dump())
    except PermissionError as e:
        raise HTTPException(403, str(e))
    return config_status()

@app.get('/api/researches')
def researches():
    out=[]
    for r in db.list_researches():
        r['markets']=json.loads(r.pop('markets_json'))
        r['sources']=json.loads(r.pop('sources_json'))
        out.append(r)
    return out

@app.post('/api/research')
def research_create(payload: ResearchIn):
    if not get('SERPAPI_API_KEY'):
        raise HTTPException(400,'SERPAPI_API_KEY 未配置。先在 Settings 填入 SerpApi key。')
    markets=[]
    for m in payload.markets:
        m=m.upper()
        if m not in {'US','AU','UK','CA'}: continue
        if m not in markets: markets.append(m)
    if not markets: markets=['US']
    rid=db.create_research(payload.keyword.strip(),markets,payload.days,list(payload.sources))
    thread=threading.Thread(target=_run_research,args=(rid,payload,markets),daemon=True)
    thread.start()
    return {'id':rid,'status':'queued','estimated_serpapi_calls':estimate_calls(payload,markets)}

@app.get('/api/research/{rid}')
def research_status(rid:int):
    r=db.get_research(rid)
    if not r: raise HTTPException(404,'research not found')
    r['markets']=json.loads(r.pop('markets_json'));r['sources']=json.loads(r.pop('sources_json'))
    return r

@app.get('/api/research/{rid}/summary')
def research_summary(rid:int):
    r=db.get_research(rid)
    if not r: raise HTTPException(404,'research not found')
    return summarize(db.rows_for(rid,'products'),db.rows_for(rid,'reviews'),db.rows_for(rid,'trends'))

@app.get('/api/research/{rid}/products')
def research_products(rid:int):
    return db.rows_for(rid,'products')

@app.get('/api/research/{rid}/reviews')
def research_reviews(rid:int,limit:int=Query(500,ge=1,le=5000),offset:int=Query(0,ge=0),source:str|None=None,market:str|None=None,sentiment:str|None=None,issue:str|None=None,q:str|None=None):
    rows=db.rows_for(rid,'reviews')
    def ok(x):
        if source and x.get('source')!=source:return False
        if market and x.get('market')!=market:return False
        if sentiment and x.get('sentiment')!=sentiment:return False
        if issue and x.get('issue')!=issue:return False
        if q and q.lower() not in (' '.join(str(x.get(k) or '') for k in ['title','text','issue','driver','scenario'])).lower():return False
        return True
    rows=[x for x in rows if ok(x)]
    return {'total':len(rows),'rows':rows[offset:offset+limit]}

@app.get('/api/research/{rid}/trends')
def research_trends(rid:int):
    return db.rows_for(rid,'trends')

@app.post('/api/research/{rid}/ask')
def research_ask(rid:int,payload:AskIn):
    r=db.get_research(rid)
    if not r: raise HTTPException(404,'research not found')
    products=db.rows_for(rid,'products');reviews=db.rows_for(rid,'reviews');trends=db.rows_for(rid,'trends');summary=summarize(products,reviews,trends)
    if llm_enabled():
        context={'research':r,'summary':summary,'sample_reviews':reviews[:120],'products':products[:40],'trends':trends[-80:]}
        try:return {'mode':'llm','answer':ask_llm(payload.question,context)}
        except Exception as e:return {'mode':'local-fallback','answer':_local_answer(payload.question,summary,reviews,products),'warning':str(e)}
    return {'mode':'local','answer':_local_answer(payload.question,summary,reviews,products)}

@app.get('/api/research/{rid}/export/{kind}')
def export(rid:int,kind:str):
    r=db.get_research(rid)
    if not r: raise HTTPException(404,'research not found')
    summary=summarize(db.rows_for(rid,'products'),db.rows_for(rid,'reviews'),db.rows_for(rid,'trends'))
    if kind=='csv':p=write_csv(db.rows_for(rid,'reviews'),rid);media='text/csv'
    elif kind=='docx':p=write_docx(r,summary);media='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    elif kind=='pdf':p=write_pdf(r,summary);media='application/pdf'
    else:raise HTTPException(400,'kind must be csv/docx/pdf')
    return FileResponse(p,media_type=media,filename=p.name)

def estimate_calls(p:ResearchIn, markets:list[str])->int:
    calls=0
    if 'shopping' in p.sources:calls+=len(markets)
    if 'trends' in p.sources:calls+=len(markets)
    if 'walmart' in p.sources and 'US' in markets:calls+=1+p.walmart_products*p.walmart_review_pages
    if 'youtube' in p.sources:calls+=len(markets)*(1+p.youtube_videos_per_market*p.youtube_comment_pages)
    return calls

def _run_research(rid:int,p:ResearchIn,markets:list[str]):
    try:
        db.clear_research_data(rid);db.set_research_status(rid,'running',2,'Starting real-data collection')
        client=SerpApiClient(get('SERPAPI_API_KEY'))
        products=[];reviews=[];trends=[];step=3
        if 'shopping' in p.sources:
            for m in markets:
                db.set_research_status(rid,'running',min(20,step),f'Google Shopping · {m}')
                products.extend(client.google_shopping(p.keyword,m,p.shopping_limit));step+=3
        walmart_products=[]
        if 'walmart' in p.sources and 'US' in markets:
            db.set_research_status(rid,'running',25,'Walmart search')
            walmart_products=client.walmart_search(p.keyword,max(p.walmart_products,8));products.extend(walmart_products)
            for i,prod in enumerate(walmart_products[:p.walmart_products],1):
                db.set_research_status(rid,'running',28+int(20*i/max(1,p.walmart_products)),f'Walmart reviews {i}/{p.walmart_products}')
                reviews.extend(client.walmart_reviews(prod,p.walmart_review_pages))
        if 'youtube' in p.sources:
            for mi,m in enumerate(markets,1):
                db.set_research_status(rid,'running',55+int(12*mi/max(1,len(markets))),f'YouTube search · {m}')
                vids=client.youtube_search(p.keyword,m,p.youtube_videos_per_market)
                for vid in vids:
                    reviews.extend(client.youtube_comments(vid,p.youtube_comment_pages))
        if 'trends' in p.sources:
            for mi,m in enumerate(markets,1):
                db.set_research_status(rid,'running',72+int(8*mi/max(1,len(markets))),f'Google Trends · {m}')
                trends.extend(client.google_trends(p.keyword,m,p.days))
        db.set_research_status(rid,'running',84,'Analyzing collected real reviews')
        # de-dupe before analysis
        seen=set();clean=[]
        for x in reviews:
            text=' '.join((x.get('text') or '').split())
            if not text:continue
            key=(x.get('source'),x.get('review_external_id') or text[:180])
            if key in seen:continue
            seen.add(key);x['text']=text;clean.append(annotate(x))
        # de-dupe products
        ps=[];seenp=set()
        for x in products:
            k=(x.get('source'),x.get('external_id') or x.get('url') or x.get('title'))
            if k in seenp:continue
            seenp.add(k);ps.append(x)
        db.insert_products(rid,ps);db.insert_reviews(rid,clean);db.insert_trends(rid,trends)
        db.set_research_status(rid,'completed',100,f'Completed: {len(ps)} products, {len(clean)} real reviews/comments, {len(trends)} trend points')
    except Exception as e:
        db.set_research_status(rid,'failed',100,f'{type(e).__name__}: {e}')

def _local_answer(question:str,summary:dict,reviews:list[dict],products:list[dict])->str:
    q=question.lower()
    if not reviews and ('review' in q or '评论' in q or '痛点' in q):
        return '当前研究没有抓到真实评论正文。请检查 Walmart / YouTube 数据源是否启用，以及 API 调用是否成功。系统不会用 synthetic 数据补空。'
    if any(k in q for k in ['痛点','问题','barrier','issue','最值得']):
        xs=summary.get('issues',[])[:5]
        if not xs:return '当前真实样本中没有识别出足够的具体痛点。'
        return '当前真实数据的 Top issues：\n'+ '\n'.join(f"{i+1}. {x['name']}：{x['count']} 条，占 {x['share']}%，购买影响率 {x['purchase_impact_rate']}%" for i,x in enumerate(xs))+'\n\n这些是规则化抽取结果，建议点击 Evidence 回看原文。'
    if any(k in q for k in ['正面','driver','为什么买','卖点']):
        xs=summary.get('drivers',[])[:5]
        return 'Top positive drivers：\n'+'\n'.join(f"{i+1}. {x['name']}：{x['count']} 条" for i,x in enumerate(xs)) if xs else '当前真实样本里正面驱动信号不足。'
    if any(k in q for k in ['机会','opportunity','新品','做什么']):
        xs=summary.get('opportunities',[])[:5]
        return 'Opportunity hypotheses（不是“市场确定空白”）：\n'+'\n'.join(f"{i+1}. {x['name']}：{x['opportunity_score']}/100；benchmark coverage proxy {x['benchmark_coverage']}%" for i,x in enumerate(xs))+'\n\n下一步要用供应链、成本、实物 benchmark 和更大真实样本验证。'
    if any(k in q for k in ['销量','畅销','best seller','产品']):
        xs=products[:10]
        return '系统不会把评论量冒充销量。当前可展示的是真实商品结果中的排名/价格/评分/review count：\n'+'\n'.join(f"{i+1}. [{x.get('source')}] {x.get('title')} | price={x.get('price')} {x.get('currency') or ''} | rating={x.get('rating')} | reviews={x.get('review_count')}" for i,x in enumerate(xs))
    return f"当前研究已收集 {summary['review_count']} 条真实评论/公开评论、{summary['product_count']} 个真实商品结果、{summary['trend_points']} 个趋势点。你可以问：Top痛点、正面购买驱动、新品机会假设、头部商品信号，或配置 LLM 后进行更自由的跨表分析。"

app.mount('/',StaticFiles(directory=STATIC,html=True),name='static')
