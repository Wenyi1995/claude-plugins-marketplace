#!/usr/bin/env python3
"""
快速通道分类器 - 三省审议流水线

负责：
1. 判断任务是否适合快速通道（跳过三省审议）
2. 提供置信度评分和原因说明
3. 支持白名单模板和双重否决机制
"""
from typing import Dict, List, Tuple
import re


class FastTrackConfig:
    """快速通道配置"""

    # 白名单模板（95% 置信度）
    WHITELIST_PATTERNS = [
        # 纯信息收集
        r'(查询|导出|列出|查看|获取).*(日志|数据|列表|信息)',
        r'(检查|查看).*(状态|版本|配置)',

        # 纯文档整理（不涉及技术决策）
        r'(格式化|整理|补充).*(文档|README|注释)',
        r'(生成|更新).*(目录|索引)',

        # 环境配置（标准化操作）
        r'(安装|配置|启动|重启).*(依赖|服务|MCP)',
        r'(设置|修改).*(权限|环境变量)',
    ]

    # 双重否决关键词（90% 置信度，出现则不走快速通道）
    VETO_KEYWORDS = {
        # 架构决策
        'architecture': ['架构', '设计', '重构', '迁移'],
        # 安全风险
        'security': ['安全', '鉴权', '加密', '密钥', '权限变更'],
        # 性能优化
        'performance': ['性能', '优化', '缓存策略', '算法'],
        # 业务逻辑
        'business_logic': ['业务逻辑', '核心代码', '接口修改'],
    }

    # 长度阈值（85% 置信度）
    MAX_SIMPLE_TASK_LENGTH = 200  # 字符数
    MAX_SIMPLE_TASK_WORDS = 50    # 分词数

    # 复杂度指标（85% 置信度）
    COMPLEXITY_INDICATORS = [
        r'\d+\s*(个|项|种)',  # "修改 5 个文件"
        r'(同时|并行|批量)',
        r'(如果|当.*时|根据.*判断)',  # 条件逻辑
        r'(优先级|权重|策略)',
    ]


def classify_task(title: str, context: str) -> Dict:
    """
    对任务进行快速通道分类

    Args:
        title: 任务标题
        context: 任务详细描述

    Returns:
        {
            'track': 'fast' | 'normal',
            'confidence': float,  # 0.0 - 1.0
            'reasons': List[str],
            'warnings': List[str]  # 如果置信度 < 0.8，列出不确定因素
        }
    """
    full_text = f"{title} {context}"

    # 初始化结果
    result = {
        'track': 'normal',
        'confidence': 0.0,
        'reasons': [],
        'warnings': []
    }

    # 第一层：白名单模板匹配（95% 置信度）
    whitelist_score, whitelist_reasons = _check_whitelist(full_text)
    if whitelist_score > 0:
        result['track'] = 'fast'
        result['confidence'] = 0.95
        result['reasons'].extend(whitelist_reasons)

    # 第二层：双重否决制（90% 置信度）
    veto_score, veto_reasons = _check_veto(full_text)
    if veto_score > 0:
        result['track'] = 'normal'
        result['confidence'] = 0.90
        result['reasons'] = veto_reasons  # 覆盖白名单理由
        return result

    # 第三层：长度和复杂度阈值（85% 置信度）
    complexity_score, complexity_reasons = _check_complexity(full_text)
    if complexity_score > 0:
        result['track'] = 'normal'
        result['confidence'] = 0.85
        result['reasons'].extend(complexity_reasons)
        return result

    # 第四层：置信度调整
    if result['track'] == 'fast' and result['confidence'] < 0.8:
        result['warnings'].append('任务虽符合白名单模板，但置信度较低，建议人工确认')

    # 如果通过白名单但没有否决，保持 fast track
    if result['track'] == 'fast':
        return result

    # 默认：走正常流程
    result['track'] = 'normal'
    result['confidence'] = 0.75  # 默认置信度
    result['reasons'].append('未匹配到明确的快速通道特征，建议走三省审议流程')

    return result


