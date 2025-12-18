from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Avg, Max, Min, Count
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from datetime import datetime, date
import json

from .models import Student, Course, Score, Enrollment, CustomUser
from .utils import DataFileManager, get_grade_level, calculate_grade_statistics


# 登录相关视图
@require_http_methods(['GET', 'POST'])
def login(request):
    """登录视图"""
    if request.user.is_authenticated:
        return redirect('students:index')
    
    if request.method == 'POST':
        # 直接使用Django的authenticate函数，它会自动处理密码验证
        username = request.POST.get('username')
        password = request.POST.get('password')
        user_type = request.POST.get('user_type')  # 'student' 或 'teacher'
        
        # 使用Django的authenticate进行用户认证
        user = authenticate(username=username, password=password)
        
        if user is not None:
            # 验证用户类型是否匹配
            if user.role == user_type:
                # 确保用户是活跃的
                if user.is_active:
                    auth_login(request, user)
                    messages.success(request, f'欢迎回来，{user.username}！')
                    return redirect('students:index')
                else:
                    messages.error(request, '该账户已被禁用！')
            else:
                messages.error(request, '用户类型不匹配！')
        else:
            messages.error(request, '用户名或密码错误！')
    
    return render(request, 'students/login.html')

def logout(request):
    """注销视图"""
    auth_logout(request)
    messages.success(request, '已成功注销！')
    return redirect('students:login')

# 教师角色验证装饰器
def teacher_required(view_func):
    """验证用户是否为教师"""
    @login_required
    def wrapped_view(request, *args, **kwargs):
        if not request.user.role == 'teacher':
            messages.error(request, '您没有权限访问此页面！')
            return redirect('index')
        return view_func(request, *args, **kwargs)
    return wrapped_view

def index(request):
    """首页"""
    if not request.user.is_authenticated:
        return redirect('students:login')
    
    # 如果是学生登录，显示学生专属首页
    if request.user.role == 'student':
        return render(request, 'students/student_dashboard.html')
    
    # 获取统计信息（教师视图）
    student_count = Student.objects.count()
    course_count = Course.objects.count()
    score_count = Score.objects.count()
    enrollment_count = Enrollment.objects.count()
    
    return render(request, 'students/index.html', {
        'student_count': student_count,
        'course_count': course_count,
        'score_count': score_count,
        'enrollment_count': enrollment_count
    })


@teacher_required
def robot_arm(request):
    """Teaching Mechanical Arm module page (demo)."""
    return render(request, 'students/robot_arm.html')


# 学生信息管理
@teacher_required
def student_list(request):
    """学生列表"""
    students = Student.objects.all().order_by('student_id')
    
    # 搜索功能
    search_query = request.GET.get('search', '')
    if search_query:
        students = students.filter(
            Q(student_id__icontains=search_query) |
            Q(name__icontains=search_query) |
            Q(major__icontains=search_query) |
            Q(college__icontains=search_query)
        )
    
    # 分页
    paginator = Paginator(students, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'students/student_list.html', {
        'page_obj': page_obj,
        'students': page_obj,  # 添加students变量以匹配模板
        'search_query': search_query,
        'is_paginated': page_obj.has_other_pages()  # 添加分页标志
    })


@teacher_required
def student_add(request):
    """添加学生"""
    if request.method == 'POST':
        try:
            student_id = request.POST['student_id']
            
            # 检查学生是否已存在
            if Student.objects.filter(student_id=student_id).exists():
                messages.error(request, f'学号 {student_id} 已存在，请使用其他学号！')
                return render(request, 'students/student_form.html', {
                    'action': '添加',
                    'form_data': request.POST
                })
            
            student = Student(
                student_id=student_id,
                name=request.POST['name'],
                gender=request.POST['gender'],
                birth_date=datetime.strptime(request.POST['birth_date'], '%Y-%m-%d').date(),
                major=request.POST['major'],
                college=request.POST['college']
            )
            student.full_clean()  # 验证数据
            student.save()
            student.save_to_file()  # 保存到文件
            messages.success(request, '学生信息添加成功！')
            return redirect('students:student_list')
        except ValueError as e:
            messages.error(request, f'数据格式错误：{str(e)}')
        except Exception as e:
            messages.error(request, f'添加失败：{str(e)}')
        
        # 如果出错，返回表单并保留用户输入的数据
        return render(request, 'students/student_form.html', {
            'action': '添加',
            'form_data': request.POST
        })
    
    return render(request, 'students/student_form.html', {'action': '添加'})


