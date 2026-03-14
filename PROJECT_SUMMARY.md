# 项目现状总结（2026-03-14）

## 已完成

- 社媒多源采集：`wechat` / `bilibili` / `xiaohongshu` / `douyin`
- RSSHub 多镜像与 API/HTML 兜底
- 聚类优先 + TopN 截断 + LLM 总结
- 去同质化增强（同源惩罚、黑名单、标题去重）
- LLM 稳定性增强（超时 fail-fast + 熔断 + 规则兜底）
- 平台开关与公众号词池可配置

## 当前默认入口

- 运行命令：`python manage.py run_realdata_pipeline --threshold 1 --hours 24 --top-n 10`
- API 文档：`/swagger/`

## 后续可做

- 增加命令行临时平台覆盖（不改 `.env`）
- 为话题质量加入可观测指标（标题长度、重复率、覆盖率）
