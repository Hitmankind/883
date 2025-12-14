"""
简化版 AI 学情分析视图
修复语法错误
"""

import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Count, Avg, Q, Max, Min
from django.utils import timezone

from students.models import Student, Score, Course
from ai_analysis.models import StudentAnalysis, AIServiceLog

# 配置日志
logger = logging.getLogger(__name__)

def ai_dashboard(request):
    """AI 分析仪表板 - 简化版"""

    # 基础统计数据
    total_students = Student.objects.count()
    total_analyses = StudentAnalysis.objects.count()
    completed_analyses = StudentAnalysis.objects.filter(status='completed').count()
    pending_analyses = StudentAnalysis.objects.filter(status='pending').count()

    # 分析类型分布
    analysis_types = StudentAnalysis.objects.values('analysis_type').annotate(
        count=Count('id')
    ).order_by('-count')

    # 最近分析记录
    recent_analyses = StudentAnalysis.objects.select_related('student').order_by('-created_at')[:10]

    # 问题学生识别
    problem_students = StudentAnalysis.objects.filter(
        status='completed',
        analysis_result__icontains='需要改进'
    ).select_related('student').distinct()[:5]

    # 优秀学生识别
    excellent_students = StudentAnalysis.objects.filter(
        status='completed',
        analysis_result__icontains='优秀'
    ).select_related('student').distinct()[:5]

    # AI 服务统计
    ai_stats = {
        'total_requests': AIServiceLog.objects.count(),
        'success_rate': 0,
        'avg_response_time': 0,
        'daily_requests': []
    }

    success_count = AIServiceLog.objects.filter(status='success').count()
    if ai_stats['total_requests'] > 0:
        ai_stats['success_rate'] = round((success_count / ai_stats['total_requests']) * 100, 1)

    # 平均响应时间
    response_times = AIServiceLog.objects.filter(
        status='success',
        response_time__isnull=False
    ).values_list('response_time', flat=True)
    if response_times:
        ai_stats['avg_response_time'] = round(sum(response_times) / len(response_times), 2)

    # 最近7天的请求量
    for i in range(7):
        date = timezone.now() - timedelta(days=i)
        count = AIServiceLog.objects.filter(
            created_at__date=date.date()
        ).count()
        ai_stats['daily_requests'].append({
            'date': date.strftime('%m-%d'),
            'count': count
        })
    ai_stats['daily_requests'] = ai_stats['daily_requests'][::-1]

    # 学业趋势数据
    performance_trend = []
    for i in range(12):  # 最近12个月
        month = timezone.now() - timedelta(days=30*i)
        avg_score = Score.objects.filter(
            date__year=month.year,
            date__month=month.month
        ).aggregate(avg=Avg('score'))['avg'] or 0

        performance_trend.append({
            'month': month.strftime('%Y-%m'),
            'avg_score': round(avg_score, 1)
        })
    performance_trend = performance_trend[::-1]

    # 构建分析类型字典
    analysis_types_dict = {}
    for analysis_type, label in StudentAnalysis.ANALYSIS_TYPES:
        analysis_types_dict[analysis_type] = label

    context = {
        'total_students': total_students,
        'total_analyses': total_analyses,
        'completed_analyses': completed_analyses,
        'pending_analyses': pending_analyses,
        'analysis_types': analysis_types,
        'recent_analyses': recent_analyses,
        'problem_students': problem_students,
        'excellent_students': excellent_students,
        'ai_stats': ai_stats,
        'performance_trend': performance_trend,
        'analysis_types_dict': analysis_types_dict,
    }

    return render(request, 'ai_analysis/ai_dashboard.html', context)

def ai_intervention_dashboard(request):
    """AI 干预面板 - 简化版"""

    # 识别需要干预的学生
    intervention_students = []

    students = Student.objects.all()
    for student in students:
        # 获取学生成绩
        scores = Score.objects.filter(student=student)
        if not scores.exists():
            continue

        avg_score = scores.aggregate(avg=Avg('score'))['avg'] or 0
        failed_courses = scores.filter(score__lt=60).count()
        total_courses = scores.count()

        # 获取最新分析
        latest_analysis = StudentAnalysis.objects.filter(
            student=student,
            status='completed'
        ).order_by('-created_at').first()

        # 判断是否需要干预
        needs_intervention = False
        intervention_level = 'normal'

        if avg_score < 60:
            needs_intervention = True
            intervention_level = 'critical'
        elif avg_score < 70 or failed_courses > 2:
            needs_intervention = True
            intervention_level = 'warning'
        elif failed_courses > 0:
            needs_intervention = True
            intervention_level = 'attention'

        if needs_intervention:
            recommendations = []
            if avg_score < 60:
                recommendations.extend([
                    '立即联系学业导师进行一对一指导',
                    '制定详细的补习计划',
                    '寻求心理咨询师帮助',
                    '考虑调整学习负担'
                ])
            elif failed_courses > 2:
                recommendations.extend([
                    '加强基础课程复习',
                    '参加学习小组',
                    '寻求优秀同学帮助',
                    '改进学习方法'
                ])
            else:
                recommendations.extend([
                    '保持当前学习状态',
                    '持续监控学业进展',
                    '预防性辅导'
                ])

            intervention_students.append({
                'student': student,
                'avg_score': round(avg_score, 1),
                'failed_courses': failed_courses,
                'total_courses': total_courses,
                'pass_rate': round(((total_courses - failed_courses) / total_courses) * 100, 1) if total_courses > 0 else 0,
                'intervention_level': intervention_level,
                'latest_analysis': latest_analysis,
                'recommendations': recommendations
            })

    # 干预统计
    intervention_stats = {
        'critical': len([s for s in intervention_students if s['intervention_level'] == 'critical']),
        'warning': len([s for s in intervention_students if s['intervention_level'] == 'warning']),
        'attention': len([s for s in intervention_students if s['intervention_level'] == 'attention']),
        'total': len(intervention_students)
    }

    context = {
        'intervention_students': intervention_students,
        'intervention_stats': intervention_stats,
    }

    return render(request, 'ai_analysis/ai_intervention.html', context)

def ai_analysis_ajax(request):
    """AJAX 接口 - 获取分析数据"""

    action = request.GET.get('action')

    if action == 'get_analysis_count':
        # 获取分析数量统计
        counts = {
            'total': StudentAnalysis.objects.count(),
            'completed': StudentAnalysis.objects.filter(status='completed').count(),
            'pending': StudentAnalysis.objects.filter(status='pending').count(),
            'failed': StudentAnalysis.objects.filter(status='failed').count(),
        }
        return JsonResponse(counts)

    return JsonResponse({'error': 'Unknown action'})