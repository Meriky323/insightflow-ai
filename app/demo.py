from __future__ import annotations

import json
from datetime import datetime, timezone
from . import db

DEMO_TITLE = 'Magnetic Power Bank · US / AU'
DEMO_KEYWORD = '10000mAh magnetic power bank'
DEMO_MARKETS = ['US', 'AU']
DEMO_DAYS = 730
DEMO_SOURCE_KEY = ['curated_public_evidence']
DEMO_SCHEMA_VERSION = '1.5'

# Every text row below is a concise paraphrase of the linked public source, not a verbatim quote.
# The purpose of the built-in snapshot is recruiter UX: it lets a reviewer explore a grounded case
# without consuming the owner's API quota. It is intentionally small and transparent about coverage.

BASELINE_REVIEWS = [
    dict(id='b01', date='2024-09-06', url='https://www.reddit.com/r/MagSafe/comments/1faewlu/the_new_slim_version_anker_maggo_powerbank_10k_is/', text='A user preferred the new slim 10K because the previous model felt too heavy and bulky for regular handling.', sentiment='positive', topics=['Portability & slimness','Feature trade-offs'], driver='Slimmer daily-carry form factor', barrier=None, impact='Preference shift', scenario='Daily carry'),
    dict(id='b02', date='2024-09-06', url='https://www.reddit.com/r/MagSafe/comments/1faewlu/the_new_slim_version_anker_maggo_powerbank_10k_is/', text='The same discussion noted that the older magnetic pack could become hot enough to stop charging after a short period.', sentiment='negative', topics=['Heat & thermal management','Charging reliability'], driver=None, barrier='Heat can interrupt charging', impact='Blocked usage', scenario='Phone-in-hand charging'),
    dict(id='b03', date='2024-09-26', url='https://www.reddit.com/r/anker/comments/1fq1g2t', text='Early owners described the slim 10K as unexpectedly thin and premium-feeling when attached to the phone.', sentiment='positive', topics=['Portability & slimness','Build quality'], driver='Premium compact feel', barrier=None, impact='Recommend / repeat', scenario='Daily carry'),
    dict(id='b04', date='2024-09-26', url='https://www.reddit.com/r/anker/comments/1fq1g2t', text='One owner said the slim format mattered more than a small difference in wireless charging speed because wired charging remained the performance option.', sentiment='positive', topics=['Portability & slimness','Charging speed','Feature trade-offs'], driver='Slimness over marginal speed', barrier=None, impact='Preference shift', scenario='Daily carry'),
    dict(id='b05', date='2024-09-26', url='https://www.reddit.com/r/anker/comments/1fq1g2t', text='Discussion around Qi2 still focused on thermal throttling: some competing packs charged slower under sustained heat.', sentiment='negative', topics=['Heat & thermal management','Charging speed','Qi2 certification'], driver=None, barrier='Thermal throttling', impact='Brand comparison', scenario='Wireless charging'),
    dict(id='b06', date='2024-11-23', url='https://www.reddit.com/r/anker/comments/1gxykoo/review_top_5_qi_2_10000_mah_powerbanks_including/', text='A comparison thread showed that by late 2024 multiple brands were competing in the 10K Qi2 segment, increasing price and performance choice.', sentiment='neutral', topics=['Competitive intensity','Value for money','Qi2 certification'], driver='More alternatives', barrier='Harder brand choice', impact='Brand comparison', scenario='Purchase research'),
    dict(id='b07', date='2025-04-22', url='https://www.reddit.com/r/MagSafe/comments/1k5fg41/looking_for_the_best_magsafe_battery_pack/', text='Shoppers explicitly evaluated magnetic battery packs on charging speed, capacity-to-size ratio, durability and value.', sentiment='neutral', topics=['Charging speed','Portability & slimness','Reliability & durability','Value for money'], driver='Balanced performance', barrier=None, impact='Purchase criteria', scenario='Purchase research'),
    dict(id='b08', date='2025-04-22', url='https://www.reddit.com/r/MagSafe/comments/1k5fg41/looking_for_the_best_magsafe_battery_pack/', text='A recommended 10K Qi2 model was praised for good thermals, thinness and strong value when discounted.', sentiment='positive', topics=['Heat & thermal management','Portability & slimness','Value for money'], driver='Thin + cool + good value', barrier=None, impact='Recommend / repeat', scenario='Daily carry'),
    dict(id='b09', date='2025-05-13', url='https://www.reddit.com/r/MagSafe/comments/1klgag3/looking_for_a_new_slim_magsafe_bank/', text='A shopper replacing an older pack complained about slow charging and poor in-hand feel, then prioritized a slim Qi2-certified replacement.', sentiment='negative', topics=['Charging speed','Portability & slimness','Qi2 certification'], driver=None, barrier='Slow and uncomfortable', impact='Switch brand', scenario='Daily carry'),
    dict(id='b10', date='2025-06-03', url='https://www.reddit.com/r/MagSafe/comments/1l2jeo1', text='Users compared a screen-and-stand model with the slim version and often accepted fewer extras in exchange for easier carry.', sentiment='positive', topics=['Feature trade-offs','Portability & slimness'], driver='Less bulk from fewer extras', barrier=None, impact='Preference shift', scenario='Daily carry'),
    dict(id='b11', date='2025-06-03', url='https://www.reddit.com/r/MagSafe/comments/1l2jeo1', text='The regular 10K was described as noticeably bulky and heavy when actually using the phone while it was attached.', sentiment='negative', topics=['Portability & slimness','Weight & hand feel'], driver=None, barrier='Bulky while using phone', impact='Switch format', scenario='Phone-in-hand charging'),
    dict(id='b12', date='2025-06-17', url='https://www.reddit.com/r/MagSafe/comments/1ldvibz', text='Price-conscious shoppers asked for a 10K magnetic pack that would not break the bank and compared several budget alternatives.', sentiment='neutral', topics=['Value for money','Capacity'], driver='Affordable 10K', barrier='Premium pricing', impact='Brand comparison', scenario='Purchase research'),
    dict(id='b13', date='2025-06-17', url='https://www.reddit.com/r/MagSafe/comments/1ldvibz', text='Some users warned that certain magnetic packs ran hot, making thermal behavior a reason to avoid a brand.', sentiment='negative', topics=['Heat & thermal management','Reliability & durability'], driver=None, barrier='Heat damages trust', impact='Avoid brand', scenario='Wireless charging'),
    dict(id='b14', date='2025-06-17', url='https://www.reddit.com/r/MagSafe/comments/1ldvibz', text='Other users described compact budget models as pocketable and satisfactory, showing that portability and price could outweigh premium branding.', sentiment='positive', topics=['Portability & slimness','Value for money'], driver='Pocketable value', barrier=None, impact='Recommend / repeat', scenario='Daily carry'),
]

