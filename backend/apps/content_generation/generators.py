"""
内容生成器
"""
from typing import List, Dict
import random
from .models import TitleTemplate, OutlineTemplate


class TitleGenerator:
    """标题生成器"""

    def __init__(self):
        self.templates = self._load_templates()

    def _load_templates(self) -> Dict[str, List[TitleTemplate]]:
        """加载模板"""
        templates = {}
        for category in dict(TitleTemplate.CATEGORY_CHOICES).keys():
            templates[category] = list(
                TitleTemplate.objects.filter(
                    category=category,
                    is_active=True
                ).order_by('-avg_ctr')
            )
        return templates

    def generate(
        self,
        keywords: List[str],
        category: str = 'news',
        n_titles: int = 5,
        style: str = 'normal'
    ) -> List[str]:
        """
        生成标题

        Args:
            keywords: 关键词列表
            category: 标题分类
            n_titles: 生成数量
            style: 风格 ('normal', 'attractive', 'professional')

        Returns:
            标题列表
        """
        titles = []

        # 获取模板
        templates = self.templates.get(category, [])

        if not templates:
            # 使用默认模板
            titles = self._generate_default(keywords, n_titles)
        else:
            # 使用模板生成
            for _ in range(n_titles):
                template = random.choice(templates)

                # 准备填充数据
                kwargs = {
                    'keyword': keywords[0] if keywords else '话题',
                    'keywords': '、'.join(keywords[:3]),
                    'num': random.randint(3, 10),
                }

                try:
                    title = template.render(**kwargs)
                    titles.append(title)
                except Exception:
                    continue

        return titles[:n_titles]

    def _generate_default(
        self,
        keywords: List[str],
        n_titles: int
    ) -> List[str]:
        """默认标题生成"""
        default_templates = [
            '关于{keyword}的深度解析',
            '{keyword}最新进展与趋势',
            '{num}个关于{keyword}的关键要点',
            '深度解读：{keyword}的影响与未来',
            '{keyword}：你不知道的{num}个秘密',
        ]

        titles = []
        for i in range(n_titles):
            template = default_templates[i % len(default_templates)]
            title = template.format(
                keyword=keywords[0] if keywords else '话题',
                num=random.randint(3, 10)
            )
            titles.append(title)

        return titles


