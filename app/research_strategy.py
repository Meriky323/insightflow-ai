from __future__ import annotations


def community_queries(keyword: str, objective: str = 'gtm', depth: str = 'standard') -> list[str]:
    """Return a small, deterministic intent plan for real community discovery.

    The point is coverage, not query spam. Quick uses one broad discovery call,
    Standard adds one decision-relevant intent, and Deep adds a third angle.
    SerpAPI/Google remains the source of the actual public evidence.
    """
    k=' '.join((keyword or '').split()).strip()
    if not k:
        return []
    objective=(objective or 'gtm').lower()
    depth=(depth or 'standard').lower()
    plans={
        'gtm': [k, f'{k} problems complaints review', f'{k} alternatives comparison worth it'],
        'product_launch': [k, f'{k} problems drawbacks wish feature', f'{k} long term review issues'],
        'competitor': [k, f'{k} alternatives vs comparison', f'{k} complaints switching from competitor'],
        'content': [k, f'{k} questions review reddit forum', f'{k} how to use tips problems'],
    }
    items=plans.get(objective,plans['gtm'])
    count=1 if depth=='quick' else 3 if depth=='deep' else 2
    out=[]
    for q in items[:count]:
        q=' '.join(q.split())
        if q and q not in out:
            out.append(q)
    return out
