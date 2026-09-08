<sub>🌐 <b>中文</b> · <a href="README.en.md">English</a></sub>

<div align="center">

# InsightFlow AI

### 把分散的市场信号，变成可追溯的消费者洞察与行动建议

**Evidence-first Consumer & GTM Intelligence**

不是“让 AI 总结评论”，而是把 **证据 → 洞察 → 产品 / 营销动作 → 下一步验证** 串成一条可复用的研究链路。

</div>

---

## 为什么做这个项目

做海外新品调研、选品或内容策略时，常见的问题不是“找不到信息”，而是：

1. **信息分散**：商品、评论、视频、搜索趋势、社区讨论和竞品信息分布在不同平台；
2. **人工链路重复**：每换一个品类，都要重新搜索、复制、整理、归类；
3. **洞察容易停在表面**：很多分析只告诉你“用户喜欢 / 不喜欢什么”，却没有回答为什么买、为什么不买；
4. **AI 结论缺少证据边界**：模型可以生成很完整的答案，但不一定能告诉你哪些是事实、哪些只是待验证假设。

所以我做了 InsightFlow：**先保留证据，再做结构化分析，最后才输出行动建议。**

---

## 它解决什么问题

### 1. 消费者需求洞察

将评论与公开讨论整理成：

- 用户痛点
- 购买驱动
- 购买阻碍
- 使用场景
- 明确的购买影响
- 竞品提及与替代选择

重点不是“情绪正负”，而是回答：

> **用户为什么选择它？为什么放弃它？哪些需求会真正影响购买？**

### 2. 市场与竞品判断

将商品事实、价格、定位和消费者证据放在一起看，避免只看竞品官网卖点。

输出包括：

- 市场共性卖点
- 竞争同质化
- 消费者反复提及的问题
- 值得进一步验证的差异化方向

### 3. 从洞察到行动

InsightFlow 不把“洞察”当终点，而是继续输出：

- **Product Action**：产品 / 供给下一步做什么
- **GTM Action**：卖点、内容、本地化与上市策略下一步做什么
- **Next Validation**：下一步还需要验证什么，避免把假设写成结论

---

## 核心流程

```text
真实市场信号
Google Shopping · Walmart · YouTube · Google Trends
公开社区讨论 · CSV / JSON 外部数据
        ↓
证据层
保留来源、日期、原始文本与市场边界
        ↓
结构化分析
痛点 · 驱动 · 阻碍 · 场景 · 购买影响
        ↓
市场 / 消费者 / 竞品洞察
        ↓
机会判断
        ↓
产品动作 · GTM 动作 · 下一步验证
```

---

## 主要产品页面

| 模块 | 回答的问题 |
|---|---|
| **Executive Snapshot** | 这次研究最值得关注的结论是什么？置信度和边界在哪里？ |
| **Trend Radar** | 哪些话题 / 搜索信号正在变化？ |
| **Consumer Voice** | 消费者具体在说什么？原始证据在哪里？ |
| **Competitors** | 竞品在卖什么，消费者又如何评价？ |
| **Opportunity Board** | 哪些需求值得优先验证？下一步产品和 GTM 动作是什么？ |
| **Ask InsightFlow** | 基于已有证据继续追问，而不是脱离数据自由生成 |

---

## Portfolio Cases

### Magnetic Power Bank · US / AU

首个通用品类案例，关注便携、发热、设备适配、磁吸体验与购买取舍。

系统会主动限制不可靠的跨市场结论：当 US / AU 的消费者证据不具备可比性时，不会强行输出“哪个国家更喜欢什么”。

### Insta360 X6 · Launch Intelligence

面向目标公司的定制研究案例：在硬件参数逐渐接近的情况下，验证 **record → reframe → export → share** 的创作者工作流是否能成为更强的差异化价值。

---

## 数据来源

### 可直接采集

- Google Shopping
- Walmart Reviews
- YouTube 视频 / 评论
- Google Trends
- Google Discussions & Forums 中的公开社区讨论信号

### 可导入

CSV / JSON 可以接入合规导出的：

- TikTok / Instagram
- Brandwatch / Sprinklr 等 Social Listening
- 问卷
- CRM / 客服记录
- 其他评论或研究数据集

---

## 研究边界

这个项目刻意保留了一些“不能直接下结论”的约束：

- 不使用合成评论作为真实消费者证据
- Review Count 不等于销量
- GLOBAL 评论不会被强行归属到某个国家
- Google Trends 指数不等于市场规模
- 机会优先级用于**决定先验证什么**，不是 TAM / Sales / PMF 预测
- 跨市场消费者偏好只有在证据真正可比时才允许比较

---

## 两种使用模式

### Public Recruiter Mode

用于公开作品集展示：

- 不暴露 API Key
- 不消耗项目 Owner 的付费模型 / 搜索额度
- 使用已保存的真实案例证据
- 可查看完整研究流程与证据链

### Local Analyst Mode

本地模式可连接：

- SerpAPI
- OpenAI-compatible LLM / Sub2API
- CSV / JSON 外部证据

---

## 本地运行

```powershell
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

运行测试：

```bash
python -m pytest -q
node --check static/app.js
```

---

## 这个项目想证明什么

对我来说，InsightFlow 不是一个“AI 功能展示”，而是一次真实运营问题的产品化尝试：

> **如何把分散、重复、依赖经验的消费者研究，变成一套有证据、有边界、能指导下一步行动的流程。**

如果你是 Recruiter / Hiring Manager，可以重点看：

1. 我如何定义业务问题；
2. 我如何把消费者声音转成结构化判断；
3. 我如何区分证据、洞察和假设；
4. 我如何把洞察继续连接到 Product / GTM Action。

---

## License / Disclaimer

InsightFlow 用于探索性消费者研究、竞品框架、概念优先级和营销假设，不替代代表性市场调研、销量预测或正式 PMF 验证。