CURRENT_REVIEWS = [
    dict(id='c01', date='2025-12-24', url='https://www.reddit.com/r/MagSafe/comments/1puzgxd/best_ultraslim_10k_mah_magsafe_power_bank/', text='A shopper defined the ideal pack as 10,000mAh, as slim as possible, not too hot, from a trusted brand and Qi2-certified.', sentiment='neutral', topics=['Capacity','Portability & slimness','Heat & thermal management','Reliability & durability','Qi2 certification'], driver='Compact trusted Qi2 package', barrier=None, impact='Purchase criteria', scenario='Purchase research'),
    dict(id='c02', date='2025-12-25', url='https://www.reddit.com/r/MagSafe/comments/1puzgxd/best_ultraslim_10k_mah_magsafe_power_bank/', text='A recommended alternative was valued because its cable could be carried as a lanyard, reducing the need to pack an extra cable.', sentiment='positive', topics=['Built-in / carried cable','Portability & slimness'], driver='Fewer loose accessories', barrier=None, impact='Recommend / repeat', scenario='Travel'),
    dict(id='c03', date='2026-05-18', mentions=['Anker'], url='https://www.reddit.com/r/MagSafe/comments/1tgi9yu/anker_maggo_slim_10000_mah_opinions/', text='An owner measured roughly 12–14W wireless charging and said performance changed with phone temperature.', sentiment='neutral', topics=['Charging speed','Heat & thermal management'], driver='Acceptable real-world speed', barrier='Temperature-dependent performance', impact='Performance trade-off', scenario='Wireless charging'),
    dict(id='c04', date='2026-05-18', mentions=['Anker'], url='https://www.reddit.com/r/MagSafe/comments/1tgi9yu/anker_maggo_slim_10000_mah_opinions/', text='The same owner said wired 30W output could be sustained only briefly before heat reduced power, reinforcing thermal throttling as a real use constraint.', sentiment='negative', topics=['Heat & thermal management','Charging speed','Charging reliability'], driver=None, barrier='Thermal throttling under high output', impact='Blocked usage', scenario='Fast wired charging'),
    dict(id='c05', date='2026-05-18', mentions=['Anker'], url='https://www.reddit.com/r/MagSafe/comments/1tgi9yu/anker_maggo_slim_10000_mah_opinions/', text='Case geometry can interfere with magnetic attachment because the pack closely matches the phone body dimensions.', sentiment='negative', topics=['Compatibility & fit','Magnetic strength','Portability & slimness'], driver=None, barrier='Case and corner interference', impact='Blocked purchase', scenario='Daily carry'),
    dict(id='c06', date='2026-07-05', mentions=['Anker','UGREEN','INIU','Baseus'], url='https://www.reddit.com/r/MagSafe/comments/1unqywy/i_know_this_gets_asked_a_lot_but_best_10k_mah/', text='A recent buyer under a $70 budget prioritized long-term reliability after problems with a premium competitor and compared trusted brands on warranty and quality.', sentiment='neutral', topics=['Value for money','Reliability & durability','Brand trust'], driver='Trusted quality at a rational price', barrier='Reliability risk', impact='Switch brand', scenario='Purchase research'),
    dict(id='c07', date='2026-07-05', mentions=['Anker','UGREEN','INIU','Baseus'], url='https://www.reddit.com/r/MagSafe/comments/1unqywy/i_know_this_gets_asked_a_lot_but_best_10k_mah/', text='The conversation showed consumers now compare Anker, UGREEN, INIU, Baseus and others rather than defaulting to one established brand.', sentiment='neutral', topics=['Competitive intensity','Value for money','Brand trust'], driver='Broader brand choice', barrier='Brand uncertainty', impact='Brand comparison', scenario='Purchase research'),
    dict(id='c08', date='2026-08-25', url='https://www.reddit.com/r/MagSafe/comments/1vyatw2/whats_your_favourite_magsafe_powerbank_for_s25/', text='A small-phone user worried that most 10K packs extend below the device and make the combination uncomfortable.', sentiment='negative', topics=['Compatibility & fit','Portability & slimness','Weight & hand feel'], driver=None, barrier='Pack footprint exceeds phone size', impact='Blocked purchase', scenario='Daily carry'),
    dict(id='c09', date='2026-08-27', mentions=['Baseus'], url='https://www.reddit.com/r/MagSafe/comments/1vyatw2/whats_your_favourite_magsafe_powerbank_for_s25/', text='A Baseus user reported good wired and wireless speed without excessive heat, showing that thermal performance can become a brand differentiator.', sentiment='positive', topics=['Charging speed','Heat & thermal management','Brand trust'], driver='Fast charging without excessive heat', barrier=None, impact='Recommend / repeat', scenario='Wireless charging'),
    dict(id='c10', date='2026-05-18', mentions=['Anker'], url='https://www.reddit.com/r/MagSafe/comments/1tgi9yu/anker_maggo_slim_10000_mah_opinions/', text='The slim Anker pack was still described as well-built and not thick, so form factor remained a clear positive despite thermal caveats.', sentiment='positive', topics=['Portability & slimness','Build quality'], driver='Slim premium construction', barrier=None, impact='Recommend / repeat', scenario='Daily carry'),
    dict(id='c11', date='2026-07-05', url='https://www.reddit.com/r/MagSafe/comments/1unqywy/i_know_this_gets_asked_a_lot_but_best_10k_mah/', text='The buyer explicitly wanted evidence before considering a less familiar brand, making warranty and service credibility part of the purchase decision.', sentiment='neutral', topics=['Brand trust','Reliability & durability','Service & warranty'], driver='Proof of reliability', barrier='Weak brand assurance', impact='Purchase criteria', scenario='Purchase research'),
    dict(id='c12', date='2026-08-25', url='https://www.reddit.com/r/MagSafe/comments/1vyatw2/whats_your_favourite_magsafe_powerbank_for_s25/', text='The user considered abandoning magnetic charging for a normal power bank plus short cable if the attached 10K form factor remained awkward.', sentiment='negative', topics=['Portability & slimness','Compatibility & fit','Feature trade-offs'], driver=None, barrier='Magnetic convenience loses to ergonomics', impact='Switch format', scenario='Daily carry'),
    dict(id='c13', date=None, mentions=['ESR'], url='https://www.esrtech.com/en-ca/products/qi2-magslim-power-bank-10k', text='One customer review liked the build quality but found the magnet weaker than expected and reported charging stopping around 80%.', sentiment='negative', topics=['Magnetic strength','Charging reliability','Build quality'], driver='Quality feel', barrier='Weak magnet / early stop', impact='Dissatisfaction', scenario='Wireless charging', source='ESR Customer Reviews'),
    dict(id='c14', date=None, mentions=['ESR'], url='https://www.esrtech.com/en-ca/products/qi2-magslim-power-bank-10k', text='Another customer review described the pack as compact enough for a pocket, durable-feeling and reasonably fast.', sentiment='positive', topics=['Portability & slimness','Build quality','Charging speed'], driver='Pocketable and solid', barrier=None, impact='Recommend / repeat', scenario='Daily carry', source='ESR Customer Reviews'),
    dict(id='c15', date=None, mentions=['ESR'], url='https://www.esrtech.com/en-ca/products/qi2-magslim-power-bank-10k', text='Customer ratings on the product page are strongly positive overall, but the negative review highlights that magnetic strength can still undermine an otherwise compact product.', sentiment='neutral', topics=['Magnetic strength','Portability & slimness'], driver='Compact form factor', barrier='Magnetic confidence', impact='Purchase criteria', scenario='Purchase research', source='ESR Customer Reviews'),
    dict(id='c16', date='2026-07-05', mentions=['Anker'], url='https://www.reddit.com/r/MagSafe/comments/1unqywy/i_know_this_gets_asked_a_lot_but_best_10k_mah/', text='Premium pricing alone no longer guarantees preference; users explicitly weigh newer Qi2.2 options against price, reliability and long-term ownership feedback.', sentiment='neutral', topics=['Value for money','Qi2 certification','Reliability & durability','Competitive intensity'], driver='Evidence-backed value', barrier='Premium price without clear advantage', impact='Brand comparison', scenario='Purchase research'),
    dict(id='c17', date='2025-12-24', url='https://www.reddit.com/r/MagSafe/comments/1puzgxd/best_ultraslim_10k_mah_magsafe_power_bank/', text='Thermal comfort is now written into the initial shopping brief alongside capacity and slimness rather than appearing only as a post-purchase complaint.', sentiment='neutral', topics=['Heat & thermal management','Purchase criteria'], driver='Cool-to-touch confidence', barrier='Heat anxiety', impact='Purchase criteria', scenario='Purchase research'),
    dict(id='c18', date='2026-08-25', url='https://www.reddit.com/r/MagSafe/comments/1vyatw2/whats_your_favourite_magsafe_powerbank_for_s25/', text='Smaller Android devices expose a fit problem that iPhone-focused designs can hide, suggesting device footprint should be validated beyond the core iPhone use case.', sentiment='negative', topics=['Compatibility & fit','Android compatibility','Portability & slimness'], driver=None, barrier='iPhone-centric footprint', impact='Blocked purchase', scenario='Android daily carry'),
]

