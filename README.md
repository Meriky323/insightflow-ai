# InsightFlow AI

**AI-powered Overseas Consumer Insight & New Product Opportunity Platform**

InsightFlow turns fragmented product signals, consumer reviews and search trends into an auditable research workflow for new-product and GTM decisions.

> Current portfolio case: Magnetic Power Bank · US / AU

## Business problem

海外新品调研通常需要在商品页、零售评论、视频平台和趋势工具之间反复切换。InsightFlow 将这些信号整合为：

**Market Landscape → Competitor Benchmark → Consumer Voice → Drivers & Barriers → Opportunity Map → GTM Recommendation**

它重点回答：用户为什么买、为什么不买、哪些问题真正影响购买、竞品解决到了什么程度，以及哪些方向值得继续做新品验证。

## Research framework

**产品属性 → 情绪 → 痛点 / 购买驱动 → 使用场景 → 购买影响**

系统保留原始证据，并将消费者关注度、购买影响与竞品覆盖信号交叉分析，形成 Opportunity Map。Opportunity 是待验证的业务假设，不被包装成“市场绝对空白”。

## Real-data sources

- Google Shopping — products / price / rating / review-count signals
- Walmart — products and real review text
- YouTube — public videos and public comments
- Google Trends — interest-over-time signals

No synthetic-review fallback is used. If a source returns no real data, the interface shows no data instead of generating fake rows.

## Core workflow

```text
Product keyword + market + time window
                ↓
        Real-data collection
                ↓
       Competitor benchmark
                ↓
      Consumer voice analysis
                ↓
 Drivers / Barriers / Trade-offs
                ↓
         Opportunity Map
                ↓
          AI Researcher
                ↓
        PDF / DOCX / CSV
```

## Portfolio links

- Online Demo: to be added after Railway deployment
- Case Study: in preparation

## Run locally

On Windows, double-click `START_WINDOWS.bat`, or run:

```powershell
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000` and configure a SerpApi key in local mode.

## Public deployment

The repository includes `railway.toml`. Recommended portfolio deployment:

**GitHub → Railway → insightflow.meriky.online**

On Railway set `SERPAPI_API_KEY` and `PUBLIC_DEPLOYMENT=1`. Attach a persistent Volume at `/data`; the app automatically uses `RAILWAY_VOLUME_MOUNT_PATH` for SQLite and report exports.

## Data integrity & boundaries

- Review count / ranking signals are never presented as actual unit sales.
- YouTube comments are labeled `GLOBAL` when author country cannot be reliably determined.
- Amazon review text is not scraped through anti-bot bypasses.
- Reddit is not enabled by default because it requires a separate compliant API path.
- Opportunity scores are hypothesis prioritization, not proof of product-market fit.

## Stack

Python · FastAPI · SQLite · SerpApi · HTML/CSS/JavaScript · optional OpenAI-compatible LLM