@teacher_required
def student_edit(request, student_id):
    """编辑学生"""
    student = get_object_or_404(Student, student_id=student_id)
    
    if request.method == 'POST':
        try:
            student.name = request.POST['name']
            student.gender = request.POST['gender']
            student.birth_date = datetime.strptime(request.POST['birth_date'], '%Y-%m-%d').date()
            student.major = request.POST['major']
            student.college = request.POST['college']
            student.full_clean()
            student.save()
            student.save_to_file()
            messages.success(request, '学生信息修改成功！')
            return redirect('students:student_list')
        except Exception as e:
            messages.error(request, f'修改失败：{str(e)}')
    
    return render(request, 'students/student_form.html', {
        'student': student,
        'action': '编辑'
    })


@teacher_required
def student_delete(request, student_id):
    """删除学生"""
    student = get_object_or_404(Student, student_id=student_id)
    
    if request.method == 'POST':
        try:
            # 删除相关的成绩和选课记录
            Score.objects.filter(student=student).delete()
            Enrollment.objects.filter(student=student).delete()
            
            # 从文件中删除
            data_manager = DataFileManager()
            data_manager.delete_student_from_file(student_id)
            
            student.delete()
            messages.success(request, '学生信息删除成功！')
        except Exception as e:
            messages.error(request, f'删除失败：{str(e)}')
    
    return redirect('student_list')


@login_required
def student_search(request):
    """学生搜索"""
    search_type = request.GET.get('search_type', 'name')
    query = request.GET.get('query', '')
    
    students = []  # 默认为空列表，只有在有查询条件时才显示结果
    
    if query:  # 只有当有查询内容时才进行搜索
        students = Student.objects.all()
        if search_type == 'name':
            students = students.filter(name__icontains=query)
        elif search_type == 'major':
            students = students.filter(major__icontains=query)
        elif search_type == 'college':
            students = students.filter(college__icontains=query)
        elif search_type == 'student_id':
            students = students.filter(student_id__icontains=query)
    
    return render(request, 'students/student_search.html', {
        'students': students,
        'search_type': search_type,
        'query': query
    })


# 课程信息管理
@teacher_required
def course_list(request):
    """课程列表"""
    courses = Course.objects.all().order_by('course_id')
    
    search_query = request.GET.get('search', '')
    if search_query:
        courses = courses.filter(
            Q(course_id__icontains=search_query) |
            Q(course_name__icontains=search_query)
        )
    
    paginator = Paginator(courses, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'students/course_list.html', {
        'page_obj': page_obj,
        'courses': page_obj,  # 模板中使用的是courses变量
        'search_query': search_query,
        'is_paginated': page_obj.has_other_pages()
    })


@teacher_required
def course_add(request):
    """添加课程"""
    if request.method == 'POST':
        try:
            course = Course(
                course_id=request.POST['course_id'],
                course_name=request.POST['course_name'],
                credits=int(request.POST['credits'])
            )
            course.full_clean()
            course.save()
            course.save_to_file()
            messages.success(request, '课程信息添加成功！')
            return redirect('students:course_list')
        except Exception as e:
            messages.error(request, f'添加失败：{str(e)}')
    
    return render(request, 'students/course_form.html', {'action': '添加'})


@teacher_required
def course_edit(request, course_id):
    """编辑课程"""
    course = get_object_or_404(Course, course_id=course_id)
    
    if request.method == 'POST':
        try:
            course.course_name = request.POST['course_name']
            course.credits = int(request.POST['credits'])
            course.full_clean()
            course.save()
            course.save_to_file()
            messages.success(request, '课程信息修改成功！')
            return redirect('students:course_list')
        except Exception as e:
            messages.error(request, f'修改失败：{str(e)}')
    
    return render(request, 'students/course_form.html', {
        'course': course,
        'action': '编辑'
    })


@teacher_required
def course_delete(request, course_id):
    """删除课程"""
    course = get_object_or_404(Course, course_id=course_id)
    
    if request.method == 'POST':
        try:
            # 删除相关的成绩和选课记录
            Score.objects.filter(course=course).delete()
            Enrollment.objects.filter(course=course).delete()
            
            # 从文件中删除
            data_manager = DataFileManager()
            data_manager.delete_course_from_file(course_id)
            
            course.delete()
            messages.success(request, '课程信息删除成功！')
        except Exception as e:
            messages.error(request, f'删除失败：{str(e)}')
    
    return redirect('course_list')


