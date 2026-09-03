from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable
import hashlib
import json
import os
import time
import httpx

BASE='https://serpapi.com/search.json'
ROOT=Path(__file__).resolve().parents[2]
CACHE_DIR=Path(os.getenv('DATA_DIR') or os.getenv('RAILWAY_VOLUME_MOUNT_PATH') or (ROOT/'data'))/'cache'/'serpapi'
CACHE_TTL_SECONDS=int(os.getenv('SERPAPI_CACHE_TTL_SECONDS','21600'))  # 6h; saves quota during repeated testing


class SerpApiError(RuntimeError):
    pass


class SerpApiClient:
    def __init__(self, api_key: str, timeout: float = 45.0):
        if not api_key:
            raise SerpApiError('SERPAPI_API_KEY is missing')
        self.api_key=api_key
        self.timeout=timeout

    def _cache_path(self, params: dict) -> Path:
        safe={k:v for k,v in params.items() if k!='api_key'}
        raw=json.dumps(safe,sort_keys=True,ensure_ascii=False,default=str).encode('utf-8')
        return CACHE_DIR/(hashlib.sha256(raw).hexdigest()+'.json')

    def _cache_get(self, params: dict):
        p=self._cache_path(params)
        if not p.exists(): return None
        try:
            payload=json.loads(p.read_text(encoding='utf-8'))
            if time.time()-float(payload.get('saved_at',0))>CACHE_TTL_SECONDS:return None
            return payload.get('data')
        except Exception:
            return None

    def _cache_set(self, params: dict, data: dict):
        try:
            CACHE_DIR.mkdir(parents=True,exist_ok=True)
            self._cache_path(params).write_text(json.dumps({'saved_at':time.time(),'data':data},ensure_ascii=False),encoding='utf-8')
        except Exception:
            pass

    def search(self, **params):
        cached=self._cache_get(params)
        if cached is not None:
            return cached
        request_params={'api_key':self.api_key, **params}
        with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
            r=client.get(BASE, params=request_params)
            if r.status_code >= 400:
                raise SerpApiError(f'SerpApi HTTP {r.status_code}: {r.text[:250]}')
            data=r.json()
        if data.get('error'):
            raise SerpApiError(str(data['error']))
        self._cache_set(params,data)
        return data

    def google_shopping(self, keyword: str, market: str, limit: int = 20) -> list[dict]:
        gl=market.lower()
        data=self.search(engine='google_shopping_light', q=keyword, gl=gl, hl='en')
        rows=(data.get('shopping_results') or []) + (data.get('inline_shopping_results') or [])
        out=[]
        seen=set()
        for x in rows:
            key=(x.get('product_id'),x.get('title'),x.get('source'))
            if key in seen: continue
            seen.add(key)
            price=x.get('extracted_price')
            out.append({
              'source':'Google Shopping','market':market,'external_id':x.get('product_id'),'title':x.get('title') or '',
              'url':x.get('product_link') or x.get('link'),'price':price,'currency':_currency_from_price(x.get('price')),
              'rating':x.get('rating'),'review_count':x.get('reviews'),'seller':x.get('source'),'badge':x.get('badge') or x.get('tag'),
              'thumbnail':x.get('thumbnail') or x.get('serpapi_thumbnail'),'raw':x,
            })
            if len(out)>=limit: break
        return out

    def walmart_search(self, keyword: str, limit: int = 12) -> list[dict]:
        data=self.search(engine='walmart', query=keyword)
        rows=data.get('organic_results') or []
        out=[]
        for x in rows[:limit]:
            offer=x.get('primary_offer') or {}
            out.append({
              'source':'Walmart','market':'US','external_id':x.get('us_item_id') or x.get('product_id'),
              'title':x.get('title') or '','url':x.get('product_page_url'),'price':offer.get('offer_price'),
              'currency':offer.get('currency') or 'USD','rating':x.get('rating'),'review_count':x.get('reviews'),
              'seller':x.get('seller_name'),'badge':x.get('special_offer_text'),'thumbnail':x.get('thumbnail'),'raw':x,
            })
        return out

    def walmart_reviews(self, product: dict, max_pages: int = 2) -> list[dict]:
        product_id=product.get('external_id')
        if not product_id: return []
        out=[]
        for page in range(1,max_pages+1):
            data=self.search(engine='walmart_product_reviews', product_id=product_id, page=page, sort='relevancy')
            reviews=data.get('reviews') or []
            for x in reviews:
                out.append({
                  'source':'Walmart','market':'US','product_external_id':str(product_id),'product_title':product.get('title'),
                  'review_external_id':str(x.get('review_id') or f'{product_id}:{page}:{x.get("position",len(out)+1)}'),
                  'title':x.get('title'),'text':x.get('text') or '','rating':x.get('rating'),'author':x.get('user_nickname'),
                  'review_date':x.get('review_submission_time'),'url':product.get('url'),'helpful':x.get('positive_feedback'),
                })
            if not reviews: break
        return out


    def community_discussions(self, keyword: str, market: str = 'US', limit: int = 20) -> list[dict]:
        """Discover public forum/community evidence through Google Discussions & Forums.

        Geography here only biases discovery; author geography is not reliable, so rows are
        deliberately labelled GLOBAL. This gives the research engine real Reddit/forum snippets
        without depending on a fragile direct scraper.
        """
        data=self.search(engine='google', q=keyword, gl=market.lower(), hl='en', device='mobile')
        rows=data.get('discussions_and_forums') or []
        out=[];seen=set()
        for thread in rows:
            source=(thread.get('source') or 'Community').strip()
            title=(thread.get('title') or '').strip()
            thread_url=thread.get('link')
            date=thread.get('date')
            answers=thread.get('answers') or []
            if answers:
                for pos,a in enumerate(answers,1):
                    text=(a.get('snippet') or '').strip()
                    if not text: continue
                    url=a.get('link') or thread_url
                    key=url or f"{source}:{title}:{text[:120]}"
                    if key in seen: continue
                    seen.add(key)
                    helpful=None
                    ext=' '.join(a.get('extensions') or [])
                    import re as _re
                    m=_re.search(r'(\d[\d,]*)\s*(?:vote|votes|upvote|upvotes)', ext, _re.I)
                    if m:
                        try: helpful=int(m.group(1).replace(',',''))
                        except Exception: helpful=None
                    out.append({
                        'source':source,'market':'GLOBAL','product_external_id':None,'product_title':title,
                        'review_external_id':str(url or key),'title':title,'text':text,'rating':None,'author':None,
                        'review_date':date,'url':url,'helpful':helpful,
                    })
                    if len(out)>=limit: return out
            elif title:
                # A discussion title itself can be a real need/question signal; keep it clearly as a thread title.
                key=thread_url or f"{source}:{title}"
                if key not in seen:
                    seen.add(key)
                    out.append({
                        'source':source,'market':'GLOBAL','product_external_id':None,'product_title':title,
                        'review_external_id':str(key),'title':'Community thread','text':title,'rating':None,'author':None,
                        'review_date':date,'url':thread_url,'helpful':None,
                    })
                    if len(out)>=limit: return out
        return out

    def google_trends(self, keyword: str, market: str, days: int) -> list[dict]:
        end=datetime.now(timezone.utc).date(); start=end-timedelta(days=days)
        date=f'{start.isoformat()} {end.isoformat()}'
        data=self.search(engine='google_trends', q=keyword, geo=market, date=date, data_type='TIMESERIES')
        rows=((data.get('interest_over_time') or {}).get('timeline_data') or [])
        out=[]
        for x in rows:
            vals=x.get('values') or []
            if not vals: continue
            v=vals[0]
            out.append({'market':market,'date_label':x.get('date'),'timestamp':_int(x.get('timestamp')),'value':_float(v.get('extracted_value') if v.get('extracted_value') is not None else v.get('value'))})
        return out

    def youtube_search(self, keyword: str, market: str, max_videos: int = 4) -> list[dict]:
        data=self.search(engine='youtube', search_query=f'{keyword} review', gl=market.lower(), hl='en')
        videos=[]
        for x in data.get('video_results') or []:
            vid=x.get('video_id')
            if not vid and x.get('link') and 'v=' in x['link']:
                vid=x['link'].split('v=',1)[1].split('&',1)[0]
            if not vid: continue
            videos.append({'video_id':vid,'title':x.get('title') or '','url':x.get('link'),'channel':(x.get('channel') or {}).get('name'),'search_market':market})
            if len(videos)>=max_videos: break
        return videos

    def youtube_comments(self, video: dict, max_pages: int = 1) -> list[dict]:
        vid=video['video_id']
        data=self.search(engine='youtube_video', v=vid, hl='en')
        out=[]
        pages=0
        while True:
            for x in data.get('comments') or []:
                channel=x.get('channel') or {}
                out.append({
                  'source':'YouTube','market':'GLOBAL','product_external_id':vid,'product_title':video.get('title'),
                  'review_external_id':x.get('comment_id'),'title':None,'text':x.get('content') or x.get('text') or '',
                  'rating':None,'author':channel.get('name') or x.get('author'),'review_date':x.get('published_date') or x.get('published_time'),
                  'url':x.get('link') or video.get('url'),'helpful':x.get('extracted_likes') or x.get('likes'),
                })
            pages += 1
            if pages>=max_pages: break
            token=data.get('comments_next_page_token')
            if not token: break
            data=self.search(engine='youtube_video', next_page_token=token, hl='en')
        return out


def _currency_from_price(s):
    if not s: return None
    s=str(s)
    if 'A$' in s or 'AUD' in s: return 'AUD'
    if '$' in s: return 'USD'
    if '£' in s: return 'GBP'
    if '€' in s: return 'EUR'
    return None


def _float(v):
    try: return float(v)
    except: return None


def _int(v):
    try: return int(v)
    except: return None
