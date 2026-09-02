from __future__ import annotations

import json
import re
import httpx
from .config import get


def llm_enabled() -> bool:
    return bool(get('LLM_API_KEY') and get('LLM_BASE_URL') and get('LLM_MODEL'))


def _chat(messages: list[dict], temperature: float = 0.1) -> str:
    if not llm_enabled():
        raise RuntimeError('LLM is not configured')
    base = get('LLM_BASE_URL').rstrip('/')
    url = base if base.endswith('/chat/completions') else base + '/chat/completions'
    headers = {
        'Authorization': f"Bearer {get('LLM_API_KEY')}",
        'Content-Type': 'application/json',
    }
    payload = {
        'model': get('LLM_MODEL'),
        'messages': messages,
        'temperature': temperature,
    }
    with httpx.Client(timeout=120) as client:
        r = client.post(url, headers=headers, json=payload)
        if r.status_code >= 400:
            raise RuntimeError(f'LLM HTTP {r.status_code}: {r.text[:300]}')
        data = r.json()
    return data['choices'][0]['message']['content']


def _json_from_text(text: str) -> dict:
    text = text.strip()
    try:
        return json.loads(text)
    except Exception:
        pass
    m = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, flags=re.S | re.I)
    if m:
        return json.loads(m.group(1))
    start = text.find('{')
    end = text.rfind('}')
    if start >= 0 and end > start:
        return json.loads(text[start:end + 1])
    raise ValueError('LLM did not return valid JSON')


def analyze_review_batch(rows: list[dict], category: str) -> dict[int, dict]:
    """Category-agnostic structured extraction for consumer voice."""
    if not rows:
        return {}
    items = []
    for i, row in enumerate(rows):
        text = ' '.join(((row.get('title') or '') + ' ' + (row.get('text') or '')).split())
        items.append({
            'i': i,
            'source': row.get('source'),
            'market': row.get('market'),
            'rating': row.get('rating'),
            'text': text[:1200],
        })

    system = (
        'You are a consumer-insights analyst. Extract only what is supported by the supplied text. '
        'Do not infer demographics, sales, market size, or facts that are not present. '
        'Use category-agnostic labels that can work for electronics, appliances, software, beauty, or other products. '
        'Return JSON only.'
    )
    schema = {
        'items': [{
            'i': 0,
            'sentiment': 'positive|neutral|negative',
            'topics': ['short aspect label, max 3'],
            'driver': 'short positive purchase/use driver or null',
            'barrier': 'short complaint/purchase barrier or null',
            'scenario': 'short usage scenario or null',
            'purchase_impact': 'Return / refund|Switch brand|Blocked purchase|Recommend / repeat|null',
            'competitor_mentions': ['brand or product names explicitly mentioned'],
        }]
    }
    user = (
        f'Product/category under research: {category}\n'
        'Analyze each item independently. Keep topic labels concise (2-6 words) and normalize synonyms. '
        'If a field is unsupported, use null or an empty list. '
        f'Return exactly this JSON shape: {json.dumps(schema, ensure_ascii=False)}\n\n'
        f'Items:\n{json.dumps(items, ensure_ascii=False)}'
    )
    data = _json_from_text(_chat([
        {'role': 'system', 'content': system},
        {'role': 'user', 'content': user},
    ], temperature=0.0))

    out: dict[int, dict] = {}
    for item in data.get('items') or []:
        try:
            idx = int(item.get('i'))
        except Exception:
            continue
        if idx < 0 or idx >= len(rows):
            continue
        sent = str(item.get('sentiment') or 'neutral').lower()
        if sent not in {'positive', 'neutral', 'negative'}:
            sent = 'neutral'
        topics = [str(x).strip() for x in (item.get('topics') or []) if str(x).strip()][:3]
        impact = item.get('purchase_impact')
        valid_impacts = {'Return / refund', 'Switch brand', 'Blocked purchase', 'Recommend / repeat'}
        if impact not in valid_impacts:
            impact = None
        out[idx] = {
            'sentiment': sent,
            'topics': topics,
            'issue': topics[0] if topics else (str(item.get('barrier')).strip() if item.get('barrier') else None),
            'driver': str(item.get('driver')).strip() if item.get('driver') else None,
            'barrier': str(item.get('barrier')).strip() if item.get('barrier') else None,
            'scenario': str(item.get('scenario')).strip() if item.get('scenario') else None,
            'purchase_impact': impact,
            'competitor_mentions': [
                str(x).strip() for x in (item.get('competitor_mentions') or []) if str(x).strip()
            ][:8],
        }
    return out