# 选课管理
@teacher_required
def enrollment_manage(request):
    """选课管理"""
    students = Student.objects.all().order_by('student_id')
    courses = Course.objects.all().order_by('course_id')
    
    # 获取选中的学生
    selected_student_id = request.GET.get('student_id') or request.POST.get('student_id')
    selected_student = None
    current_enrollments = []
    available_courses = courses
    enrolled_course_ids = []
    
    if selected_student_id:
        try:
            selected_student = Student.objects.get(student_id=selected_student_id)
            current_enrollments = Enrollment.objects.filter(student=selected_student).select_related('course')
            enrolled_course_ids = [e.course.course_id for e in current_enrollments]
            available_courses = courses  # 显示所有课程，已选的会被标记
        except Student.DoesNotExist:
            pass
    
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        course_ids = request.POST.getlist('course_ids')
        
        try:
            student = Student.objects.get(student_id=student_id)
            # 清除该学生的现有选课记录
            Enrollment.objects.filter(student=student).delete()
            
            # 添加新的选课记录
            for course_id in course_ids:
                course = Course.objects.get(course_id=course_id)
                Enrollment.objects.create(student=student, course=course)
            
            messages.success(request, f'学生 {student.name} 的选课信息更新成功！')
            
            # 重新获取更新后的选课信息
            current_enrollments = Enrollment.objects.filter(student=student).select_related('course')
            enrolled_course_ids = [e.course.course_id for e in current_enrollments]
            
        except Exception as e:
            messages.error(request, f'选课失败：{str(e)}')
    
    # 获取所有选课信息（用于其他功能）
    enrollments = {}
    for enrollment in Enrollment.objects.all():
        if enrollment.student.student_id not in enrollments:
            enrollments[enrollment.student.student_id] = []
        enrollments[enrollment.student.student_id].append(enrollment.course.course_id)
    
    return render(request, 'students/enrollment_manage.html', {
        'students': students,
        'courses': courses,
        'selected_student': selected_student,
        'current_enrollments': current_enrollments,
        'available_courses': available_courses,
        'enrolled_course_ids': enrolled_course_ids,
        'enrollments': enrollments
    })


# 成绩管理
@teacher_required
def score_list(request):
    """成绩列表"""
    scores = Score.objects.all().select_related('student', 'course').order_by('-date')
    
    # 搜索功能
    search_query = request.GET.get('search', '')
    if search_query:
        scores = scores.filter(
            Q(student__student_id__icontains=search_query) |
            Q(student__name__icontains=search_query) |
            Q(course__course_id__icontains=search_query) |
            Q(course__course_name__icontains=search_query)
        )
    
    paginator = Paginator(scores, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'students/score_list.html', {
        'page_obj': page_obj,
        'search_query': search_query
    })


@teacher_required
def score_batch_input(request):
    """批量录入成绩"""
    if request.method == 'POST':
        course_id = request.POST.get('course_id')
        try:
            course = Course.objects.get(course_id=course_id)
            # 获取选修该课程的学生
            enrolled_students = Enrollment.objects.filter(course=course).select_related('student')
            
            success_count = 0
            for enrollment in enrolled_students:
                score_value = request.POST.get(f'score_{enrollment.student.student_id}')
                if score_value and score_value.strip():
                    try:
                        score_obj, created = Score.objects.get_or_create(
                            student=enrollment.student,
                            course=course,
                            defaults={'score': float(score_value)}
                        )
                        if not created:
                            score_obj.score = float(score_value)
                            score_obj.save()
                        
                        score_obj.save_to_file()
                        success_count += 1
                    except ValueError:
                        continue
            
            messages.success(request, f'成功录入 {success_count} 条成绩！')
            return redirect('students:score_list')
        except Course.DoesNotExist:
            messages.error(request, '课程不存在！')
    
    courses = Course.objects.all().order_by('course_id')
    
    # 如果选择了课程，显示选修该课程的学生
    selected_course_id = request.GET.get('course_id')
    selected_course = None
    enrolled_students = []
    
    if selected_course_id:
        try:
            selected_course = Course.objects.get(course_id=selected_course_id)
            enrolled_students = Enrollment.objects.filter(course=selected_course).select_related('student')
            # 获取已有成绩
            existing_scores = {score.student.student_id: score.score 
                             for score in Score.objects.filter(course=selected_course)}
            for enrollment in enrolled_students:
                enrollment.existing_score = existing_scores.get(enrollment.student.student_id, '')
        except Course.DoesNotExist:
            pass
    
    return render(request, 'students/score_batch_input.html', {
        'courses': courses,
        'enrolled_students': enrolled_students,
        'selected_course': selected_course,
        'selected_course_id': selected_course_id
    })