PRODUCTS = [
    {
        'source':'Anker Official','market':'US','external_id':'A1664-US','title':'Anker MagGo Power Bank (10K, Slim)','url':'https://www.anker.com/products/a1664-maggo-10000mah-power-bank','price':None,'currency':'USD','rating':4.8,'review_count':583,'seller':'Anker','badge':'Qi2 15W · 30W USB-C · 0.58 in',
        'raw':{'features':['10,000mAh','Qi2 15W','30W USB-C','ultra-slim','aerogel / thermal management','premium metal frame']}
    },
    {
        'source':'UGREEN Official','market':'US','external_id':'65958-US','title':'UGREEN MagFlow Magnetic Wireless Power Bank 10000mAh Qi2 25W','url':'https://us.ugreen.com/products/ugreen-25w-magnetic-power-bank-10000mah','price':54.97,'currency':'USD','rating':None,'review_count':18,'seller':'UGREEN','badge':'Qi2 25W · built-in 30W USB-C cable',
        'raw':{'features':['10,000mAh','Qi2 25W','30W two-way USB-C','built-in cable','17 magnets','thermal guard','13-layer protection']}
    },
    {
        'source':'Baseus Official','market':'US','external_id':'P10080000123-00','title':'Baseus Qi2 Magsafe Power Bank 22.5W 10000mAh','url':'https://www.baseus.com/products/qi2-magsafe-power-bank-22-5w-10000-mah','price':None,'currency':'USD','rating':None,'review_count':None,'seller':'Baseus','badge':'Qi2 15W · 22.5W wired',
        'raw':{'features':['10,000mAh','Qi2 15W','22.5W wired','magnetic snap','pocket size','over-charge protection']}
    },
    {
        'source':'Belkin Official','market':'US','external_id':'BPD016','title':'Belkin BoostCharge Slim Magnetic Power Bank 10K 15W','url':'https://www.belkin.com/support-article/?articleNum=337523','price':None,'currency':'USD','rating':None,'review_count':None,'seller':'Belkin','badge':'Qi2 15W · 30W USB-C · passthrough',
        'raw':{'features':['10,000mAh','Qi2 15W','30W USB-C','ultra-slim','kickstand','passthrough charging','2-year warranty']}
    },
    {
        'source':'Anker Official','market':'AU','external_id':'A1664-AU','title':'Anker MagGo Power Bank (Ultra-Slim, 10K, MagSafe)','url':'https://www.anker.com/au/products/a1664-maggo-10000mah-power-bank','price':99.95,'currency':'AUD','rating':None,'review_count':1120,'seller':'Anker','badge':'Qi2 15W · ultra-slim',
        'raw':{'features':['10,000mAh','Qi2 15W','ultra-slim','ergonomic portability','thermal management']}
    },
    {
        'source':'UGREEN Official','market':'AU','external_id':'65958-AU','title':'UGREEN MagFlow Magsafe Power Bank Qi2 25W 10000mAh','url':'https://www.ugreen.com/en-au/products/au-65958','price':None,'currency':'AUD','rating':None,'review_count':None,'seller':'UGREEN','badge':'Qi2 25W · built-in cable · 254g',
        'raw':{'features':['10,000mAh','Qi2 25W','30W built-in cable','17 N52 magnets','travel / airport positioning','13-layer protection']}
    },
    {
        'source':'Belkin Official','market':'AU','external_id':'BPD016-AU','title':'Belkin BoostCharge Slim Magnetic Power Bank 10K with Qi2','url':'https://www.belkin.com/au/p/slim-magnetic-power-bank-10k-with-qi2/BPD016fqBK.html','price':None,'currency':'AUD','rating':None,'review_count':None,'seller':'Belkin','badge':'Qi2 15W · 30W USB-C · travel-ready',
        'raw':{'features':['10,000mAh','Qi2 15W','30W USB-C','slim design','kickstand','TSA carry-on compliant','2-year warranty']}
    },
    {
        'source':'ESR Official','market':'GLOBAL','external_id':'ESR-QI2-MAGSLIM-10K','title':'ESR Qi2 MagSlim Power Bank (10K)','url':'https://www.esrtech.com/en-ca/products/qi2-magslim-power-bank-10k','price':None,'currency':'CAD','rating':None,'review_count':44,'seller':'ESR','badge':'Qi2 10K · customer-review evidence',
        'raw':{'features':['10,000mAh','Qi2','compact','portable','customer review evidence']}
    },
]

