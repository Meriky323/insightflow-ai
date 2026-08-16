from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / '.env'
load_dotenv(ENV_PATH)


def get(name: str, default: str = '') -> str:
    return os.getenv(name, default).strip()


def config_status() -> dict:
    return {
        'public_deployment': get('PUBLIC_DEPLOYMENT').lower() in {'1','true','yes'},
        'serpapi': bool(get('SERPAPI_API_KEY')),
        'llm': bool(get('LLM_API_KEY') and get('LLM_BASE_URL') and get('LLM_MODEL')),
        'llm_base_url': get('LLM_BASE_URL'),
        'llm_model': get('LLM_MODEL'),
    }


def save_settings(payload: dict) -> None:
    if get('PUBLIC_DEPLOYMENT').lower() in {'1','true','yes'}:
        raise PermissionError('Settings are managed by server environment variables in public deployment mode.')
    current = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding='utf-8').splitlines():
            if not line or line.lstrip().startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            current[k.strip()] = v.strip()

    mapping = {
        'serpapi_api_key': 'SERPAPI_API_KEY',
        'llm_api_key': 'LLM_API_KEY',
        'llm_base_url': 'LLM_BASE_URL',
        'llm_model': 'LLM_MODEL',
    }
    for src, dst in mapping.items():
        val = payload.get(src)
        if val is not None and str(val).strip() != '':
            current[dst] = str(val).strip()

    lines = [
        '# InsightFlow AI local secrets. Never commit this file.',
        f"SERPAPI_API_KEY={current.get('SERPAPI_API_KEY','')}",
        f"LLM_API_KEY={current.get('LLM_API_KEY','')}",
        f"LLM_BASE_URL={current.get('LLM_BASE_URL','')}",
        f"LLM_MODEL={current.get('LLM_MODEL','')}",
    ]
    ENV_PATH.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    load_dotenv(ENV_PATH, override=True)
