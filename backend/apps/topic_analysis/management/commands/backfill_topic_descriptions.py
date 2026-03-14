"""
按关联内容为已有话题补全 description（话题概要，可作短视频选题）。
用法：python manage.py backfill_topic_descriptions
"""
from django.core.management.base import BaseCommand
from apps.topic_analysis.models import Topic, ContentTopicRelation
from apps.topic_analysis.llm import generate_topic_title_summary, rule_based_title_summary


def _build_source_items(contents, max_items=5):
    items = []
    for c in contents[:max_items]:
        items.append(
            {
                "title": (c.title or "")[:200],
                "summary": (c.summary or c.content or "")[:500],
                "url": c.url,
            }
        )
    return items


def _unique_title(candidate: str, current_topic_id: int) -> str:
    if not Topic.objects.filter(name=candidate).exclude(id=current_topic_id).exists():
        return candidate
    idx = 2
    while True:
        name = f"{candidate} #{idx}"
        if not Topic.objects.filter(name=name).exclude(id=current_topic_id).exists():
            return name
        idx += 1


class Command(BaseCommand):
    help = "为已有话题按关联内容补全 description，并可重写为短视频标题风格"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="只打印将要更新的内容，不写库",
        )
        parser.add_argument(
            "--rewrite-title",
            action="store_true",
            help="同时重写 topic.name 为短视频标题风格",
        )
        parser.add_argument(
            "--fallback-only",
            action="store_true",
            help="不调用大模型，强制使用规则兜底摘要/标题",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        rewrite_title = options["rewrite_title"]
        fallback_only = options["fallback_only"]
        if dry_run:
            self.stdout.write("（dry-run 模式，不写库）")
        updated = 0
        skipped = 0
        for topic in Topic.objects.all():
            relations = (
                ContentTopicRelation.objects.filter(topic=topic)
                .select_related("content")
                .order_by("-relevance_score")
            )
            contents = [r.content for r in relations]
            if not contents:
                skipped += 1
                continue
            source_items = _build_source_items(contents)
            keyword = topic.main_keyword or topic.name
            if fallback_only:
                generated = rule_based_title_summary(keyword, source_items)
            else:
                generated = generate_topic_title_summary(keyword, source_items)
            description = (generated.get("summary", "") or "").strip()
            generated_title = (generated.get("title", "") or "").strip()
            if not description:
                skipped += 1
                continue
            if dry_run:
                preview_title = generated_title if rewrite_title and generated_title else topic.name
                self.stdout.write(f"  [{topic.id}] {preview_title}: {description[:80]}...")
            else:
                topic.description = description
                update_fields = ["description"]
                if rewrite_title and generated_title:
                    topic.name = _unique_title(generated_title, topic.id)
                    update_fields.append("name")
                topic.save(update_fields=update_fields)
            updated += 1
        self.stdout.write(
            self.style.SUCCESS(f"已处理: 更新 {updated} 条，跳过 {skipped} 条")
        )
