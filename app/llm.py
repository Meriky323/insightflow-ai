from __future__ import annotations

import json
import httpx
from .config import get


def llm_enabled() -> bool:
    return bool(get('LLM_API_KEY') and get('LLM_BASE_URL') and get('LLM_MODEL'))


def ask_llm(question: str, context: dict) -> str:
    if not llm_enabled():
        raise RuntimeError('LLM is not configured')
    base=get('LLM_BASE_URL').rstrip('/')
    url=base if base.endswith('/chat/completions') else base + '/chat/completions'
    headers={'Authorization':f"Bearer {get('LLM_API_KEY')}",'Content-Type':'application/json'}
    system=(
      'You are a consumer-research analyst. Use only the supplied research context. '
      'Do not invent sales figures or market facts. Clearly separate evidence from inference. '
      'When context says a source is GLOBAL, do not attribute it to a country. Answer in Chinese unless asked otherwise.'
    )
    payload={'model':get('LLM_MODEL'),'messages':[{'role':'system','content':system},{'role':'user','content':f"Research context:\n{json.dumps(context,ensure_ascii=False)[:45000]}\n\nQuestion: {question}"}], 'temperature':0.2}
    with httpx.Client(timeout=90) as client:
        r=client.post(url,headers=headers,json=payload)
        if r.status_code>=400:
            raise RuntimeError(f'LLM HTTP {r.status_code}: {r.text[:300]}')
        data=r.json()
    return data['choices'][0]['message']['content']