class OutlineGenerator:
    """大纲生成器"""

    def __init__(self):
        self.templates = self._load_templates()

    def _load_templates(self) -> Dict[str, List[OutlineTemplate]]:
        """加载模板"""
        templates = {}
        for style in dict(OutlineTemplate.STYLE_CHOICES).keys():
            templates[style] = list(
                OutlineTemplate.objects.filter(
                    style=style,
                    is_active=True
                ).order_by('-avg_engagement')
            )
        return templates

    def generate(
        self,
        topic: str,
        keywords: List[str],
        style: str = 'informative',
        n_sections: int = 3
    ) -> Dict:
        """
        生成文章大纲

        Args:
            topic: 主题
            keywords: 关键词列表
            style: 风格
            n_sections: 章节数量

        Returns:
            大纲字典
        """
        # 获取模板
        templates = self.templates.get(style, [])

        if templates:
            template = random.choice(templates)
            structure = template.structure
        else:
            structure = self._get_default_structure(n_sections)

        # 填充大纲
        outline = {
            'title': topic,
            'style': style,
            'introduction': self._generate_intro(topic, keywords),
            'sections': [],
            'conclusion': self._generate_conclusion(topic, keywords)
        }

        # 生成各章节
        for i, section_template in enumerate(structure[:n_sections]):
            section = self._generate_section(
                section_template,
                topic,
                keywords,
                i + 1
            )
            outline['sections'].append(section)

        return outline

    def _get_default_structure(self, n_sections: int) -> List[Dict]:
        """获取默认结构"""
        default_sections = [
            {
                'title': '背景介绍',
                'points': ['发展历程', '现状分析']
            },
            {
                'title': '核心要点',
                'points': ['关键概念', '主要内容']
            },
            {
                'title': '影响分析',
                'points': ['积极影响', '潜在风险']
            },
            {
                'title': '案例研究',
                'points': ['典型案例', '成功经验']
            },
            {
                'title': '未来展望',
                'points': ['发展趋势', '应对策略']
            },
        ]

        return default_sections[:n_sections]

    def _generate_intro(
        self,
        topic: str,
        keywords: List[str]
    ) -> Dict:
        """生成引言"""
        return {
            'content': f'本文将深入探讨{topic}，从多个角度分析其背景、现状和未来趋势。',
            'key_points': keywords[:3],
            'word_count': 200
        }

    def _generate_section(
        self,
        section_template: Dict,
        topic: str,
        keywords: List[str],
        section_num: int
    ) -> Dict:
        """生成章节"""
        title = section_template.get('title', f'第{section_num}部分')
        points = section_template.get('points', [])

        # 填充要点
        filled_points = []
        for i, point in enumerate(points):
            if i < len(keywords):
                filled_points.append(f'{point}：关于{keywords[i]}的分析')
            else:
                filled_points.append(point)

        return {
            'number': section_num,
            'title': title,
            'key_points': filled_points,
            'estimated_length': 500,
            'writing_tips': self._get_writing_tips(title)
        }

    def _generate_conclusion(
        self,
        topic: str,
        keywords: List[str]
    ) -> Dict:
        """生成结论"""
        return {
            'content': f'综上所述，{topic}是一个值得深入研究和关注的话题。',
            'summary_points': keywords[:3],
            'call_to_action': '欢迎分享您的观点和看法',
            'word_count': 150
        }

    def _get_writing_tips(self, section_title: str) -> List[str]:
        """获取写作建议"""
        tips_map = {
            '背景介绍': [
                '提供客观事实',
                '引用权威数据',
                '建立上下文'
            ],
            '核心要点': [
                '突出重点',
                '使用具体例子',
                '保持逻辑清晰'
            ],
            '影响分析': [
                '多角度分析',
                '平衡利弊',
                '提供解决方案'
            ],
            '案例研究': [
                '选择代表性案例',
                '详细分析过程',
                '提炼经验教训'
            ],
            '未来展望': [
                '基于事实预测',
                '提供行动建议',
                '保持开放态度'
            ]
        }

        return tips_map.get(section_title, ['保持内容相关性', '注意逻辑性'])


class ContentQualityScorer:
    """内容质量评分器"""

    def score_title(self, title: str) -> float:
        """
        标题质量评分

        Args:
            title: 标题

        Returns:
            质量分数 (0-1)
        """
        score = 0.0

        # 长度评分 (10-30字最佳)
        length = len(title)
        if 10 <= length <= 30:
            score += 0.3
        elif 8 <= length <= 40:
            score += 0.2
        else:
            score += 0.1

        # 包含数字
        if any(char.isdigit() for char in title):
            score += 0.2

        # 包含疑问词
        question_words = ['如何', '为什么', '什么', '怎样', '是否']
        if any(word in title for word in question_words):
            score += 0.2

        # 包含情感词
        emotional_words = ['震惊', '惊喜', '秘密', '真相', '必看']
        if any(word in title for word in emotional_words):
            score += 0.2

        # 标点符号
        if '！' in title or '？' in title:
            score += 0.1

        return min(score, 1.0)

    def score_outline(self, outline: Dict) -> float:
        """
        大纲质量评分

        Args:
            outline: 大纲字典

        Returns:
            质量分数 (0-1)
        """
        score = 0.0

        # 结构完整性
        required_keys = ['title', 'introduction', 'sections', 'conclusion']
        if all(key in outline for key in required_keys):
            score += 0.3

        # 章节数量
        n_sections = len(outline.get('sections', []))
        if 3 <= n_sections <= 5:
            score += 0.3
        elif 2 <= n_sections <= 6:
            score += 0.2
        else:
            score += 0.1

        # 内容丰富度
        total_points = sum(
            len(section.get('key_points', []))
            for section in outline.get('sections', [])
        )
        if total_points >= 6:
            score += 0.2
        elif total_points >= 4:
            score += 0.1

        # 包含写作建议
        if any('writing_tips' in section for section in outline.get('sections', [])):
            score += 0.2

        return min(score, 1.0)
