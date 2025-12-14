"""
AI 分析应用 URL 配置
"""

from django.urls import path
from . import views
from . import views_enhanced
from . import views_simple
from . import test_views as test
from . import demo

urlpatterns = [
    # 分析仪表板
    path('dashboard/', views.analysis_dashboard, name='dashboard'),

    # 创建分析
    path('create/', views.create_analysis, name='create_analysis'),

    # 分析详情
    path('detail/<int:analysis_id>/', views.analysis_detail, name='analysis_detail'),

    # 执行分析
    path('run/<int:analysis_id>/', views.run_analysis, name='run_analysis'),

    # 分析报告
    path('report/<int:analysis_id>/', views.analysis_report, name='analysis_report'),

    # 学生分析历史
    path('student/<int:student_id>/history/', views.student_analysis_history, name='student_history'),

    # 服务日志
    path('logs/', views.service_logs, name='service_logs'),

    # API 回调
    path('api/callback/', views.api_analysis_callback, name='api_callback'),

    # 测试路由
    path('test/dashboard/', test.test_dashboard, name='test_dashboard'),
    path('test/create/', test.test_create_analysis, name='test_create'),
    path('test/detail/<int:analysis_id>/', test.test_analysis_detail, name='test_detail'),
    path('test/students/', test.test_students_info, name='test_students'),

    # 演示路由
    path('demo/', demo.demo_page, name='demo_page'),

    # 增强版 AI 功能路由
    path('ai-dashboard/', views_enhanced.ai_dashboard, name='ai_dashboard'),
    path('ai-intervention/', views_enhanced.ai_intervention_dashboard, name='ai_intervention'),
    path('student/<int:student_id>/analysis/', views_enhanced.student_ai_analysis_detail, name='student_ai_analysis_detail'),
    path('report/generate/', views_enhanced.ai_report_generation, name='ai_report_generation'),
    path('history/', views_enhanced.ai_analysis_history, name='ai_analysis_history'),
    path('suggestions/', views_enhanced.ai_suggestions_system, name='ai_suggestions_system'),
    path('ajax/', views_enhanced.ai_analysis_ajax, name='ai_analysis_ajax'),
]