@teacher_required
def score_single_input(request):
    """单个成绩录入"""
    if request.method == 'POST':
        try:
            student = Student.objects.get(student_id=request.POST['student_id'])
            course = Course.objects.get(course_id=request.POST['course_id'])
            score_value = float(request.POST['score'])
            
            score_obj, created = Score.objects.get_or_create(
                student=student,
                course=course,
                defaults={'score': score_value}
            )
            if not created:
                score_obj.score = score_value
                score_obj.save()
            
            score_obj.save_to_file()
            messages.success(request, '成绩录入成功！')
            return redirect('students:score_single_input')
        except (Student.DoesNotExist, Course.DoesNotExist):
            messages.error(request, '学生或课程不存在！')
        except ValueError:
            messages.error(request, '成绩格式不正确！')
        except Exception as e:
            messages.error(request, f'录入失败：{str(e)}')
    
    students = Student.objects.all().order_by('student_id')
    # 获取最近录入的成绩记录（最近10条）
    recent_scores = Score.objects.select_related('student', 'course').order_by('-date')[:10]
    
    return render(request, 'students/score_single_input.html', {
        'students': students,
        'recent_scores': recent_scores
    })


@teacher_required
def score_edit(request, score_id):
    """编辑成绩"""
    score = get_object_or_404(Score, id=score_id)
    
    if request.method == 'POST':
        try:
            score.score = float(request.POST['score'])
            score.save()
            score.save_to_file()
            messages.success(request, '成绩修改成功！')
            return redirect('students:score_list')
        except ValueError:
            messages.error(request, '成绩格式不正确！')
        except Exception as e:
            messages.error(request, f'修改失败：{str(e)}')
    
    return render(request, 'students/score_form.html', {'score': score})


@teacher_required
def score_delete(request, score_id):
    """删除成绩"""
    score = get_object_or_404(Score, id=score_id)
    
    if request.method == 'POST':
        try:
            # 从文件中删除
            data_manager = DataFileManager()
            data_manager.delete_score_from_file(score.student.student_id, score.course.course_id)
            
            score.delete()
            messages.success(request, '成绩删除成功！')
        except Exception as e:
            messages.error(request, f'删除失败：{str(e)}')
    
    return redirect('score_list')


# 统计分析
@login_required
def student_transcript(request, student_id=None):
    """学生个人成绩单"""
    # 学生只能查看自己的成绩
    if request.user.role == 'student':
        if request.user.student:
            student_id = request.user.student.student_id
        else:
            messages.error(request, '您的账号未关联学生信息！')
            return redirect('index')
    
    student = None
    scores = []
    statistics = {}
    
    # 初始化所有统计变量
    total_courses = 0
    total_credits = 0
    avg_score = 0
    highest_score = None
    lowest_score = None
    excellent_count = 0
    good_count = 0
    medium_count = 0
    pass_count = 0
    fail_count = 0
    jckc_count = 0
    zybx_count = 0
    zyxx_count = 0
    bysj_count = 0
    jckc_credits = 0
    zybx_credits = 0
    zyxx_credits = 0
    bysj_credits = 0
    
    # 从URL参数或GET参数获取student_id
    if student_id:
        target_student_id = student_id
    elif request.method == 'GET' and 'student_id' in request.GET and request.user.role == 'teacher':
        target_student_id = request.GET['student_id']
    else:
        target_student_id = None
    
    if target_student_id:
        try:
            student = Student.objects.get(student_id=target_student_id)
            scores = Score.objects.filter(student=student).select_related('course').order_by('course__course_id')
            
            if scores:
                score_values = [float(score.score) for score in scores]
                max_score = max(score_values)
                min_score = min(score_values)
                avg_score = sum(score_values) / len(score_values)
                
                # 基本统计
                total_courses = scores.count()
                total_credits = sum([score.course.credits for score in scores])
                
                # 最高最低成绩
                highest_score = scores.filter(score=max_score).first()
                lowest_score = scores.filter(score=min_score).first()
                
                # 成绩分布统计
                excellent_count = scores.filter(score__gte=90).count()
                good_count = scores.filter(score__gte=80, score__lt=90).count()
                medium_count = scores.filter(score__gte=70, score__lt=80).count()
                pass_count = scores.filter(score__gte=60, score__lt=70).count()
                fail_count = scores.filter(score__lt=60).count()
                
                # 课程类型统计
                jckc_scores = scores.filter(course__course_id__startswith='JCKC')
                zybx_scores = scores.filter(course__course_id__startswith='ZYBX')
                zyxx_scores = scores.filter(course__course_id__startswith='ZYXX')
                bysj_scores = scores.filter(course__course_id__startswith='BYSJ')
                
                jckc_count = jckc_scores.count()
                zybx_count = zybx_scores.count()
                zyxx_count = zyxx_scores.count()
                bysj_count = bysj_scores.count()
                
                jckc_credits = sum([score.course.credits for score in jckc_scores])
                zybx_credits = sum([score.course.credits for score in zybx_scores])
                zyxx_credits = sum([score.course.credits for score in zyxx_scores])
                bysj_credits = sum([score.course.credits for score in bysj_scores])
                
                statistics = {
                    'max_score': max_score,
                    'max_score_course': highest_score.course.course_name if highest_score else '',
                    'min_score': min_score,
                    'min_score_course': lowest_score.course.course_name if lowest_score else '',
                    'avg_score': round(avg_score, 2)
                }
        except Student.DoesNotExist:
            messages.error(request, '学生不存在！')
    
    students = Student.objects.all().order_by('student_id') if request.user.role == 'teacher' else []
    
    return render(request, 'students/student_transcript.html', {
        'students': students,
        'student': student,
        'scores': scores,
        'statistics': statistics,
        # 基本统计数据
        'total_courses': total_courses,
        'total_credits': total_credits,
        'average_score': avg_score,
        'highest_score': highest_score,
        'lowest_score': lowest_score,
        # 成绩分布
        'excellent_count': excellent_count,
        'good_count': good_count,
        'medium_count': medium_count,
        'pass_count': pass_count,
        'fail_count': fail_count,
        # 课程类型统计
        'jckc_count': jckc_count,
        'zybx_count': zybx_count,
        'zyxx_count': zyxx_count,
        'bysj_count': bysj_count,
        'jckc_credits': jckc_credits,
        'zybx_credits': zybx_credits,
        'zyxx_credits': zyxx_credits,
        'bysj_credits': bysj_credits,
    })