def normalize_topic_labels(labels: list[str], category: str) -> dict[str, str]:
    labels = sorted({str(x).strip() for x in labels if str(x).strip()})
    if len(labels) < 2:
        return {x: x for x in labels}
    system = (
        'You normalize consumer-insight topic labels. Merge only true synonyms or near-synonyms. '
        'Do not merge distinct needs. Return JSON only.'
    )
    user = (
        f'Category: {category}\n'
        f'Labels: {json.dumps(labels, ensure_ascii=False)}\n'
        'Return {"mapping":{"old label":"canonical label"}}. Canonical labels should be concise and reusable.'
    )
    data = _json_from_text(_chat([
        {'role': 'system', 'content': system},
        {'role': 'user', 'content': user},
    ], temperature=0.0))
    raw = data.get('mapping') or {}
    return {x: str(raw.get(x) or x).strip() for x in labels}


def ask_llm(question: str, context: dict) -> str:
    system = (
        'You are a consumer-research analyst. Use only the supplied research context. '
        'Do not invent sales figures or market facts. Clearly separate evidence from inference. '
        'When context says a source is GLOBAL, do not attribute it to a country. '
        'When comparing markets, only compare metrics whose source coverage is comparable. '
        'Answer in Chinese unless asked otherwise.'
    )
    return _chat([
        {'role': 'system', 'content': system},
        {
            'role': 'user',
            'content': (
                f"Research context:\n{json.dumps(context, ensure_ascii=False)[:52000]}"
                f"\n\nQuestion: {question}"
            ),
        },
    ], temperature=0.2)


def test_llm_connection() -> dict:
    if not llm_enabled():
        return {'ok': False, 'message': 'LLM is not configured'}
    base = get('LLM_BASE_URL').rstrip('/')
    url = base + '/models' if not base.endswith('/models') else base
    headers = {'Authorization': f"Bearer {get('LLM_API_KEY')}"}
    try:
        with httpx.Client(timeout=20) as client:
            r = client.get(url, headers=headers)
            if r.status_code >= 400:
                return {'ok': False, 'message': f'HTTP {r.status_code}: {r.text[:180]}'}
            data = r.json()
        ids = []
        for item in (data.get('data') or [])[:30]:
            if isinstance(item, dict) and item.get('id'):
                ids.append(str(item['id']))
        configured = get('LLM_MODEL')
        return {
            'ok': True,
            'message': 'AI Engine reachable',
            'configured_model': configured,
            'model_visible': configured in ids if ids else None,
            'models_sample': ids[:12],
        }
    except Exception as e:
        return {'ok': False, 'message': f'{type(e).__name__}: {e}'}


def generate_decision_brief(category: str, objective: str, summary: dict, representative_evidence: list[dict]) -> dict:
    """Turn grounded aggregate evidence into bounded Product/GTM actions once per research."""
    opps = (summary.get('opportunities') or [])[:5]
    if not opps:
        return {'opportunities': []}
    compact_evidence = []
    for r in representative_evidence[:36]:
        compact_evidence.append({
            'source': r.get('source'),
            'market': r.get('market'),
            'text': (r.get('text') or '')[:500],
            'issue': r.get('issue'),
            'driver': r.get('driver'),
            'barrier': r.get('barrier'),
            'purchase_impact': r.get('purchase_impact'),
        })
    system = (
        'You are a senior consumer-insights and GTM analyst. Use only supplied evidence. '
        'Do not claim market size, sales, demographics, causality, or product superiority unless supported. '
        'Actions must be concrete but framed as hypotheses to validate. Return JSON only.'
    )
    schema = {
        'opportunities': [{
            'name': 'topic name exactly as supplied',
            'insight': 'what the evidence indicates',
            'product_action': 'what product team should test/change',
            'gtm_action': 'what marketing/GTM team should test',
            'next_validation': 'specific next validation step',
            'caution': 'key evidence limitation',
        }]
    }
    user = (
        f'Category: {category}\nResearch objective: {objective}\n'
        f'Opportunity aggregates: {json.dumps(opps, ensure_ascii=False)}\n'
        f'Representative evidence: {json.dumps(compact_evidence, ensure_ascii=False)}\n'
        f'Return exactly this JSON shape: {json.dumps(schema, ensure_ascii=False)}'
    )
    return _json_from_text(_chat([
        {'role': 'system', 'content': system},
        {'role': 'user', 'content': user},
    ], temperature=0.1))