DECISION = {
    'demo_meta': {
        'portfolio_demo': True,
        'demo_schema_version': DEMO_SCHEMA_VERSION,
        'title': DEMO_TITLE,
        'snapshot_date': '2026-08-31',
        'business_question': 'For a crowded 10K magnetic power-bank category, what should product and GTM teams validate before launch — and which US/AU claims are not supported yet?',
        'executive_recommendation': 'Prioritize usable-in-hand slimness and thermal stability as core proof points; validate device fit and magnetic retention before launch, and do not claim US-vs-AU consumer preference differences until comparable voice data exists.',
        'decision_principle': 'Make the strongest decision the evidence supports — and block the rest.',
        'teams': ['Consumer Insights','Product','GTM / Marketing'],
        'method': 'Curated public-evidence snapshot. Consumer text is concise paraphrase of linked public sources; product facts come from linked official/retail pages. No synthetic reviews.',
        'baseline_period': '2024-09 to 2025-06',
        'current_period': '2025-12 to 2026-08',
        'limitations': [
            'The built-in demo is intentionally compact and is not a population-representative market survey.',
            'Most consumer voice is GLOBAL Reddit evidence; the app therefore blocks US-vs-AU consumer preference claims.',
            'Prices and review counts are source snapshots and can change after the snapshot date; uncertain marketplace metrics are intentionally omitted.',
            'Live research is the path for fresh Google Trends / retail / YouTube collection.'
        ]
    },
    'opportunities': [
        {
            'name':'Portability & slimness',
            'insight':'Slimness is no longer a cosmetic preference; it changes whether users can keep the pack attached while actually using the phone.',
            'product_action':'Prioritize thickness, footprint and weight as first-class requirements; benchmark one-handed use on both Pro-size and smaller Android devices.',
            'gtm_action':'Lead with usable-in-hand portability and pocket comfort, not only capacity. Show attached-phone side profiles and real carry scenarios.',
            'next_validation':'Run a physical benchmark of 5 leading 10K packs: thickness, weight, phone overhang, one-hand comfort and pocketability.'
        },
        {
            'name':'Heat & thermal management',
            'insight':'Thermal behavior appears both as a post-purchase complaint and as a pre-purchase screening criterion, while brands increasingly market thermal-control claims.',
            'product_action':'Treat sustained thermal performance and throttling curves as a product requirement, not just a safety checklist item.',
            'gtm_action':'If validated, convert thermal performance into proof-based messaging such as sustained output / cooler-to-touch benchmark rather than generic safety claims.',
            'next_validation':'Instrument 20–80% wireless-charge tests at controlled ambient temperature and compare surface temperature plus delivered wattage over time.'
        },
        {
            'name':'Value for money',
            'insight':'The segment is crowded enough that premium branding alone is not a durable advantage; buyers compare price, warranty, reliability and newer charging specs together.',
            'product_action':'Define the minimum feature bundle that creates a clear price-performance step-up: Qi2, compact body, stable thermals and strong warranty support.',
            'gtm_action':'Position against a concrete value equation instead of “premium” alone: price vs wireless speed vs form factor vs ownership confidence.',
            'next_validation':'Build a price-feature matrix for the top 10 US/AU offers and test willingness-to-pay for 15W vs 25W, slimness and built-in cable.'
        },
        {
            'name':'Compatibility & fit',
            'insight':'A 10K pack can be acceptable on large iPhones but awkward on smaller devices or with raised-edge cases, creating a hidden addressable-fit problem.',
            'product_action':'Validate geometry across iPhone and Android device sizes, camera bumps and common magnetic cases before finalizing industrial design.',
            'gtm_action':'Use explicit device-fit visuals and dimensions; avoid implying universal comfort from iPhone-only hero imagery.',
            'next_validation':'Create a device/case fit matrix covering iPhone Pro/Pro Max, Galaxy S25-class compact phones and representative magnetic cases.'
        },
        {
            'name':'Magnetic strength',
            'insight':'Compactness is not sufficient if magnetic hold feels insecure; magnet confidence affects perceived quality and willingness to use the pack while moving.',
            'product_action':'Set a magnetic retention target and test removal force with common cases, not only bare phones.',
            'gtm_action':'Demonstrate secure snap and movement stability with measurable proof rather than visual-only claims.',
            'next_validation':'Benchmark pull force and slip resistance across leading packs and 5 popular case constructions.'
        }
    ]
}