@teacher_required
def course_statistics(request):
    """课程成绩统计"""
    course = None
    scores = []
    statistics = {}
    
    # 初始化统计变量
    total_students = 0
    excellent_count = 0
    good_count = 0
    medium_count = 0
    pass_count = 0
    fail_count = 0
    excellent_percent = 0
    good_percent = 0
    medium_percent = 0
    pass_percent = 0
    fail_percent = 0
    average_score = 0
    highest_score = None
    lowest_score = None
    pass_students = 0
    pass_rate = 0
    major_stats = []
    
    if request.method == 'GET' and 'course_id' in request.GET:
        try:
            course = Course.objects.get(course_id=request.GET['course_id'])
            scores = Score.objects.filter(course=course).select_related('student').order_by('-score')
            
            # 获取选课总人数
            total_students = Enrollment.objects.filter(course=course).count()
            
            if scores:
                score_values = [float(score.score) for score in scores]
                total_scores = len(score_values)
                
                # 基本统计
                average_score = sum(score_values) / total_scores
                max_score = max(score_values)
                min_score = min(score_values)
                
                # 最高最低成绩
                highest_score = scores.filter(score=max_score).first()
                lowest_score = scores.filter(score=min_score).first()
                
                # 成绩分布统计
                excellent_count = scores.filter(score__gte=90).count()
                good_count = scores.filter(score__gte=80, score__lt=90).count()
                medium_count = scores.filter(score__gte=70, score__lt=80).count()
                pass_count = scores.filter(score__gte=60, score__lt=70).count()
                fail_count = scores.filter(score__lt=60).count()
                
                # 计算百分比
                excellent_percent = (excellent_count / total_scores) * 100
                good_percent = (good_count / total_scores) * 100
                medium_percent = (medium_count / total_scores) * 100
                pass_percent = (pass_count / total_scores) * 100
                fail_percent = (fail_count / total_scores) * 100
                
                # 及格率统计
                pass_students = excellent_count + good_count + medium_count + pass_count
                pass_rate = (pass_students / total_scores) * 100
                
                # 专业分布统计
                from django.db.models import Count, Avg
                major_data = scores.values('student__major').annotate(
                    count=Count('id'),
                    avg_score=Avg('score')
                ).order_by('-count')
                
                major_stats = []
                for major in major_data:
                    major_scores = scores.filter(student__major=major['student__major'])
                    major_pass_count = major_scores.filter(score__gte=60).count()
                    major_pass_rate = (major_pass_count / major['count']) * 100 if major['count'] > 0 else 0
                    
                    major_stats.append({
                        'major': major['student__major'],
                        'count': major['count'],
                        'avg_score': major['avg_score'],
                        'pass_rate': major_pass_rate
                    })
                
                statistics = calculate_grade_statistics(score_values)
        except Course.DoesNotExist:
            messages.error(request, '课程不存在！')
    
    courses = Course.objects.all().order_by('course_id')
    
    return render(request, 'students/course_statistics.html', {
        'courses': courses,
        'course': course,
        'scores': scores,
        'statistics': statistics,
        'total_students': total_students,
        'excellent_count': excellent_count,
        'good_count': good_count,
        'medium_count': medium_count,
        'pass_count': pass_count,
        'fail_count': fail_count,
        'excellent_percent': excellent_percent,
        'good_percent': good_percent,
        'medium_percent': medium_percent,
        'pass_percent': pass_percent,
        'fail_percent': fail_percent,
        'average_score': average_score,
        'highest_score': highest_score,
        'lowest_score': lowest_score,
        'pass_students': pass_students,
        'pass_rate': pass_rate,
        'major_stats': major_stats,
    })


