#!/usr/bin/env python
"""
生成完整的 AI 学情分析假数据
"""

import os
import sys
import django
import random
from datetime import datetime, timedelta

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grade_management.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

django.setup()

from students.models import Student, Score, Course, Enrollment
from ai_analysis.models import StudentAnalysis, PromptTemplate, AIServiceLog
from decimal import Decimal

def generate_more_students():
    """生成更多学生数据"""

    students_data = [
        {
            'student_id': '20230017',
            'name': '张三',
            'gender': '男',
            'birth_date': datetime(2004, 3, 15).date(),
            'major': '计算机科学与技术',
            'college': '信息工程学院'
        },
        {
            'student_id': '20230018',
            'name': '李四',
            'gender': '女',
            'birth_date': datetime(2004, 7, 22).date(),
            'major': '软件工程',
            'college': '信息工程学院'
        },
        {
            'student_id': '20230019',
            'name': '王五',
            'gender': '男',
            'birth_date': datetime(2004, 11, 8).date(),
            'major': '人工智能',
            'college': '信息工程学院'
        },
        {
            'student_id': '20230020',
            'name': '赵六',
            'gender': '女',
            'birth_date': datetime(2004, 5, 18).date(),
            'major': '数据科学',
            'college': '信息工程学院'
        },
        {
            'student_id': '20230021',
            'name': '陈七',
            'gender': '男',
            'birth_date': datetime(2004, 9, 12).date(),
            'major': '网络工程',
            'college': '信息工程学院'
        }
    ]

    created_count = 0
    for student_data in students_data:
        try:
            student, created = Student.objects.get_or_create(
                student_id=student_data['student_id'],
                defaults=student_data
            )
            if created:
                created_count += 1
                print(f"[OK] 创建学生：{student.name}")
        except Exception as e:
            print(f"[ERROR] 创建学生失败：{e}")

    return created_count

def generate_comprehensive_analyses():
    """为所有学生生成综合分析"""

    students = Student.objects.all()
    analysis_types = ['comprehensive', 'academic_performance', 'strength_weakness', 'improvement_suggestions']

    # 分析结果模板
    analysis_templates = {
        'comprehensive': """# {student_name}的360度综合学情分析报告

## 执行摘要

### 关键发现
- 整体学业表现{performance_level}
- 在{subject_areas}方面表现{performance_desc}
- 需要重点关注{focus_areas}

### 核心建议
{core_suggestions}

## 详细分析
{detailed_analysis}

## 发展建议
{development_suggestions}""",

        'academic_performance': """# {student_name}学业表现分析

## 总体评估
- 平均成绩：{avg_score}分
- 排名：第{rank}名
- 学业趋势：{trend}

## 学科分析
{subject_analysis}

## 改进建议
{improvement_suggestions}""",

        'strength_weakness': """# {student_name}优势劣势分析

## SWOT分析

### 优势 (Strengths)
{strengths}

### 劣势 (Weaknesses)
{weaknesses}

### 机会 (Opportunities)
{opportunities}

### 威胁 (Threats)
{threats}

## 发展策略
{development_strategies}""",

        'improvement_suggestions': """# {student_name}学习改进建议

## 短期目标（1-3个月）
{short_term_goals}

## 中期目标（3-6个月）
{mid_term_goals}

## 长期目标（6-12个月）
{long_term_goals}

## 具体措施
{specific_measures}"""
    }

    created_count = 0
    for student in students:
        for analysis_type in analysis_types:
            # 检查是否已存在
            if StudentAnalysis.objects.filter(student=student, analysis_type=analysis_type).exists():
                continue

            # 生成假的分析结果
            performance_levels = ['优秀', '良好', '中等', '需要改进']
            performance_descs = ['突出', '稳定', '有待提升', '需要重点关注']

            result_data = {
                'student_name': student.name,
                'performance_level': random.choice(performance_levels),
                'performance_desc': random.choice(performance_descs),
                'subject_areas': random.choice(['专业课程', '基础课程', '实践课程']),
                'focus_areas': '时间管理和学习方法的改进',
                'core_suggestions': '制定合理的学习计划，加强基础知识学习',
                'detailed_analysis': '该学生在专业课程方面表现稳定，但在理论基础方面需要加强。',
                'development_suggestions': '建议参加学习小组，寻求老师指导，多做练习题。',
                'avg_score': random.randint(60, 95),
                'rank': random.randint(1, 50),
                'trend': random.choice(['稳步提升', '保持稳定', '略有下降']),
                'subject_analysis': '数学：优秀，编程：良好，英语：需要加强',
                'improvement_suggestions': '建议制定详细的学习计划，加强薄弱科目练习，寻求老师和同学的帮助。',
                'strengths': '逻辑思维能力强，学习态度认真，有良好的学习习惯',
                'weaknesses': '时间管理需要改进，基础知识不够扎实，缺乏有效的学习方法',
                'opportunities': '有丰富的学习资源，同学互助氛围好，行业发展前景广阔',
                'threats': '竞争激烈，就业压力增大，技术更新快速',
                'development_strategies': '发挥优势，弥补不足，抓住机遇，规避风险',
                'short_term_goals': '提高时间管理效率，加强基础知识复习，改善学习方法',
                'mid_term_goals': '提升专业课成绩，参加实践活动，积累项目经验',
                'long_term_goals': '全面提升综合能力，为就业做准备，培养终身学习能力',
                'specific_measures': '每天制定学习计划，每周总结反思，定期与老师交流学习情况'
            }

            template = analysis_templates[analysis_type]
            analysis_result = template.format(**result_data)

            # 创建分析记录
            analysis = StudentAnalysis.objects.create(
                student=student,
                analysis_type=analysis_type,
                title=f'{student.name}的{analysis_type}分析',
                status='completed',
                input_data={'student_id': student.student_id, 'generated_at': datetime.now().isoformat()},
                analysis_result=analysis_result,
                ai_confidence=Decimal(str(round(random.uniform(0.75, 0.95), 2))),
                analyzed_at=django.utils.timezone.now(),
                actual_prompt=f'为{student.name}生成{analysis_type}分析'
            )

            created_count += 1
            print(f"[OK] 创建分析：{student.name} - {analysis_type}")

    return created_count

