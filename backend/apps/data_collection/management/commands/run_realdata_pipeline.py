"""
真实数据流水线：拉取 RSS 新闻 → 处理正文与关键词 → 发现话题 → 更新热度。
用法：python manage.py run_realdata_pipeline
可选：--no-crawl 仅做处理+发现+热度（不重新拉取）
"""
from django.core.management.base import BaseCommand
from django.conf import settings

from apps.data_collection.models import DataSource, RawContent
from apps.data_collection.tasks import crawl_source_task, process_raw_content_task
from apps.topic_analysis.tasks import discover_new_topics, update_topic_heat_scores

# 默认多源配置（MVP：公开可抓取 feed/聚合源）
SOCIAL_SOURCE_TYPES = {"wechat", "bilibili", "xiaohongshu", "douyin"}

DEFAULT_RSSHUB_MIRRORS = [
    "https://rsshub.app",
    "https://rsshub.rssforever.com",
    "https://rsshub.feeded.xyz",
]


def _rsshub_mirrors():
    custom = getattr(settings, "RSSHUB_MIRRORS", None) or []
    mirrors = []
    for x in (custom or DEFAULT_RSSHUB_MIRRORS):
        v = str(x or "").strip().rstrip("/")
        if v and v not in mirrors:
            mirrors.append(v)
    return mirrors


def _build_rsshub_urls(route: str):
    route = "/" + str(route or "").lstrip("/")
    return [f"{base}{route}" for base in _rsshub_mirrors()]


def _enabled_social_sources():
    configured = getattr(settings, "ENABLED_SOCIAL_SOURCES", None) or list(SOCIAL_SOURCE_TYPES)
    enabled = set()
    for item in configured:
        name = str(item or "").strip().lower()
        if name in SOCIAL_SOURCE_TYPES:
            enabled.add(name)
    return enabled


def _wechat_keywords():
    keywords = getattr(settings, "WECHAT_SOGOU_KEYWORDS", None) or ["科技", "AI", "互联网", "创业", "数码"]
    cleaned = []
    for kw in keywords:
        text = str(kw or "").strip()
        if text:
            cleaned.append(text)
    return cleaned or ["科技", "AI", "互联网", "创业", "数码"]


def _wechat_max_per_keyword():
    value = int(getattr(settings, "WECHAT_SOGOU_MAX_PER_KEYWORD", 6) or 6)
    return max(1, min(value, 20))


DEFAULT_SOURCES = [
    {
        "name": "Solidot",
        "source_type": "rss",
        "base_url": "https://www.solidot.org/index.rss",
        "config": {"feed_url": "https://www.solidot.org/index.rss", "pages": 1},
    },
    {
        "name": "阮一峰博客",
        "source_type": "rss",
        "base_url": "https://www.ruanyifeng.com/blog/atom.xml",
        "config": {"feed_url": "https://www.ruanyifeng.com/blog/atom.xml", "pages": 1},
    },
    {
        "name": "少数派",
        "source_type": "rss",
        "base_url": "https://sspai.com/feed",
        "config": {"feed_url": "https://sspai.com/feed", "pages": 1},
    },
    {
        "name": "小红书热点(聚合)",
        "source_type": "xiaohongshu",
        "base_url": "https://rsshub.app/xiaohongshu/discovery/hot_list",
        "config": {
            "platform": "xiaohongshu",
            "feed_urls": _build_rsshub_urls("/xiaohongshu/discovery/hot_list"),
            "api_endpoints": [
                {
                    "url": "https://www.xiaohongshu.com/explore",
                    "format": "xiaohongshu_explore",
                }
            ],
            "pages": 1,
            "timeout": 8,
            "max_retries": 1,
        },
    },
    {
        "name": "公众号热点(聚合)",
        "source_type": "wechat",
        "base_url": "https://rsshub.app/wechat/top",
        "config": {
            "platform": "wechat",
            "feed_urls": _build_rsshub_urls("/wechat/top"),
            "api_endpoints": [
                {
                    "url": "https://weixin.sogou.com/weixin",
                    "format": "wechat_sogou",
                    "keywords": _wechat_keywords(),
                    "max_per_keyword": _wechat_max_per_keyword(),
                }
            ],
            "pages": 1,
            "timeout": 8,
            "max_retries": 1,
        },
    },
    {
        "name": "B站热搜(聚合)",
        "source_type": "bilibili",
        "base_url": "https://rsshub.app/bilibili/hot-search",
        "config": {
            "platform": "bilibili",
            "feed_urls": _build_rsshub_urls("/bilibili/hot-search"),
            "api_endpoints": [
                {
                    "url": "https://api.bilibili.com/x/web-interface/popular?ps=30&pn=1",
                    "format": "bilibili_popular",
                }
            ],
            "pages": 1,
            "timeout": 8,
            "max_retries": 1,
        },
    },
    {
        "name": "抖音热搜(聚合)",
        "source_type": "douyin",
        "base_url": "https://rsshub.app/douyin/hot_search",
        "config": {
            "platform": "douyin",
            "feed_urls": _build_rsshub_urls("/douyin/hot_search"),
            "api_endpoints": [
                {
                    "url": "https://www.iesdouyin.com/web/api/v2/hotsearch/billboard/word/",
                    "format": "douyin_hot",
                }
            ],
            "pages": 1,
            "timeout": 8,
            "max_retries": 1,
        },
    },
]


