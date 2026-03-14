"""
初始化示例话题数据，用于推荐页展示与调试。
用法：python manage.py seed_topics
"""
from django.core.management.base import BaseCommand
from apps.topic_analysis.models import Topic


SAMPLE_TOPICS = [
    {
        'name': 'AI大模型应用落地',
        'description': '大语言模型在办公、创作、编程等场景的实践与产品动态',
        'main_keyword': 'AI大模型',
        'keywords': ['ChatGPT', '大模型', 'AIGC', '人工智能'],
        'heat_score': 95.0,
        'trend': 'rising',
        'status': 'trending',
        'article_count': 1200,
        'view_count': 500000,
    },
    {
        'name': '新能源汽车与智能驾驶',
        'description': '电动车、智能座舱与自动驾驶技术进展',
        'main_keyword': '新能源汽车',
        'keywords': ['电动车', '智能驾驶', '蔚来', '比亚迪'],
        'heat_score': 88.0,
        'trend': 'rising',
        'status': 'trending',
        'article_count': 800,
        'view_count': 320000,
    },
    {
        'name': '短视频与直播电商',
        'description': '抖音、快手等平台的带货与内容运营',
        'main_keyword': '短视频',
        'keywords': ['抖音', '直播带货', '短视频', '种草'],
        'heat_score': 82.0,
        'trend': 'stable',
        'status': 'active',
        'article_count': 2000,
        'view_count': 400000,
    },
    {
        'name': '职场与副业赚钱',
        'description': '副业思路、自由职业与个人IP打造',
        'main_keyword': '副业',
        'keywords': ['副业', '自由职业', '个人IP', '职场'],
        'heat_score': 78.0,
        'trend': 'rising',
        'status': 'active',
        'article_count': 1500,
        'view_count': 280000,
    },
    {
        'name': '健康养生与运动',
        'description': '健身、饮食与心理健康相关话题',
        'main_keyword': '健康',
        'keywords': ['健身', '养生', '减脂', '心理健康'],
        'heat_score': 75.0,
        'trend': 'stable',
        'status': 'active',
        'article_count': 900,
        'view_count': 200000,
    },
    {
        'name': '理财与投资入门',
        'description': '基金、股票与资产配置的入门知识',
        'main_keyword': '理财',
        'keywords': ['基金', '理财', '投资', '定投'],
        'heat_score': 72.0,
        'trend': 'stable',
        'status': 'active',
        'article_count': 600,
        'view_count': 180000,
    },
    {
        'name': '读书与知识付费',
        'description': '好书推荐、听书与知识课程',
        'main_keyword': '读书',
        'keywords': ['读书', '知识付费', '得到', '樊登'],
        'heat_score': 68.0,
        'trend': 'stable',
        'status': 'active',
        'article_count': 500,
        'view_count': 150000,
    },
    {
        'name': '旅行与户外',
        'description': '国内游、出境游与户外徒步攻略',
        'main_keyword': '旅行',
        'keywords': ['旅行', '户外', '攻略', '自驾'],
        'heat_score': 65.0,
        'trend': 'rising',
        'status': 'active',
        'article_count': 700,
        'view_count': 160000,
    },
]


class Command(BaseCommand):
    help = '创建示例话题数据，用于推荐页展示'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='先清空已有话题再创建（慎用）',
        )

    def handle(self, *args, **options):
        if options['clear']:
            n = Topic.objects.count()
            Topic.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'已删除 {n} 条话题'))

        created = 0
        for item in SAMPLE_TOPICS:
            _, is_new = Topic.objects.update_or_create(
                name=item['name'],
                defaults={
                    'description': item['description'],
                    'main_keyword': item['main_keyword'],
                    'keywords': item['keywords'],
                    'heat_score': item['heat_score'],
                    'trend': item['trend'],
                    'status': item['status'],
                    'article_count': item['article_count'],
                    'view_count': item['view_count'],
                    'engagement_rate': 0.05,
                },
            )
            if is_new:
                created += 1

        self.stdout.write(self.style.SUCCESS(f'示例话题已就绪，本次新建 {created} 条'))
        self.stdout.write('刷新前端推荐页即可看到「热门话题」与「个性化推荐」内容。')