def _make_rows(items: list[dict]) -> list[dict]:
    rows=[]
    for x in items:
        source=x.get('source') or 'Reddit'
        topics=x['topics']
        rows.append({
            'source':source,
            'market':'GLOBAL',
            'product_external_id':None,
            'product_title':None,
            'review_external_id':f'demo-{x["id"]}',
            'title':'Curated public evidence',
            'text':x['text'],
            'rating':None,
            'author':'curated paraphrase',
            'review_date':x['date'],
            'url':x['url'],
            'helpful':None,
            'sentiment':x['sentiment'],
            'issue':topics[0] if topics else None,
            'topics_json':json.dumps(topics,ensure_ascii=False),
            'driver':x.get('driver'),
            'barrier':x.get('barrier'),
            'purchase_impact':x.get('impact'),
            'scenario':x.get('scenario'),
            'competitor_mentions_json':json.dumps(x.get('mentions') or [],ensure_ascii=False),
            'analysis_mode':'curated-demo',
            'window_status':'verified' if x.get('date') else 'unknown',
        })
    return rows


def _find_existing_demo():
    for r in db.list_researches(100):
        try:
            d=json.loads(r.get('decision_json') or '{}')
        except Exception:
            d={}
        meta=d.get('demo_meta') or {}
        if meta.get('portfolio_demo') and str(meta.get('demo_schema_version') or '') == DEMO_SCHEMA_VERSION:
            return r
    return None


