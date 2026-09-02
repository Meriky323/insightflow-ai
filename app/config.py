from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / '.env'
load_dotenv(ENV_PATH)


def get(name: str, default: str = '') -> str:
    return os.getenv(name, default).strip()


def _truthy(name: str, default: str = '') -> bool:
    return get(name, default).lower() in {'1','true','yes','on'}


def config_status() -> dict:
    public = _truthy('PUBLIC_DEPLOYMENT') or bool(get('RAILWAY_PUBLIC_DOMAIN') or get('RAILWAY_PROJECT_ID'))
    # A recruiter-facing deployment should not disclose whether server-side connector
    # credentials exist, nor reveal the configured gateway/model. Local mode keeps the
    # diagnostics visible for the project owner.
    serpapi_ready = bool(get('SERPAPI_API_KEY'))
    llm_ready = bool(get('LLM_API_KEY') and get('LLM_BASE_URL') and get('LLM_MODEL'))
    return {
        'public_deployment': public,
        'allow_public_live_research': _truthy('ALLOW_PUBLIC_LIVE_RESEARCH'),
        'serpapi': False if public else serpapi_ready,
        'llm': False if public else llm_ready,
        'llm_base_url': '' if public else get('LLM_BASE_URL'),
        'llm_model': '' if public else get('LLM_MODEL'),
    }


def _read_current() -> dict:
    current = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding='utf-8').splitlines():
            if not line or line.lstrip().startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            current[k.strip()] = v.strip()
    return current


def _write_current(current: dict) -> None:
    preferred = [
        'SERPAPI_API_KEY','LLM_API_KEY','LLM_BASE_URL','LLM_MODEL',
        'PUBLIC_DEPLOYMENT','ALLOW_PUBLIC_LIVE_RESEARCH','DATA_DIR','SERPAPI_CACHE_TTL_SECONDS'
    ]
    lines = ['# InsightFlow AI local settings. Never commit real secrets.']
    written = set()
    for key in preferred:
        if key in current or key in {'SERPAPI_API_KEY','LLM_API_KEY','LLM_BASE_URL','LLM_MODEL'}:
            lines.append(f"{key}={current.get(key,'')}")
            written.add(key)
    for key in sorted(k for k in current if k not in written):
        lines.append(f"{key}={current[key]}")
    ENV_PATH.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    load_dotenv(ENV_PATH, override=True)


def save_settings(payload: dict) -> None:
    if _truthy('PUBLIC_DEPLOYMENT') or bool(get('RAILWAY_PUBLIC_DOMAIN') or get('RAILWAY_PROJECT_ID')):
        raise PermissionError('Settings are managed by server environment variables in public deployment mode.')
    current = _read_current()
    mapping = {
        'serpapi_api_key': 'SERPAPI_API_KEY',
        'llm_api_key': 'LLM_API_KEY',
        'llm_base_url': 'LLM_BASE_URL',
        'llm_model': 'LLM_MODEL',
    }
    for src, dst in mapping.items():
        val = payload.get(src)
        # Empty fields mean "leave unchanged" so a user can edit only one connector safely.
        if val is not None and str(val).strip() != '':
            current[dst] = str(val).strip()
    _write_current(current)


def clear_settings(fields: list[str]) -> None:
    if _truthy('PUBLIC_DEPLOYMENT') or bool(get('RAILWAY_PUBLIC_DOMAIN') or get('RAILWAY_PROJECT_ID')):
        raise PermissionError('Settings are managed by server environment variables in public deployment mode.')
    allowed = {
        'serpapi': ['SERPAPI_API_KEY'],
        'llm': ['LLM_API_KEY','LLM_BASE_URL','LLM_MODEL'],
    }
    current = _read_current()
    for field in fields:
        for key in allowed.get(field, []):
            current[key] = ''
    _write_current(current)