# AJAX接口
@teacher_required
def get_course_students(request):
    """获取选修某课程的学生列表（AJAX）"""
    course_id = request.GET.get('course_id')
    if course_id:
        try:
            course = Course.objects.get(course_id=course_id)
            enrolled_students = Enrollment.objects.filter(course=course).select_related('student')
            students_data = []
            for enrollment in enrolled_students:
                students_data.append({
                    'student_id': enrollment.student.student_id,
                    'name': enrollment.student.name
                })
            return JsonResponse({'students': students_data})
        except Course.DoesNotExist:
            return JsonResponse({'error': '课程不存在'}, status=404)
    
    return JsonResponse({'error': '缺少课程ID'}, status=400)


@teacher_required
def sync_data(request):
    """数据同步"""
    if request.method == 'POST':
        try:
            sync_type = request.POST.get('sync_type', 'db_to_file')
            
            if sync_type == 'db_to_file':
                # 导出数据库数据到文件
                data_manager = DataFileManager()
                data_manager.sync_database_to_files()
                messages.success(request, '数据库数据已同步到文件！')
            elif sync_type == 'file_to_db':
                # 从文件导入数据到数据库
                student_count = Student.load_from_file()
                course_count = Course.load_from_file()
                score_count = Score.load_from_file()
                
                total_count = student_count + course_count + score_count
                if total_count > 0:
                    messages.success(request, f'文件数据已同步到数据库！导入了 {student_count} 个学生，{course_count} 门课程，{score_count} 条成绩记录。')
                else:
                    messages.info(request, '没有新数据需要导入。')
        except Exception as e:
            messages.error(request, f'同步失败：{str(e)}')
    
    return redirect('index')


@login_required
def get_student_courses(request, student_id):
    """AJAX接口：获取学生的选课信息"""
    from django.http import JsonResponse
    
    try:
        student = Student.objects.get(student_id=student_id)
        # 获取学生的选课记录
        enrollments = Enrollment.objects.filter(student=student).select_related('course')
        
        if not enrollments.exists():
            return JsonResponse({
                'success': False,
                'message': '该学生暂无选课记录'
            })
        
        courses = []
        course_details = {}
        
        for enrollment in enrollments:
            course = enrollment.course
            # 检查是否已有成绩
            existing_score = None
            try:
                score_obj = Score.objects.get(student=student, course=course)
                existing_score = score_obj.score
            except Score.DoesNotExist:
                pass
            
            course_info = {
                'course_id': course.course_id,
                'course_name': course.course_name,
                'credits': course.credits,
                'existing_score': existing_score
            }
            courses.append(course_info)
            
            # 详细信息用于前端显示
            course_details[course.course_id] = {
                'course_name': course.course_name,
                'credits': course.credits,
                'existing_score': existing_score
            }
        
        return JsonResponse({
            'success': True,
            'courses': courses,
            'course_details': course_details
        })
        
    except Student.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': '学生不存在'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'获取数据失败：{str(e)}'
        })
    
    return render(request, 'students/sync_data.html')


@teacher_required
def ai_learning_dashboard(request):
    """AI学习分析仪表板"""
    # 这里可以添加实际的数据处理逻辑
    return render(request, 'students/ai_learning_dashboard.html')


@teacher_required
def student_ai_analysis(request, student_id):
    """学生个人AI学习分析页面"""
    student = get_object_or_404(Student, student_id=student_id)
    # 这里可以添加实际的学生数据分析逻辑
    return render(request, 'students/student_ai_analysis.html', {'student': student})