def generate_service_logs():
    """生成AI服务调用日志"""

    students = Student.objects.all()
    request_types = ['analysis', 'suggestion', 'evaluation']
    statuses = ['success', 'failed']

    created_count = 0
    for _ in range(50):  # 生成50条日志
        student = random.choice(students)

        log = AIServiceLog.objects.create(
            request_type=random.choice(request_types),
            request_data={'model': 'deepseek-chat', 'tokens': random.randint(1000, 4000)},
            response_content='模拟的AI响应内容，包含了详细的分析结果和建议。',
            response_time=Decimal(str(round(random.uniform(1.0, 15.0), 3))),
            status=random.choice(statuses),
            error_message=None if random.random() > 0.1 else '模拟的错误信息',
            created_at=django.utils.timezone.now() - timedelta(days=random.randint(0, 30))
        )

        created_count += 1

    return created_count

def generate_student_scores():
    """为学生生成成绩数据"""

    students = Student.objects.all()
    courses = Course.objects.all()

    created_count = 0
    for student in students:
        # 为每个学生随机选择5-10门课程
        student_courses = random.sample(list(courses), random.randint(5, 10))

        for course in student_courses:
            # 检查是否已存在
            try:
                Score.objects.get(student=student, course=course)
                continue
            except Score.DoesNotExist:
                # 生成成绩（根据学生情况调整）
                if student.student_id == '20230015':  # 问题学生李小明
                    score = random.randint(45, 65)  # 低分
                elif student.student_id == '20230016':  # 优秀学生王小华
                    score = random.randint(85, 98)  # 高分
                else:
                    score = random.randint(60, 90)  # 普通成绩

                score_obj = Score.objects.create(
                    student=student,
                    course=course,
                    score=score,
                    date=django.utils.timezone.now() - timedelta(days=random.randint(1, 180))
                )

                created_count += 1

    return created_count

if __name__ == '__main__':
    try:
        print("[INFO] 开始生成AI学情分析假数据...")

        # 生成更多学生
        student_count = generate_more_students()
        print(f"[OK] 生成学生数据：{student_count}个")

        # 生成成绩数据
        score_count = generate_student_scores()
        print(f"[OK] 生成成绩数据：{score_count}条")

        # 生成综合分析
        analysis_count = generate_comprehensive_analyses()
        print(f"[OK] 生成分析数据：{analysis_count}条")

        # 生成服务日志
        log_count = generate_service_logs()
        print(f"[OK] 生成服务日志：{log_count}条")

        print(f"\n[SUCCESS] AI学情分析假数据生成完成！")
        print(f"现在可以访问以下页面查看完整功能：")
        print(f"  - AI仪表板：http://127.0.0.1:8000/ai-dashboard/")
        print(f"  - AI干预面板：http://127.0.0.1:8000/ai-intervention-dashboard/")
        print(f"  - AI演示页面：http://127.0.0.1:8000/ai/demo/")

    except Exception as e:
        print(f"\n[ERROR] 生成数据失败：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)