def _set_created_at(research_id:int, iso_value:str):
    with db.conn() as c:
        c.execute('UPDATE researches SET created_at=?, completed_at=? WHERE id=?',(iso_value,iso_value,research_id))


def seed_portfolio_demo(force: bool = False) -> dict:
    existing=_find_existing_demo()
    if existing and not force:
        return {'current_id':existing['id'],'created':False,'message':'Existing recruiter demo opened.'}

    baseline=db.create_research(DEMO_KEYWORD,DEMO_MARKETS,DEMO_DAYS,DEMO_SOURCE_KEY,'gtm')
    db.insert_reviews(baseline,_make_rows(BASELINE_REVIEWS))
    db.set_research_meta(
        baseline,
        source_status={'curated_public_evidence':{'status':'ok','rows':len(BASELINE_REVIEWS),'note':'Curated public-source paraphrases for historical comparison.'}},
        analysis_mode='curated-demo',
        decision={'demo_meta':{'portfolio_demo_baseline':True,'demo_schema_version':DEMO_SCHEMA_VERSION,'period':'2024-09 to 2025-06'}}
    )
    db.set_research_status(baseline,'completed',100,'Recruiter demo baseline · curated public evidence')
    _set_created_at(baseline,'2025-06-30T12:00:00+00:00')

    current=db.create_research(DEMO_KEYWORD,DEMO_MARKETS,DEMO_DAYS,DEMO_SOURCE_KEY,'gtm')
    db.insert_products(current,PRODUCTS)
    db.insert_reviews(current,_make_rows(CURRENT_REVIEWS))
    db.set_research_meta(
        current,
        source_status={
            'curated_public_evidence':{'status':'ok','rows':len(CURRENT_REVIEWS),'note':'Curated public-source paraphrases with traceable URLs.'},
            'product_snapshot':{'status':'ok','rows':len(PRODUCTS),'note':'Official / retail product facts captured for the portfolio snapshot.'},
            'google_trends':{'status':'not_in_demo','rows':0,'note':'Live Google Trends is intentionally not fabricated in the built-in demo.'}
        },
        analysis_mode='curated-demo',
        decision=DECISION,
    )
    db.set_research_status(current,'completed',100,'Portfolio recruiter demo · curated public evidence snapshot · 2026-08-31')
    _set_created_at(current,'2026-08-31T12:00:00+00:00')
    return {'baseline_id':baseline,'current_id':current,'created':True,'message':'Recruiter demo seeded without API usage.'}