@teacher_required
def ai_intervention_dashboard(request):
    """AI教学干预仪表板"""
    # Get all students for the dropdown
    students = Student.objects.all().order_by('student_id')
    return render(request, 'students/ai_intervention_dashboard.html', {'students': students})


@teacher_required
def generate_intervention_plan(request):
    """Generate intervention plan based on latest student course score data"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'})

    try:
        student_id = request.POST.get('student_id')
        if not student_id:
            return JsonResponse({'success': False, 'message': 'Student ID is required'})

        student = get_object_or_404(Student, student_id=student_id)

        # Collect latest course score data
        scores = Score.objects.filter(student=student).select_related('course').order_by('-date')

        if not scores.exists():
            return JsonResponse({
                'success': False,
                'message': f'No score data available for student {student_id}'
            })

        # Analyze student performance and generate intervention plan
        intervention_plan = generate_intervention_recommendations(student, scores)

        return JsonResponse({
            'success': True,
            'intervention_plan': intervention_plan
        })

    except Student.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Student not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error generating intervention plan: {str(e)}'})


def generate_intervention_recommendations(student, scores):
    """
    Generate personalized intervention recommendations based on student performance
    """
    # Calculate key metrics
    avg_score = scores.aggregate(avg=Avg('score'))['avg'] or 0
    recent_scores = scores[:10]  # Last 10 scores
    recent_avg = sum(s.score for s in recent_scores) / len(recent_scores) if recent_scores else 0

    # Group scores by course
    course_performance = {}
    for score in scores:
        if score.course.course_id not in course_performance:
            course_performance[score.course.course_id] = []
        course_performance[score.course.course_id].append(score.score)

    # Calculate course averages
    course_averages = {}
    for course_id, course_scores in course_performance.items():
        course_averages[course_id] = sum(course_scores) / len(course_scores)

    # Identify struggling courses (below 70)
    struggling_courses = []
    for course_id, avg in course_averages.items():
        if avg < 70:
            course_obj = scores.filter(course__course_id=course_id).first().course
            struggling_courses.append({
                'course_id': course_id,
                'course_name': course_obj.course_name,
                'average_score': avg,
                'latest_score': course_performance[course_id][-1] if course_performance[course_id] else 0
            })

    # Sort struggling courses by severity (lowest average first)
    struggling_courses.sort(key=lambda x: x['average_score'])

    # Generate intervention plan based on performance
    intervention_plan = {
        'student_info': {
            'student_id': student.student_id,
            'name': student.name,
            'overall_average': round(avg_score, 1),
            'recent_performance': round(recent_avg, 1),
            'total_courses': len(course_averages),
            'struggling_courses_count': len(struggling_courses)
        },
        'priority_level': 'high' if len(struggling_courses) >= 3 else 'medium' if len(struggling_courses) >= 1 else 'low',
        'interventions': []
    }

    # Generate specific interventions for struggling courses
    for i, course in enumerate(struggling_courses[:5]):  # Top 5 struggling courses
        priority = 'Critical' if i == 0 and course['average_score'] < 60 else 'High' if i < 2 else 'Medium'

        intervention = {
            'title': f"{course['course_name']} Performance Improvement",
            'priority': priority,
            'category': 'Academic Support',
            'description': f"Student is struggling with {course['course_name']} (Avg: {course['average_score']:.1f}, Latest: {course['latest_score']:.1f})",
            'actions': generate_course_specific_actions(course['average_score'], course['course_name']),
            'resources': generate_course_resources(course['course_name'], course['average_score']),
            'timeline': '4-6 weeks',
            'success_criteria': f"Improve average score to 75+ in {course['course_name']}",
            'responsible_teacher': 'Subject Teacher',
            'progress_monitoring': 'Weekly assessment reviews'
        }
        intervention_plan['interventions'].append(intervention)

    # Add general academic support if overall performance is low
    if avg_score < 65:
        intervention_plan['interventions'].append({
            'title': 'Overall Academic Performance Enhancement',
            'priority': 'High',
            'category': 'General Support',
            'description': f"Student needs comprehensive academic support (Overall Average: {avg_score:.1f})",
            'actions': [
                'Schedule twice-weekly tutoring sessions',
                'Implement daily study schedule monitoring',
                'Provide study skills workshops',
                'Create peer study groups',
                'Weekly progress meetings with academic advisor'
            ],
            'resources': [
                'Study skills development resources',
                'Time management tools',
                'Peer tutoring program',
                'Academic success workshops'
            ],
            'timeline': '8-12 weeks',
            'success_criteria': 'Achieve overall average of 70+',
            'responsible_teacher': 'Academic Advisor',
            'progress_monitoring': 'Bi-weekly comprehensive reviews'
        })

    # Add motivation support if recent performance declined
    if len(recent_scores) >= 10:
        # Convert to list to enable negative indexing
        scores_list = list(recent_scores)
        early_recent = scores_list[-5:]  # Last 5 scores (earlier in time)
        late_recent = scores_list[:5]    # First 5 scores (more recent)
        early_avg = sum(s.score for s in early_recent) / len(early_recent)
        late_avg = sum(s.score for s in late_recent) / len(late_recent)

        if late_avg < early_avg - 10:  # Decline of 10+ points
            intervention_plan['interventions'].append({
                'title': 'Motivation and Engagement Support',
                'priority': 'Medium',
                'category': 'Behavioral Support',
                'description': f'Student shows declining performance trend (From {early_avg:.1f} to {late_avg:.1f})',
                'actions': [
                    'Conduct motivational counseling session',
                    'Set achievable short-term goals',
                    'Identify and address learning barriers',
                    'Implement positive reinforcement strategies',
                    'Engage parents/guardians in support plan'
                ],
                'resources': [
                    'Student counseling services',
                    'Goal-setting worksheets',
                    'Motivation tracking tools',
                    'Parent communication templates'
                ],
                'timeline': '6-8 weeks',
                'success_criteria': 'Reverse declining trend and show improvement',
                'responsible_teacher': 'School Counselor',
                'progress_monitoring': 'Weekly motivation and engagement assessments'
            })

    return intervention_plan


def generate_course_specific_actions(average_score, course_name):
    """Generate specific actions based on course performance"""
    actions = []

    if average_score < 50:
        actions.extend([
            'Immediate one-on-one tutoring intervention',
            'Comprehensive diagnostic assessment',
            'Modified curriculum requirements',
            'Daily check-ins and progress monitoring',
            'Additional practice assignments with immediate feedback'
        ])
    elif average_score < 65:
        actions.extend([
            'Weekly tutoring sessions',
            'Targeted practice on weak areas',
            'Study group participation',
            'Increased formative assessments',
            'Peer mentorship assignment'
        ])
    else:
        actions.extend([
            'Weekly progress monitoring',
            'Targeted practice exercises',
            'Study skill enhancement',
            'Exam preparation workshops'
        ])

    # Add course-specific actions
    if 'Math' in course_name:
        actions.append('Step-by-step problem-solving techniques')
        actions.append('Math concept visualization tools')
    elif 'English' in course_name or 'Language' in course_name:
        actions.append('Reading comprehension strategies')
        actions.append('Writing practice with feedback')
    elif 'Science' in course_name:
        actions.append('Laboratory practice sessions')
        actions.append('Concept mapping for complex topics')

    return actions[:6]  # Limit to 6 actions


def generate_course_resources(course_name, average_score):
    """Generate course-specific learning resources"""
    resources = []

    # General resources
    resources.extend([
        f'YouTube: {course_name} tutorial videos',
        f'Khan Academy {course_name} resources',
        'Online practice problems and exercises',
        'Textbook study guides and supplements'
    ])

    # Performance-specific resources
    if average_score < 60:
        resources.append('Remedial learning materials')
        resources.append('Step-by-step video tutorials')
    elif average_score < 75:
        resources.append('Intermediate practice materials')
        resources.append('Concept reinforcement exercises')
    else:
        resources.append('Advanced practice challenges')
        resources.append('Extension activities')

    return resources[:5]  # Limit to 5 resources


@login_required
def my_ai_analysis(request):
    """Student personal AI analysis page"""
    # Ensure the user is a student
    if request.user.role != 'student':
        messages.error(request, 'This page is only available for students.')
        return redirect('students:index')

    try:
        student = request.user.student
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found.')
        return redirect('students:index')

    # Get recent analyses for this student
    from ai_analysis.models import StudentAnalysis
    recent_analyses = StudentAnalysis.objects.filter(
        student=student,
        status='completed'
    ).order_by('-created_at')[:5]

    # Get academic stats
    student_scores = Score.objects.filter(student=student)
    total_scores = student_scores.count()
    avg_score = student_scores.aggregate(avg=Avg('score'))['avg'] or 0

    context = {
        'student': student,
        'recent_analyses': recent_analyses,
        'total_scores': total_scores,
        'average_score': round(avg_score, 1),
    }

    return render(request, 'students/my_ai_analysis.html', context)