class Command(BaseCommand):
    help = "拉取真实网络数据并生成推荐用话题（RSS → 处理 → 发现话题 → 更新热度）"

    def add_arguments(self, parser):
        parser.add_argument(
            "--no-crawl",
            action="store_true",
            help="不执行爬取，仅对已有 RawContent 做处理与发现话题",
        )
        parser.add_argument(
            "--threshold",
            type=int,
            default=1,
            help="发现话题时关键词出现次数阈值（默认 1，数据多时可改为 2 或 5）",
        )
        parser.add_argument(
            "--hours",
            type=int,
            default=24,
            help="只统计最近 N 小时的已处理内容用于发现话题（默认 24）",
        )
        parser.add_argument(
            "--top-n",
            type=int,
            default=10,
            help="聚类排序后仅保留前 N 个热点调用大模型（默认 10）",
        )
        parser.add_argument(
            "--cluster-first",
            action="store_true",
            default=True,
            help="先做候选聚类再筛选 TopN（默认开启）",
        )
        parser.add_argument(
            "--no-cluster-first",
            action="store_false",
            dest="cluster_first",
            help="关闭候选聚类，按关键词直接排序筛选",
        )

    def handle(self, *args, **options):
        no_crawl = options["no_crawl"]
        threshold = options["threshold"]
        hours = options["hours"]
        top_n = options["top_n"]
        cluster_first = options["cluster_first"]

        if not no_crawl:
            self._ensure_default_sources()
            self._run_crawl()
        self._process_pending_contents()
        self._discover_topics(
            threshold=threshold,
            hours=hours,
            top_n=top_n,
            cluster_first=cluster_first,
        )
        self._update_heat()
        self.stdout.write(self.style.SUCCESS("真实数据流水线执行完成，刷新前端即可看到基于实时数据的推荐。"))

    def _ensure_default_sources(self):
        """确保存在默认多源数据配置"""
        enabled_social_sources = _enabled_social_sources()
        self.stdout.write(f"启用社媒平台: {sorted(enabled_social_sources)}")
        for item in DEFAULT_SOURCES:
            source_type = item["source_type"]
            base_url = item["base_url"]
            should_enable = source_type not in SOCIAL_SOURCE_TYPES or source_type in enabled_social_sources
            target_status = "active" if should_enable else "inactive"
            source = DataSource.objects.filter(source_type=source_type, base_url=base_url).first()
            if not source:
                source = DataSource.objects.filter(source_type=source_type, name=item["name"]).first()

            if not source:
                DataSource.objects.create(
                    name=item["name"],
                    source_type=source_type,
                    base_url=base_url,
                    status=target_status,
                    config=item["config"],
                )
                self.stdout.write(f"已创建数据源: {item['name']} (status={target_status})")
                continue

            # 已存在的默认源进行配置修复（补齐镜像、兜底API、快速失败参数）
            old_cfg = source.config or {}
            new_cfg = item["config"] or {}
            merged_cfg = dict(old_cfg)
            merged_cfg.update(new_cfg)
            # 保留老配置中的自定义 feed_urls，同时补齐新镜像
            old_urls = old_cfg.get("feed_urls") if isinstance(old_cfg, dict) else []
            new_urls = new_cfg.get("feed_urls") if isinstance(new_cfg, dict) else []
            merged_urls = []
            for u in (old_urls or []) + (new_urls or []):
                text = str(u or "").strip()
                if text and text not in merged_urls:
                    merged_urls.append(text)
            if merged_urls:
                merged_cfg["feed_urls"] = merged_urls

            changed = False
            if source.name != item["name"]:
                source.name = item["name"]
                changed = True
            if source.base_url != base_url:
                source.base_url = base_url
                changed = True
            if source.config != merged_cfg:
                source.config = merged_cfg
                changed = True
            if source.status != target_status:
                source.status = target_status
                changed = True
            if changed:
                source.save(update_fields=["name", "base_url", "config", "status", "updated_at"])
                self.stdout.write(f"已更新数据源配置: {item['name']} (status={target_status})")

    def _run_crawl(self):
        """同步执行所有支持类型的数据源爬取"""
        supported_types = ["rss"] + sorted(_enabled_social_sources())
        sources = DataSource.objects.filter(source_type__in=supported_types, status="active")
        for source in sources:
            self.stdout.write(f"正在拉取: {source.name} ...")
            try:
                result = crawl_source_task.apply(args=[source.id])
                if result.successful():
                    r = result.get()
                    self.stdout.write(
                        f"  -> 爬取 {r.get('total', 0)} 条, 保存 {r.get('saved', 0)} 条"
                    )
                else:
                    self.stdout.write(self.style.WARNING(f"  -> 失败: {result.result}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  -> 异常: {e}"))

    def _process_pending_contents(self):
        """处理所有 pending 的 RawContent：清洗、提取关键词、标记为 processed"""
        pending = RawContent.objects.filter(status="pending")
        total = pending.count()
        if total == 0:
            self.stdout.write("没有待处理内容，跳过处理步骤。")
            return
        self.stdout.write(f"正在处理 {total} 条待处理内容...")
        done = 0
        for content in pending:
            try:
                process_raw_content_task.apply(args=[content.id])
                done += 1
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"  处理 {content.id} 失败: {e}"))
        self.stdout.write(f"  -> 已处理 {done}/{total} 条")

    def _discover_topics(self, threshold=2, hours=24, top_n=10, cluster_first=True):
        """从已处理内容中发现新话题"""
        self.stdout.write(
            f"发现新话题（阈值={threshold}, hours={hours}, top_n={top_n}, cluster_first={cluster_first}）..."
        )
        try:
            result = discover_new_topics.apply(
                kwargs={
                    "threshold": threshold,
                    "hours": hours,
                    "top_n": top_n,
                    "cluster_first": cluster_first,
                }
            )
            if result.successful():
                r = result.get()
                n = len(r.get("new_topics", []))
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  -> 新发现 {n} 个话题（候选 {r.get('candidate_count', 0)}，LLM 调用 {r.get('llm_calls', 0)} 次）"
                    )
                )
            else:
                self.stdout.write(self.style.WARNING(f"  -> 失败: {result.result}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  -> 异常: {e}"))

    def _update_heat(self):
        """更新所有话题热度与趋势"""
        self.stdout.write("更新话题热度...")
        try:
            result = update_topic_heat_scores.apply()
            if result.successful():
                r = result.get()
                self.stdout.write(self.style.SUCCESS(f"  -> 已更新 {r.get('updated_count', 0)} 个话题"))
            else:
                self.stdout.write(self.style.WARNING(f"  -> 失败: {result.result}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  -> 异常: {e}"))
