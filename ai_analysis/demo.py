"""
AI 分析演示页面
"""

from django.shortcuts import render
from ai_analysis.models import StudentAnalysis, PromptTemplate
from students.models import Student

def demo_page(request):
    """AI 分析演示页面"""

    # 获取统计数据
    stats = {
        'total_students': Student.objects.count(),
        'total_analyses': StudentAnalysis.objects.count(),
        'completed_analyses': StudentAnalysis.objects.filter(status='completed').count(),
        'pending_analyses': StudentAnalysis.objects.filter(status='pending').count(),
        'total_templates': PromptTemplate.objects.count(),
    }

    # 获取最近的分析记录
    recent_analyses = StudentAnalysis.objects.select_related('student').order_by('-created_at')[:5]

    context = {
        'stats': stats,
        'recent_analyses': recent_analyses,
    }

    return render(request, 'ai_analysis/simple_test.html', context)