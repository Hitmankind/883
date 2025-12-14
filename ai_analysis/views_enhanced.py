"""
增强版 AI 学情分析视图
完整的动态 AI 分析功能
"""

import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg, Q, Max, Min
from django.utils import timezone

from students.models import Student, Score, Course
from ai_analysis.models import StudentAnalysis, AIServiceLog

# 配置日志
logger = logging.getLogger(__name__)

def ai_dashboard(request):
    """AI 分析仪表板 - 完整动态版"""

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
        'analysis_types_dict': dict(StudentAnalysis.ANALYSIS_TYPES),
    }

    return render(request, 'ai_analysis/ai_dashboard.html', context)

def ai_intervention_dashboard(request):
    """AI 干预面板"""

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
            intervention_students.append({
                'student': student,
                'avg_score': round(avg_score, 1),
                'failed_courses': failed_courses,
                'total_courses': total_courses,
                'pass_rate': round(((total_courses - failed_courses) / total_courses) * 100, 1) if total_courses > 0 else 0,
                'intervention_level': intervention_level,
                'latest_analysis': latest_analysis,
                'recommendations': generate_intervention_recommendations(student, avg_score, failed_courses)
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

def generate_intervention_recommendations(student, avg_score, failed_courses):
    """生成干预建议"""
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

    return recommendations

def student_ai_analysis_detail(request, student_id):
    """学生 AI 分析详情页"""

    student = get_object_or_404(Student, pk=student_id)

    # 获取该学生的所有分析
    analyses = StudentAnalysis.objects.filter(
        student=student,
        status='completed'
    ).order_by('-created_at')

    # 学业统计
    scores = Score.objects.filter(student=student).select_related('course')
    course_count = scores.count()
    avg_score = scores.aggregate(avg=Avg('score'))['avg'] or 0
    failed_courses = scores.filter(score__lt=60).count()
    excellent_courses = scores.filter(score__gte=90).count()

    # 成绩分布
    score_distribution = {
        'excellent': scores.filter(score__gte=90).count(),
        'good': scores.filter(score__gte=80, score__lt=90).count(),
        'average': scores.filter(score__gte=70, score__lt=80).count(),
        'pass': scores.filter(score__gte=60, score__lt=70).count(),
        'fail': scores.filter(score__lt=60).count(),
    }

    # 课程类型统计
    course_stats = {}
    for score in scores:
        course_type = getattr(score.course, 'course_type', 'OTHER')
        if course_type not in course_stats:
            course_stats[course_type] = []
        course_stats[course_type].append(float(score.score))

    for course_type in course_stats:
        scores_list = course_stats[course_type]
        course_stats[course_type] = {
            'avg': round(sum(scores_list) / len(scores_list), 1),
            'count': len(scores_list),
            'max': max(scores_list),
            'min': min(scores_list)
        }

    context = {
        'student': student,
        'analyses': analyses,
        'course_count': course_count,
        'avg_score': round(avg_score, 1),
        'failed_courses': failed_courses,
        'excellent_courses': excellent_courses,
        'score_distribution': score_distribution,
        'course_stats': course_stats,
        'analysis_types_dict': dict(StudentAnalysis.ANALYSIS_TYPES),
    }

    return render(request, 'ai_analysis/student_analysis_detail.html', context)

def ai_report_generation(request):
    """AI 报告生成页面"""

    if request.method == 'POST':
        # 处理报告生成请求
        student_id = request.POST.get('student_id')
        analysis_type = request.POST.get('analysis_type')
        report_format = request.POST.get('report_format', 'html')

        student = get_object_or_404(Student, pk=student_id)

        # 获取最新分析
        latest_analysis = StudentAnalysis.objects.filter(
            student=student,
            analysis_type=analysis_type,
            status='completed'
        ).order_by('-created_at').first()

        if not latest_analysis:
            return JsonResponse({
                'success': False,
                'message': '未找到相关分析记录'
            })

        # 生成报告（这里简化处理）
        report_data = {
            'student_info': {
                'name': student.name,
                'student_id': student.student_id,
                'major': student.major,
                'college': student.college,
            },
            'analysis': {
                'type': latest_analysis.get_analysis_type_display(),
                'title': latest_analysis.title,
                'result': latest_analysis.analysis_result,
                'confidence': latest_analysis.ai_confidence,
                'created_at': latest_analysis.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            }
        }

        return JsonResponse({
            'success': True,
            'report_data': report_data,
            'message': '报告生成成功'
        })

    # GET 请求 - 显示报告生成页面
    students = Student.objects.all()
    analysis_types = StudentAnalysis.ANALYSIS_TYPES

    context = {
        'students': students,
        'analysis_types': analysis_types,
    }

    return render(request, 'ai_analysis/ai_report_generation.html', context)

def ai_analysis_history(request):
    """AI 分析历史记录"""

    # 获取查询参数
    student_id = request.GET.get('student_id')
    analysis_type = request.GET.get('analysis_type')
    status = request.GET.get('status')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    # 构建查询
    queryset = StudentAnalysis.objects.select_related('student').order_by('-created_at')

    if student_id:
        queryset = queryset.filter(student__student_id__icontains=student_id)

    if analysis_type:
        queryset = queryset.filter(analysis_type=analysis_type)

    if status:
        queryset = queryset.filter(status=status)

    if date_from:
        queryset = queryset.filter(created_at__gte=date_from)

    if date_to:
        queryset = queryset.filter(created_at__lte=date_to)

    # 分页
    from django.core.paginator import Paginator
    paginator = Paginator(queryset, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # 统计数据
    stats = {
        'total': queryset.count(),
        'completed': queryset.filter(status='completed').count(),
        'pending': queryset.filter(status='pending').count(),
        'failed': queryset.filter(status='failed').count(),
    }

    context = {
        'page_obj': page_obj,
        'stats': stats,
        'analysis_types_dict': dict(StudentAnalysis.ANALYSIS_TYPES),
        'status_choices_dict': dict(StudentAnalysis.STATUS_CHOICES),
        'filters': {
            'student_id': student_id or '',
            'analysis_type': analysis_type or '',
            'status': status or '',
            'date_from': date_from or '',
            'date_to': date_to or '',
        }
    }

    return render(request, 'ai_analysis/ai_history.html', context)

def ai_suggestions_system(request):
    """AI 预警和建议系统"""

    # 获取所有需要建议的学生
    suggestions = []

    students = Student.objects.all()
    for student in students:
        scores = Score.objects.filter(student=student)
        if not scores.exists():
            continue

        avg_score = scores.aggregate(avg=Avg('score'))['avg'] or 0
        recent_scores = scores.order_by('-date')[:5]

        # 生成预警和建议
        alerts = []
        recommendations = []

        if avg_score < 60:
            alerts.append({
                'level': 'danger',
                'title': '学业严重困难',
                'message': f'平均成绩仅{avg_score:.1f}分，需要立即干预'
            })
            recommendations.extend([
                '立即联系学业导师',
                '制定补习计划',
                '寻求心理辅导'
            ])
        elif avg_score < 75:
            alerts.append({
                'level': 'warning',
                'title': '学业需要关注',
                'message': f'平均成绩{avg_score:.1f}分，建议加强学习'
            })
            recommendations.extend([
                '加强基础知识学习',
                '参加学习小组',
                '改进学习方法'
            ])
        elif avg_score >= 90:
            alerts.append({
                'level': 'success',
                'title': '学业表现优秀',
                'message': f'平均成绩{avg_score:.1f}分，继续保持'
            })
            recommendations.extend([
                '参加学科竞赛',
                '探索进阶课程',
                '指导其他同学'
            ])

        # 检查成绩趋势
        if len(recent_scores) >= 3:
            recent_avg = sum(float(s.score) for s in recent_scores) / len(recent_scores)
            older_avg = scores.aggregate(avg=Avg('score'))['avg'] or 0

            if recent_avg < older_avg - 5:
                alerts.append({
                    'level': 'warning',
                    'title': '成绩下降趋势',
                    'message': '近期成绩有所下降，需要关注'
                })
                recommendations.append('分析下降原因，调整学习策略')

        if alerts:
            suggestions.append({
                'student': student,
                'avg_score': round(avg_score, 1),
                'alerts': alerts,
                'recommendations': recommendations,
                'latest_analysis': StudentAnalysis.objects.filter(
                    student=student,
                    status='completed'
                ).order_by('-created_at').first()
            })

    # 预警统计
    alert_stats = {
        'danger': len([s for s in suggestions if any(a['level'] == 'danger' for a in s['alerts'])]),
        'warning': len([s for s in suggestions if any(a['level'] == 'warning' for a in s['alerts'])]),
        'success': len([s for s in suggestions if any(a['level'] == 'success' for a in s['alerts'])]),
        'total': len(suggestions)
    }

    context = {
        'suggestions': suggestions,
        'alert_stats': alert_stats,
    }

    return render(request, 'ai_analysis/ai_suggestions.html', context)

@require_http_methods(["GET"])
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

    elif action == 'get_student_stats':
        # 获取学生统计
        student_id = request.GET.get('student_id')
        student = get_object_or_404(Student, pk=student_id)

        scores = Score.objects.filter(student=student)
        stats = {
            'name': student.name,
            'major': student.major,
            'avg_score': scores.aggregate(avg=Avg('score'))['avg'] or 0,
            'total_courses': scores.count(),
            'failed_courses': scores.filter(score__lt=60).count(),
            'latest_analysis_date': StudentAnalysis.objects.filter(
                student=student,
                status='completed'
            ).order_by('-created_at').values_list('created_at', flat=True).first()
        }
        return JsonResponse(stats)

    return JsonResponse({'error': 'Unknown action'})