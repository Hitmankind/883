from django.urls import path
from . import views

urlpatterns = [
    # 登录相关
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    # 首页
    path('', views.index, name='index'),
    
    # 学生管理
    path('students/', views.student_list, name='student_list'),
    path('students/add/', views.student_add, name='student_add'),
    path('students/edit/<str:student_id>/', views.student_edit, name='student_edit'),
    path('students/delete/<str:student_id>/', views.student_delete, name='student_delete'),
    path('students/search/', views.student_search, name='student_search'),
    
    # 课程管理
    path('courses/', views.course_list, name='course_list'),
    path('courses/add/', views.course_add, name='course_add'),
    path('courses/edit/<str:course_id>/', views.course_edit, name='course_edit'),
    path('courses/delete/<str:course_id>/', views.course_delete, name='course_delete'),
    
    # 选课管理
    path('enrollment/', views.enrollment_manage, name='enrollment_manage'),
    
    # 成绩管理
    path('scores/', views.score_list, name='score_list'),
    path('scores/batch-input/', views.score_batch_input, name='score_batch_input'),
    path('scores/single-input/', views.score_single_input, name='score_single_input'),
    path('scores/edit/<int:score_id>/', views.score_edit, name='score_edit'),
    path('scores/delete/<int:score_id>/', views.score_delete, name='score_delete'),
    
    # 统计分析
    path('transcript/<str:student_id>/', views.student_transcript, name='student_transcript'),
    path('statistics/', views.course_statistics, name='course_statistics'),
    
    # AI分析中心
    path('ai-dashboard/', views.ai_learning_dashboard, name='ai_learning_dashboard'),
    path('student-ai-analysis/<str:student_id>/', views.student_ai_analysis, name='student_ai_analysis'),
    path('ai-intervention-dashboard/', views.ai_intervention_dashboard, name='ai_intervention_dashboard'),
    
    # AJAX接口
    path('api/course-students/', views.get_course_students, name='get_course_students'),
    path('api/student-courses/<str:student_id>/', views.get_student_courses, name='get_student_courses'),
    
    # 数据同步
    path('sync/', views.sync_data, name='sync_data'),
]