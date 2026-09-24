# 容量选择研究与产品改版

2026-09-24 · https://insightflow.meriky.online/

## 决策范围
假设详情页团队本轮可以改一个模块：优先测试按使用任务选择容量的模块。研究不用于决定硬件改型、淘汰 10K 或证明增长结果。

## 可核查的差异
Anker A1665 与 A1664 分别厚 8.6 / 14.7 mm、重 122 / 215.9 g，宽度均为 70.6 mm。因此“薄 6.1 mm、轻 93.9 g”不能延伸成更窄、一定适配小手机或握持更舒适。iPhone 16 的 7.8 mm 与 170 g 仅用于明确口径的加总，排除壳、镜头突起和间隙。

## 来源
- S1 https://www.anker.com/products/a1664-maggo-10000mah-power-bank
- S2 https://www.anker.com/au/products/a1665-5k-ultra-slim-qi2-power-bank
- S3 https://support.apple.com/en-us/121029
- S4 https://www.reddit.com/r/MagSafe/comments/1udb0ew/one_magnetic_bank_to_cover_a_full_day_out_does/
- S5 https://baymard.com/research-articles/product-listing-information
- S6 https://www.belkin.com/uk/p/slim-magnetic-power-bank-10k-with-qi2/BPD018hqBK.html

S4 是一条自选择社区讨论，不计作独立访谈，不估计人群比例。S5 是方法参考，不证明本品类转化效果。跨区域官方页面只取型号参数，不比较价格或地区偏好。

## 参考产品方法
参考 Dovetail 将证据置于研究判断旁的组织方式（https://dovetail.com/solutions/product-research/），以及 Product Talk 将机会、方案和验证连接的方法（https://www.producttalk.org/opportunity-solution-trees/）。界面和代码为本项目实现，没有复制这些产品的代码、品牌或素材。

## 产品与界面
首页直接呈现研究判断；左侧五个入口组成完整工作流程。白底、深绿强调、细分隔线和克制的状态标签，减少宣传式标题。规格图使用统一厚度比例，设备检查放在原型选择之前。手机端转为横向导航，正文与备注改为单列。

## 验证与限制
8 项 Node 检查通过：规格计算、来源结构、记录校验、CSV 防公式注入，以及旧公开 API 的证据边界和导出。浏览器已检查桌面 1440 与手机 390 宽度、来源筛选与弹窗、中英文切换、规格口径切换、A/B 原型、机型提醒、记录保存与刷新恢复、移除与撤销。没有进行真实用户测试；6 人方案是待执行计划。公开站不调用 LLM，不自动生成新的研究结论。

研究 TXT 包含本地笔记与观察；来源和观察可单独导出 CSV。打印功能可使用浏览器另存 PDF。原始采集工作区与原报告导出仍保留。
