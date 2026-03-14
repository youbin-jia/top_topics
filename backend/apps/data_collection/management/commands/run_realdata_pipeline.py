"""
真实数据流水线：拉取 RSS 新闻 → 处理正文与关键词 → 发现话题 → 更新热度。
用法：python manage.py run_realdata_pipeline
可选：--no-crawl 仅做处理+发现+热度（不重新拉取）
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from apps.data_collection.models import DataSource, RawContent
from apps.data_collection.tasks import crawl_source_task, process_raw_content_task
from apps.topic_analysis.tasks import discover_new_topics, update_topic_heat_scores

# 默认 RSS 源（可自行在后台增删）
DEFAULT_RSS_SOURCES = [
    {"name": "Solidot", "feed_url": "https://www.solidot.org/index.rss"},
    {"name": "阮一峰博客", "feed_url": "https://www.ruanyifeng.com/blog/atom.xml"},
    {"name": "少数派", "feed_url": "https://sspai.com/feed"},
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
            default=None,
            help="只统计最近 N 小时的已处理内容用于发现话题（默认不限制）",
        )

    def handle(self, *args, **options):
        no_crawl = options["no_crawl"]
        threshold = options["threshold"]
        hours = options["hours"]

        if not no_crawl:
            self._ensure_rss_sources()
            self._run_crawl()
        self._process_pending_contents()
        self._discover_topics(threshold=threshold, hours=hours)
        self._update_heat()
        self.stdout.write(self.style.SUCCESS("真实数据流水线执行完成，刷新前端即可看到基于实时数据的推荐。"))

    def _ensure_rss_sources(self):
        """确保存在默认 RSS 数据源"""
        for item in DEFAULT_RSS_SOURCES:
            feed_url = item["feed_url"]
            if not DataSource.objects.filter(
                source_type="rss",
                config__feed_url=feed_url,
            ).exists():
                DataSource.objects.create(
                    name=item["name"],
                    source_type="rss",
                    base_url=feed_url,
                    status="active",
                    config={"feed_url": feed_url, "pages": 1},
                )
                self.stdout.write(f"已创建数据源: {item['name']}")

    def _run_crawl(self):
        """同步执行所有 RSS 源爬取"""
        sources = DataSource.objects.filter(source_type="rss", status="active")
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

    def _discover_topics(self, threshold=2, hours=None):
        """从已处理内容中发现新话题"""
        self.stdout.write(f"发现新话题（阈值={threshold}）...")
        try:
            result = discover_new_topics.apply(kwargs={"threshold": threshold, "hours": hours})
            if result.successful():
                r = result.get()
                n = len(r.get("new_topics", []))
                self.stdout.write(self.style.SUCCESS(f"  -> 新发现 {n} 个话题"))
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