def _check_whitelist(text: str) -> Tuple[float, List[str]]:
    """
    检查是否匹配白名单模板

    Returns:
        (score, reasons)
        score: 匹配的权重（0.0 - 1.0）
        reasons: 匹配的原因列表
    """
    reasons = []

    for pattern in FastTrackConfig.WHITELIST_PATTERNS:
        if re.search(pattern, text):
            reasons.append(f'匹配白名单模板: {pattern}')

    if reasons:
        return 0.95, reasons
    return 0.0, []


def _check_veto(text: str) -> Tuple[float, List[str]]:
    """
    检查是否触发双重否决

    Returns:
        (score, reasons)
        score: 否决的权重（0.0 - 1.0）
        reasons: 否决的原因列表
    """
    reasons = []

    for category, keywords in FastTrackConfig.VETO_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text:
                reasons.append(f'触发否决关键词 [{category}]: "{keyword}"')

    if reasons:
        return 0.90, reasons
    return 0.0, []


def _check_complexity(text: str) -> Tuple[float, List[str]]:
    """
    检查任务复杂度

    Returns:
        (score, reasons)
        score: 复杂度权重（0.0 - 1.0）
        reasons: 复杂度指标列表
    """
    reasons = []

    # 检查长度
    if len(text) > FastTrackConfig.MAX_SIMPLE_TASK_LENGTH:
        reasons.append(f'任务描述过长（{len(text)} 字符 > {FastTrackConfig.MAX_SIMPLE_TASK_LENGTH}）')

    # 检查分词数（简单按空格和标点分词）
    words = re.split(r'[\s,，。！？、；：\n]+', text)
    words = [w for w in words if w]  # 过滤空字符串
    if len(words) > FastTrackConfig.MAX_SIMPLE_TASK_WORDS:
        reasons.append(f'任务描述词数过多（{len(words)} 词 > {FastTrackConfig.MAX_SIMPLE_TASK_WORDS}）')

    # 检查复杂度指标
    for pattern in FastTrackConfig.COMPLEXITY_INDICATORS:
        if re.search(pattern, text):
            reasons.append(f'检测到复杂度指标: {pattern}')

    if reasons:
        return 0.85, reasons
    return 0.0, []


def format_classification_result(result: Dict) -> str:
    """
    格式化分类结果为可读字符串

    Args:
        result: classify_task() 的返回结果

    Returns:
        格式化的字符串
    """
    lines = []
    lines.append(f"轨道: {result['track']}")
    lines.append(f"置信度: {result['confidence']:.0%}")

    if result['reasons']:
        lines.append("\n判断依据:")
        for i, reason in enumerate(result['reasons'], 1):
            lines.append(f"  {i}. {reason}")

    if result['warnings']:
        lines.append("\n注意事项:")
        for i, warning in enumerate(result['warnings'], 1):
            lines.append(f"  {i}. {warning}")

    return '\n'.join(lines)


def get_confidence_threshold() -> float:
    """获取司礼监应该询问用户的置信度阈值"""
    return 0.80


# ===== 统计和审计功能 =====

def record_fast_track_decision(
    task_id: str,
    classification: Dict,
    user_override: bool = False,
    final_decision: str = None
) -> None:
    """
    记录快速通道决策（用于后续分析和优化）

    Args:
        task_id: 任务 ID
        classification: classify_task() 的返回结果
        user_override: 是否用户手动覆盖了分类结果
        final_decision: 最终决策（'fast' 或 'normal'）
    """
    # TODO: 实现决策日志记录
    # 可以写入到 data/fast_track_decisions.jsonl
    pass


def get_fast_track_stats() -> Dict:
    """
    获取快速通道使用统计

    Returns:
        {
            'total_decisions': int,
            'fast_track_count': int,
            'normal_track_count': int,
            'user_override_count': int,
            'accuracy': float  # 如果有用户反馈
        }
    """
    # TODO: 实现统计功能
    return {
        'total_decisions': 0,
        'fast_track_count': 0,
        'normal_track_count': 0,
        'user_override_count': 0,
        'accuracy': 0.0
    }
