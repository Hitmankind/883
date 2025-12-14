"""
临时测试视图 - 用于验证 AI 分析功能
"""

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from students.models import Student
from ai_analysis.models import StudentAnalysis
from ai_analysis.prompts import PROMPT_TEMPLATES
from ai_analysis.views import prepare_student_data, format_prompt

def test_dashboard(request):
    """测试仪表板"""
    analyses = StudentAnalysis.objects.select_related('student').order_by('-created_at')[:10]

    stats = {
        'total_analyses': analyses.count(),
        'completed_analyses': analyses.filter(status='completed').count(),
        'pending_analyses': analyses.filter(status='pending').count(),
        'failed_analyses': analyses.filter(status='failed').count(),
    }

    context = {
        'analyses': analyses,
        'stats': stats,
        'analysis_types': StudentAnalysis.ANALYSIS_TYPES,
    }

    return render(request, 'ai_analysis/test_dashboard.html', context)

def test_create_analysis(request):
    """测试创建分析"""
    if request.method == 'POST':
        try:
            student_id = request.POST.get('student_id')
            analysis_type = request.POST.get('analysis_type')
            title = request.POST.get('title', f'{analysis_type}分析')

            if not student_id or not analysis_type:
                return JsonResponse({'success': False, 'error': '请选择学生和分析类型'})

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

            return JsonResponse({
                'success': True,
                'analysis_id': analysis.id,
                'message': '分析任务已创建'
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    # GET 请求
    students = Student.objects.all()
    analysis_types = StudentAnalysis.ANALYSIS_TYPES

    context = {
        'students': students,
        'analysis_types': analysis_types,
    }

    return render(request, 'ai_analysis/test_create.html', context)

def test_analysis_detail(request, analysis_id):
    """测试分析详情"""
    analysis = get_object_or_404(
        StudentAnalysis.objects.select_related('student'),
        pk=analysis_id
    )

    context = {
        'analysis': analysis,
        'analysis_types': StudentAnalysis.ANALYSIS_TYPES,
        'status_choices': StudentAnalysis.STATUS_CHOICES,
    }

    return render(request, 'ai_analysis/test_detail.html', context)

def test_students_info(request):
    """显示学生信息，用于测试"""
    students = Student.objects.all()
    return render(request, 'ai_analysis/test_students.html', {'students': students})