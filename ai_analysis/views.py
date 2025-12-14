"""
学生 AI 分析视图
处理学情分析的 Web 请求和业务逻辑
"""

import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Avg, StdDev, Count, Q
from django.urls import reverse
from django.utils import timezone

from students.models import Student, Score, Course, Enrollment
from .models import StudentAnalysis, PromptTemplate, AIServiceLog
from .deepseek_client import get_deepseek_client, DeepSeekClient
from .prompts import PROMPT_TEMPLATES, TEMPLATE_VARIABLES

# 配置日志
logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET"])
def analysis_dashboard(request):
    """
    分析仪表板页面
    """
    # 获取用户的分析记录
    analyses = StudentAnalysis.objects.select_related('student').order_by('-created_at')

    # 分页处理
    paginator = Paginator(analyses, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # 统计数据
    stats = {
        'total_analyses': analyses.count(),
        'completed_analyses': analyses.filter(status='completed').count(),
        'pending_analyses': analyses.filter(status='pending').count(),
        'failed_analyses': analyses.filter(status='failed').count(),
    }

    context = {
        'page_obj': page_obj,
        'stats': stats,
        'analysis_types': StudentAnalysis.ANALYSIS_TYPES,
    }

    return render(request, 'ai_analysis/dashboard.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def create_analysis(request):
    """
    创建新的学生分析
    """
    if request.method == 'GET':
        # 获取学生列表
        students = Student.objects.all()
        analysis_types = StudentAnalysis.ANALYSIS_TYPES

        context = {
            'students': students,
            'analysis_types': analysis_types,
        }
        return render(request, 'ai_analysis/create_analysis.html', context)

    # 处理 POST 请求
    try:
        student_id = request.POST.get('student_id')
        analysis_type = request.POST.get('analysis_type')
        title = request.POST.get('title', f'{analysis_type}分析')

        if not student_id or not analysis_type:
            messages.error(request, '请选择学生和分析类型')
            return redirect('ai_analysis:create_analysis')

        student = get_object_or_404(Student, pk=student_id)

        # 创建分析记录
        analysis = StudentAnalysis.objects.create(
            student=student,
            analysis_type=analysis_type,
            title=title,
            status='pending',
            prompt_template=PROMPT_TEMPLATES.get(analysis_type, ''),
        )

        # 准备输入数据
        input_data = prepare_student_data(student, analysis_type)
        analysis.input_data = input_data
        analysis.save()

        messages.success(request, '分析任务已创建，正在处理中...')
        return redirect('ai_analysis:analysis_detail', analysis_id=analysis.id)

    except Exception as e:
        logger.error(f"创建分析失败: {e}")
        messages.error(request, f'创建分析失败: {str(e)}')
        return redirect('ai_analysis:create_analysis')


@login_required
@require_http_methods(["GET"])
def analysis_detail(request, analysis_id):
    """
    分析详情页面
    """
    analysis = get_object_or_404(
        StudentAnalysis.objects.select_related('student'),
        pk=analysis_id
    )

    context = {
        'analysis': analysis,
        'analysis_types': StudentAnalysis.ANALYSIS_TYPES,
        'status_choices': StudentAnalysis.STATUS_CHOICES,
    }

    return render(request, 'ai_analysis/detail.html', context)


@login_required
@require_http_methods(["POST"])
def run_analysis(request, analysis_id):
    """
    执行 AI 分析
    """
    analysis = get_object_or_404(StudentAnalysis, pk=analysis_id)

    if analysis.status != 'pending':
        return JsonResponse({
            'success': False,
            'error': '只有待处理的分析才能执行'
        })

    try:
        # 更新状态为处理中
        analysis.status = 'processing'
        analysis.save()

        # 获取 DeepSeek 客户端
        client = get_deepseek_client()

        # 准备提示词
        prompt = format_prompt(analysis)

        # 保存实际使用的提示词
        analysis.actual_prompt = prompt
        analysis.save()

        # 调用 AI API
        result = client.generate_analysis(
            prompt=prompt,
            student_analysis_id=analysis.id,
            request_type='analysis'
        )

        if result['success']:
            # 验证响应质量
            validation = client.validate_response(result['content'])
            confidence = client.estimate_confidence(
                result['content'],
                len(analysis.input_data) if analysis.input_data else 0
            )

            # 更新分析结果
            analysis.status = 'completed'
            analysis.analysis_result = result['content']
            analysis.ai_confidence = Decimal(str(confidence))
            analysis.analyzed_at = timezone.now()
            analysis.save()

            return JsonResponse({
                'success': True,
                'message': '分析完成',
                'confidence': confidence,
                'response_time': result.get('response_time', 0),
                'validation': validation
            })
        else:
            analysis.status = 'failed'
            analysis.error_message = result.get('error', '未知错误')
            analysis.save()

            return JsonResponse({
                'success': False,
                'error': analysis.error_message
            })

    except Exception as e:
        logger.error(f"执行分析失败: {e}")
        analysis.status = 'failed'
        analysis.error_message = str(e)
        analysis.save()

        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_http_methods(["GET"])
def student_analysis_history(request, student_id):
    """
    学生分析历史记录
    """
    student = get_object_or_404(Student, pk=student_id)
    analyses = StudentAnalysis.objects.filter(
        student=student
    ).order_by('-created_at')

    context = {
        'student': student,
        'analyses': analyses,
    }

    return render(request, 'ai_analysis/student_history.html', context)


@login_required
@require_http_methods(["GET"])
def analysis_report(request, analysis_id):
    """
    生成并显示分析报告
    """
    analysis = get_object_or_404(
        StudentAnalysis.objects.select_related('student'),
        pk=analysis_id
    )

    if analysis.status != 'completed':
        messages.error(request, '分析尚未完成')
        return redirect('ai_analysis:analysis_detail', analysis_id=analysis.id)

    context = {
        'analysis': analysis,
        'report_data': json.loads(analysis.analysis_result) if analysis.analysis_result else None,
    }

    return render(request, 'ai_analysis/report.html', context)


@login_required
@require_http_methods(["GET"])
def service_logs(request):
    """
    AI 服务调用日志
    """
    logs = AIServiceLog.objects.all().order_by('-created_at')

    # 分页处理
    paginator = Paginator(logs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'request_types': AIServiceLog.REQUEST_TYPES,
        'status_choices': AIServiceLog.STATUS_CHOICES,
    }

    return render(request, 'ai_analysis/logs.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def api_analysis_callback(request):
    """
    API 回调接口（用于异步处理）
    """
    try:
        data = json.loads(request.body)
        analysis_id = data.get('analysis_id')
        result = data.get('result')
        status = data.get('status')

        if not analysis_id:
            return JsonResponse({'success': False, 'error': '缺少 analysis_id'})

        analysis = get_object_or_404(StudentAnalysis, pk=analysis_id)

        if status == 'success':
            analysis.status = 'completed'
            analysis.analysis_result = result.get('content', '')
            analysis.ai_confidence = Decimal(str(result.get('confidence', 0)))
            analysis.analyzed_at = timezone.now()
        else:
            analysis.status = 'failed'
            analysis.error_message = result.get('error', '未知错误')

        analysis.save()

        return JsonResponse({'success': True})

    except Exception as e:
        logger.error(f"API 回调处理失败: {e}")
        return JsonResponse({'success': False, 'error': str(e)})


# 辅助函数

def prepare_student_data(student: Student, analysis_type: str) -> Dict[str, Any]:
    """
    准备用于分析的学生数据

    Args:
        student: 学生对象
        analysis_type: 分析类型

    Returns:
        格式化的学生数据字典
    """
    # 基础学生信息
    base_data = {
        'student_name': student.name,
        'student_id': student.student_id,
        'gender': student.gender,
        'major': student.major,
        'college': student.college,
        'birth_date': str(student.birth_date),
    }

    # 获取学生成绩数据
    scores = Score.objects.filter(student=student).select_related('course')
    courses = Course.objects.filter(
        Q(score__student=student) | Q(enrollment__student=student)
    ).distinct()

    # 计算基础统计数据
    score_values = [float(s.score) for s in scores]
    if score_values:
        base_data.update({
            'average_score': sum(score_values) / len(score_values),
            'max_score': max(score_values),
            'min_score': min(score_values),
            'total_credits': sum(c.credits for c in courses),
            'course_count': len(courses),
        })

    # 根据分析类型准备特定数据
    if analysis_type == 'academic_performance':
        return prepare_academic_performance_data(student, scores, courses, base_data)
    elif analysis_type == 'learning_progress':
        return prepare_learning_progress_data(student, scores, courses, base_data)
    elif analysis_type == 'strength_weakness':
        return prepare_strength_weakness_data(student, scores, courses, base_data)
    elif analysis_type == 'improvement_suggestions':
        return prepare_improvement_suggestions_data(student, scores, courses, base_data)
    else:  # comprehensive
        return prepare_comprehensive_data(student, scores, courses, base_data)


def prepare_academic_performance_data(student: Student, scores: List[Score],
                                    courses: List[Course], base_data: Dict) -> Dict:
    """准备学业表现分析数据"""
    # 按课程类型分组统计
    course_type_stats = {}
    for score in scores:
        course_type = getattr(score.course, 'course_type', 'UNKNOWN')
        if course_type not in course_type_stats:
            course_type_stats[course_type] = []
        course_type_stats[course_type].append(float(score.score))

    # 计算各类型平均分
    type_averages = {k: sum(v)/len(v) for k, v in course_type_stats.items()}

    # 成绩分布
    score_distribution = {
        'excellent': len([s for s in scores if s.score >= 90]),
        'good': len([s for s in scores if 80 <= s.score < 90]),
        'average': len([s for s in scores if 70 <= s.score < 80]),
        'pass': len([s for s in scores if 60 <= s.score < 70]),
        'fail': len([s for s in scores if s.score < 60]),
    }

    base_data.update({
        'course_type_averages': type_averages,
        'score_distribution': score_distribution,
        'detailed_scores': [
            {
                'course_name': s.course.course_name,
                'course_id': s.course.course_id,
                'score': float(s.score),
                'credits': s.course.credits,
                'date': str(s.date),
            }
            for s in scores
        ]
    })

    return base_data


def prepare_learning_progress_data(student: Student, scores: List[Score],
                                 courses: List[Course], base_data: Dict) -> Dict:
    """准备学习进度分析数据"""
    # 按时间排序的成绩
    scores_by_date = sorted(scores, key=lambda x: x.date)

    # 计算学习进度趋势
    progress_trend = []
    cumulative_avg = 0
    for i, score in enumerate(scores_by_date, 1):
        cumulative_avg = (cumulative_avg * (i-1) + float(score.score)) / i
        progress_trend.append({
            'date': str(score.date),
            'score': float(score.score),
            'cumulative_average': cumulative_avg,
            'course_name': score.course.course_name,
        })

    # 课程完成情况
    completed_courses = scores.count()
    total_courses = courses.count()
    completion_rate = (completed_courses / total_courses * 100) if total_courses > 0 else 0

    base_data.update({
        'progress_trend': progress_trend,
        'completion_rate': completion_rate,
        'completed_courses': completed_courses,
        'total_courses': total_courses,
        'time_period': f"{scores_by_date[0].date if scores_by_date else 'N/A'} 到 {scores_by_date[-1].date if scores_by_date else 'N/A'}"
    })

    return base_data


def prepare_strength_weakness_data(student: Student, scores: List[Score],
                                 courses: List[Course], base_data: Dict) -> Dict:
    """准备优势劣势分析数据"""
    # 分析强势和弱势课程
    score_course_pairs = [(float(s.score), s.course) for s in scores]
    score_course_pairs.sort(reverse=True)

    # 强势课程（前20%）
    strong_courses = score_course_pairs[:max(1, len(score_course_pairs) // 5)]
    # 弱势课程（后20%）
    weak_courses = score_course_pairs[-max(1, len(score_course_pairs) // 5):]

    base_data.update({
        'strong_courses': [
            {
                'course_name': course.course_name,
                'score': score,
                'credits': course.credits,
                'course_id': course.course_id,
            }
            for score, course in strong_courses
        ],
        'weak_courses': [
            {
                'course_name': course.course_name,
                'score': score,
                'credits': course.credits,
                'course_id': course.course_id,
            }
            for score, course in weak_courses
        ],
        'course_details': [
            {
                'course_name': s.course.course_name,
                'course_id': s.course.course_id,
                'score': float(s.score),
                'credits': s.course.credits,
                'date': str(s.date),
            }
            for s in scores
        ]
    })

    return base_data


def prepare_improvement_suggestions_data(student: Student, scores: List[Score],
                                       courses: List[Course], base_data: Dict) -> Dict:
    """准备改进建议数据"""
    # 分析学习模式
    recent_scores = scores.filter(date__gte=timezone.now() - timedelta(days=90))
    older_scores = scores.filter(date__lt=timezone.now() - timedelta(days=90))

    recent_avg = sum(float(s.score) for s in recent_scores) / len(recent_scores) if recent_scores else 0
    older_avg = sum(float(s.score) for s in older_scores) / len(older_scores) if older_scores else 0

    # 识别学习问题
    learning_issues = []
    if recent_avg < older_avg - 5:
        learning_issues.append('近期成绩呈下降趋势')
    if len([s for s in scores if s.score < 60]) > len(scores) * 0.2:
        learning_issues.append('挂科率较高')
    if len(scores) < 10:
        learning_issues.append('课程数量偏少')

    base_data.update({
        'current_performance': {
            'recent_average': recent_avg,
            'older_average': older_avg,
            'trend': 'improving' if recent_avg > older_avg + 5 else 'declining' if recent_avg < older_avg - 5 else 'stable',
        },
        'learning_history': {
            'total_courses': len(scores),
            'failed_courses': len([s for s in scores if s.score < 60]),
            'excellent_courses': len([s for s in scores if s.score >= 90]),
        },
        'learning_patterns': {
            'issues': learning_issues,
            'course_load': 'heavy' if len(scores) > 15 else 'light' if len(scores) < 8 else 'normal',
        },
        'academic_status': f"平均分: {sum(float(s.score) for s in scores) / len(scores):.1f}" if scores else "暂无成绩数据"
    })

    return base_data


def prepare_comprehensive_data(student: Student, scores: List[Score],
                             courses: List[Course], base_data: Dict) -> Dict:
    """准备综合分析数据"""
    # 整合所有分析数据
    base_data.update(prepare_academic_performance_data(student, scores, courses, {}))
    base_data.update(prepare_learning_progress_data(student, scores, courses, {}))
    base_data.update(prepare_strength_weakness_data(student, scores, courses, {}))
    base_data.update(prepare_improvement_suggestions_data(student, scores, courses, {}))

    # 添加综合分析特有数据
    base_data.update({
        'age': (timezone.now().date() - student.birth_date).days // 365,
        'academic_performance_data': json.dumps(base_data, ensure_ascii=False),
        'learning_behavior_data': json.dumps({
            'study_hours_per_week': '估算值',
            'preferred_study_time': '待收集',
            'study_methods': ['待收集'],
        }, ensure_ascii=False),
        'course_enrollment_data': json.dumps({
            'total_enrolled': courses.count(),
            'active_courses': scores.count(),
            'completed_rate': f"{(scores.count() / courses.count() * 100):.1f}%" if courses.count() > 0 else "0%",
        }, ensure_ascii=False),
        'grade_trend_data': json.dumps(base_data.get('progress_trend', []), ensure_ascii=False),
    })

    return base_data


def format_prompt(analysis: StudentAnalysis) -> str:
    """
    格式化提示词

    Args:
        analysis: 分析对象

    Returns:
        格式化后的提示词
    """
    template = analysis.prompt_template
    if not template:
        template = PROMPT_TEMPLATES.get(analysis.analysis_type, '')

    if not template:
        raise ValueError(f"未找到分析类型 {analysis.analysis_type} 的提示词模板")

    # 准备变量数据
    data = analysis.input_data or {}

    # 添加格式化的数据
    if 'detailed_scores' in data:
        data['academic_data'] = format_academic_data_for_prompt(data['detailed_scores'])

    if 'progress_trend' in data:
        data['progress_data'] = format_progress_data_for_prompt(data['progress_trend'])

    if 'course_details' in data:
        data['course_completion_data'] = format_course_data_for_prompt(data['course_details'])

    try:
        # 格式化提示词
        formatted_prompt = template.format(**data)
        return formatted_prompt
    except KeyError as e:
        logger.error(f"提示词格式化失败，缺少变量: {e}")
        raise ValueError(f"提示词模板变量不完整: {e}")


def format_academic_data_for_prompt(scores: List[Dict]) -> str:
    """格式化学业数据用于提示词"""
    if not scores:
        return "暂无成绩数据"

    data_lines = [
        f"### 课程成绩详情",
        f"| 课程名称 | 课程代码 | 成绩 | 学分 | 考试日期 |",
        f"|---------|---------|------|------|----------|",
    ]

    for score in scores:
        data_lines.append(
            f"| {score['course_name']} | {score['course_id']} | {score['score']} | {score['credits']} | {score['date']} |"
        )

    return '\n'.join(data_lines)


def format_progress_data_for_prompt(progress: List[Dict]) -> str:
    """格式化进度数据用于提示词"""
    if not progress:
        return "暂无进度数据"

    data_lines = [
        f"### 学习进度趋势",
        f"| 日期 | 课程名称 | 成绩 | 累计平均 |",
        f"|------|---------|------|----------|",
    ]

    for item in progress:
        data_lines.append(
            f"| {item['date']} | {item['course_name']} | {item['score']} | {item['cumulative_average']:.2f} |"
        )

    return '\n'.join(data_lines)


def format_course_data_for_prompt(courses: List[Dict]) -> str:
    """格式化课程数据用于提示词"""
    if not courses:
        return "暂无课程数据"

    data_lines = [
        f"### 课程修读情况",
        f"| 课程名称 | 课程代码 | 成绩 | 学分 |",
        f"|---------|---------|------|------|",
    ]

    for course in courses:
        data_lines.append(
            f"| {course['course_name']} | {course['course_id']} | {course['score']} | {course['credits']} |"
        )

    return '\n'.join(data_lines)