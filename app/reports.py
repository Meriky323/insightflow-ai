from __future__ import annotations

import csv, io, os
from pathlib import Path
from docx import Document
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT=Path(__file__).resolve().parents[1]
DATA_DIR=Path(os.getenv('DATA_DIR') or os.getenv('RAILWAY_VOLUME_MOUNT_PATH') or (ROOT/'data'))
OUT=DATA_DIR/'exports'
OUT.mkdir(parents=True,exist_ok=True)


def _register_cjk():
    candidates=[
      Path(r'C:\Windows\Fonts\msyh.ttc'), Path(r'C:\Windows\Fonts\simhei.ttf'),
      Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'), Path('/System/Library/Fonts/PingFang.ttc')
    ]
    for p in candidates:
        if p.exists():
            try:
                pdfmetrics.registerFont(TTFont('CJK',str(p),subfontIndex=0))
                return 'CJK'
            except Exception:
                try:
                    pdfmetrics.registerFont(TTFont('CJK',str(p)))
                    return 'CJK'
                except Exception:
                    pass
    return 'Helvetica'


def write_docx(research: dict, summary: dict) -> Path:
    p=OUT/f"insightflow_research_{research['id']}.docx"
    doc=Document();doc.add_heading('InsightFlow AI · GTM Research Report',0)
    doc.add_paragraph(f"Keyword: {research['keyword']}")
    doc.add_paragraph(f"Markets: {research['markets_json']} · Window: {research['days']} days")
    doc.add_heading('Executive summary',1)
    doc.add_paragraph(f"Real consumer voices collected: {summary['review_count']}")
    doc.add_paragraph(f"Real products collected: {summary['product_count']}")
    if summary['issues']:
        x=summary['issues'][0];doc.add_paragraph(f"Top issue: {x['name']} — {x['count']} mentions, {x['purchase_impact_rate']}% purchase-impact rate")
    if summary['drivers']:
        d=summary['drivers'][0];doc.add_paragraph(f"Top positive driver: {d['name']} — {d['count']} mentions")
    doc.add_heading('Top issues',1)
    for x in summary['issues'][:10]: doc.add_paragraph(f"{x['name']}: {x['count']} ({x['share']}% of reviews), impact {x['purchase_impact_rate']}%",style='List Bullet')
    doc.add_heading('Opportunity hypotheses',1)
    for x in summary['opportunities'][:8]: doc.add_paragraph(f"{x['name']} — score {x['opportunity_score']}/100. Benchmark coverage proxy {x['benchmark_coverage']}%. Requires validation.",style='List Bullet')
    doc.add_heading('Data provenance',1)
    doc.add_paragraph('This report contains only data collected from configured real-data connectors. No synthetic review fallback is used. YouTube comments are labeled GLOBAL because comment author country is not reliably available.')
    doc.save(p);return p


def write_pdf(research: dict, summary: dict) -> Path:
    p=OUT/f"insightflow_research_{research['id']}.pdf";font=_register_cjk();c=canvas.Canvas(str(p),pagesize=A4);W,H=A4;y=H-22*mm
    def line(text,size=10,bold=False,indent=0):
        nonlocal y
        c.setFont(font,size)
        maxchars=82 if font=='Helvetica' else 52
        chunks=[str(text)[i:i+maxchars] for i in range(0,len(str(text)),maxchars)] or ['']
        for ch in chunks:
            if y<18*mm: c.showPage();c.setFont(font,size);y=H-20*mm
            c.drawString((18+indent)*mm,y,ch);y-=5.5*mm
    c.setFont(font,17);c.drawString(18*mm,y,'InsightFlow AI · GTM Research Report');y-=10*mm
    line(f"Keyword: {research['keyword']}",11);line(f"Window: {research['days']} days · Real reviews: {summary['review_count']} · Products: {summary['product_count']}",10);y-=3*mm
    line('Top issues',13)
    for x in summary['issues'][:10]: line(f"• {x['name']}: {x['count']} mentions; share {x['share']}%; purchase impact {x['purchase_impact_rate']}%",10,indent=2)
    y-=3*mm;line('Opportunity hypotheses',13)
    for x in summary['opportunities'][:8]: line(f"• {x['name']} — score {x['opportunity_score']}/100; benchmark coverage proxy {x['benchmark_coverage']}%. Validation required.",10,indent=2)
    y-=3*mm;line('Data provenance',13);line('No synthetic review fallback is used. YouTube comments are labeled GLOBAL because author country is not reliably available.',9)
    c.save();return p


def write_csv(reviews: list[dict], research_id: int) -> Path:
    p=OUT/f'insightflow_reviews_{research_id}.csv'
    fields=['source','market','product_title','title','text','rating','author','review_date','url','helpful','sentiment','issue','driver','purchase_impact','scenario']
    with p.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(reviews)
    return p
