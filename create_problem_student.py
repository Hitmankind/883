#!/usr/bin/env python
"""
创建问题学生案例并填入数据库
用于测试 AI 学情分析系统
"""

import os
import sys
import django
from datetime import date, timedelta

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grade_management.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

django.setup()

from students.models import Student, Course, Score, Enrollment

def create_problem_student():
    """创建一个典型的问题学生案例"""

    print("[INFO] 开始创建问题学生案例...")

    # 1. 创建问题学生 - 李小明
    try:
        student = Student.objects.get(student_id='20230015')
        print(f"[INFO] 学生 {student.name} 已存在，跳过创建")
    except Student.DoesNotExist:
        student = Student.objects.create(
            student_id='20230015',
            name='李小明',
            gender='男',
            birth_date=date(2004, 8, 15),  # 19岁
            major='计算机科学与技术',
            college='信息工程学院'
        )
        print(f"[OK] 创建问题学生：{student.name} ({student.student_id})")

    # 2. 创建相关课程
    courses_data = [
        # 必修课
        {'course_id': 'CS101', 'name': '高等数学', 'credits': 4, 'type': 'ZYBX'},
        {'course_id': 'CS102', 'name': '线性代数', 'credits': 3, 'type': 'ZYBX'},
        {'course_id': 'CS103', 'name': '大学物理', 'credits': 4, 'type': 'ZYBX'},
        {'course_id': 'CS201', 'name': '数据结构', 'credits': 4, 'type': 'ZYBX'},
        {'course_id': 'CS202', 'name': '算法设计与分析', 'credits': 3, 'type': 'ZYBX'},
        {'course_id': 'CS203', 'name': '计算机网络', 'credits': 3, 'type': 'ZYBX'},
        {'course_id': 'CS204', 'name': '操作系统', 'credits': 4, 'type': 'ZYBX'},
        {'course_id': 'CS205', 'name': '数据库原理', 'credits': 3, 'type': 'ZYBX'},

        # 选修课
        {'course_id': 'CS301', 'name': '人工智能导论', 'credits': 2, 'type': 'ZYXX'},
        {'course_id': 'CS302', 'name': '软件工程', 'credits': 3, 'type': 'ZYXX'},
        {'course_id': 'CS303', 'name': '编译原理', 'credits': 3, 'type': 'ZYXX'},
        {'course_id': 'CS304', 'name': '计算机图形学', 'credits': 2, 'type': 'ZYXX'},

        # 基础课
        {'course_id': 'ENG101', 'name': '大学英语', 'credits': 2, 'type': 'JCKC'},
        {'course_id': 'PE101', 'name': '体育', 'credits': 1, 'type': 'JCKC'},
    ]

    created_courses = []
    for course_data in courses_data:
        try:
            course = Course.objects.get(course_id=course_data['course_id'])
            print(f"[INFO] 课程 {course.course_name} 已存在")
        except Course.DoesNotExist:
            course = Course.objects.create(
                course_id=course_data['course_id'],
                course_name=course_data['name'],
                credits=course_data['credits']
            )
            print(f"[OK] 创建课程：{course.course_name}")
        created_courses.append(course)

    # 3. 创建有问题的成绩数据（体现学习困难）

    # 第一学期成绩 - 基础课还行，但专业课开始吃力
    first_semester_scores = [
        {'course': 'CS101', 'score': 65.0, 'date': date(2023, 10, 15)},  # 高等数学刚及格
        {'course': 'CS102', 'score': 58.0, 'date': date(2023, 11, 20)},  # 线性代数不及格
        {'course': 'ENG101', 'score': 72.0, 'date': date(2023, 12, 10)},  # 英语还行
        {'course': 'PE101', 'score': 85.0, 'date': date(2023, 12, 15)},  # 体育不错
    ]

    # 第二学期成绩 - 专业课继续下滑
    second_semester_scores = [
        {'course': 'CS103', 'score': 52.0, 'date': date(2024, 3, 10)},   # 大物不及格
        {'course': 'CS201', 'score': 61.0, 'date': date(2024, 4, 15)},   # 数据结构勉强及格
        {'course': 'CS301', 'score': 45.0, 'date': date(2024, 5, 20)},   # AI导论不及格
    ]

    # 第三学期成绩 - 持续低迷，出现多门挂科
    third_semester_scores = [
        {'course': 'CS202', 'score': 55.0, 'date': date(2024, 10, 5)},   # 算法不及格
        {'course': 'CS203', 'score': 59.0, 'date': date(2024, 11, 10)},  # 计网勉强及格
        {'course': 'CS204', 'score': 48.0, 'date': date(2024, 12, 5)},   # 操作系统不及格
        {'course': 'CS302', 'score': 67.0, 'date': date(2024, 12, 15)},  # 软工还行
    ]

    # 第四学期成绩 - 最新成绩，显示持续困难
    fourth_semester_scores = [
        {'course': 'CS205', 'score': 53.0, 'date': date(2025, 3, 8)},    # 数据库不及格
        {'course': 'CS303', 'score': 50.0, 'date': date(2025, 4, 12)},   # 编译原理不及格
        {'course': 'CS304', 'score': 62.0, 'date': date(2025, 5, 10)},   # 图形学勉强及格
    ]

    # 合并所有成绩
    all_scores = (first_semester_scores + second_semester_scores +
                 third_semester_scores + fourth_semester_scores)

    # 创建成绩记录
    created_scores = []
    for score_data in all_scores:
        course = Course.objects.get(course_id=score_data['course'])

        # 检查是否已存在
        try:
            existing_score = Score.objects.get(student=student, course=course)
            print(f"[INFO] 成绩记录已存在：{course.course_name} - {existing_score.score}")
        except Score.DoesNotExist:
            score = Score.objects.create(
                student=student,
                course=course,
                score=score_data['score'],
                date=score_data['date']
            )
            created_scores.append(score)
            print(f"[OK] 创建成绩：{course.course_name} - {score.score}分")

    # 4. 创建选课记录
    for course in created_courses:
        try:
            Enrollment.objects.get(student=student, course=course)
        except Enrollment.DoesNotExist:
            Enrollment.objects.create(
                student=student,
                course=course,
                enrollment_date=date(2023, 9, 1)
            )

    # 5. 统计和展示问题
    print("\n" + "="*50)
    print("李小明同学学习情况统计")
    print("="*50)

    total_courses = len(all_scores)
    passed_courses = len([s for s in all_scores if s['score'] >= 60])
    failed_courses = total_courses - passed_courses

    avg_score = sum(s['score'] for s in all_scores) / total_courses
    core_failed = len([s for s in all_scores if s['score'] < 60 and s['course'].startswith('CS')])

    print(f"学生：{student.name} ({student.student_id})")
    print(f"专业：{student.major} - {student.college}")
    print(f"总课程数：{total_courses}")
    print(f"及格课程：{passed_courses}")
    print(f"挂科课程：{failed_courses}")
    print(f"平均分：{avg_score:.1f}")
    print(f"核心专业课挂科：{core_failed}")

    print(f"\n主要问题识别：")
    if failed_courses > 3:
        print(f"   - 挂科门数过多（{failed_courses}门）")
    if avg_score < 65:
        print(f"   - 整体成绩偏低（平均分{avg_score:.1f}）")
    if core_failed > 2:
        print(f"   - 专业课基础薄弱（{core_failed}门专业课挂科）")

    # 显示具体挂科课程
    failed_list = [f"{s['course']}({s['score']}分)" for s in all_scores if s['score'] < 60]
    if failed_list:
        print(f"   - 挂科课程：{', '.join(failed_list)}")

    print(f"\n问题学生案例创建完成！")
    print(f"   学生ID：{student.student_id}")
    print(f"   可用于AI分析测试")

    return student

def create_comparison_student():
    """创建一个对比学生案例（优秀学生）"""

    print("\n[INFO] 创建对比学生案例（优秀学生）...")

    try:
        student = Student.objects.get(student_id='20230016')
        print(f"[INFO] 对比学生 {student.name} 已存在，跳过创建")
        return student
    except Student.DoesNotExist:
        student = Student.objects.create(
            student_id='20230016',
            name='王小华',
            gender='女',
            birth_date=date(2004, 5, 20),  # 19岁
            major='计算机科学与技术',
            college='信息工程学院'
        )
        print(f"[OK] 创建对比学生：{student.name} ({student.student_id})")

    # 为对比学生创建优秀成绩
    excellent_scores = [
        {'course': 'CS101', 'score': 92.0, 'date': date(2023, 10, 15)},
        {'course': 'CS102', 'score': 88.0, 'date': date(2023, 11, 20)},
        {'course': 'CS103', 'score': 95.0, 'date': date(2024, 3, 10)},
        {'course': 'CS201', 'score': 90.0, 'date': date(2024, 4, 15)},
        {'course': 'CS202', 'score': 93.0, 'date': date(2024, 10, 5)},
        {'course': 'CS203', 'score': 91.0, 'date': date(2024, 11, 10)},
        {'course': 'CS204', 'score': 89.0, 'date': date(2024, 12, 5)},
        {'course': 'CS205', 'score': 94.0, 'date': date(2025, 3, 8)},
        {'course': 'ENG101', 'score': 85.0, 'date': date(2023, 12, 10)},
        {'course': 'PE101', 'score': 90.0, 'date': date(2023, 12, 15)},
    ]

    for score_data in excellent_scores:
        course = Course.objects.get(course_id=score_data['course'])
        try:
            existing_score = Score.objects.get(student=student, course=course)
            print(f"[INFO] 成绩记录已存在：{course.course_name}")
        except Score.DoesNotExist:
            score = Score.objects.create(
                student=student,
                course=course,
                score=score_data['score'],
                date=score_data['date']
            )
            print(f"[OK] 创建优秀成绩：{course.course_name} - {score.score}分")

    print(f"✅ 对比学生创建完成！")
    return student

if __name__ == '__main__':
    try:
        problem_student = create_problem_student()
        excellent_student = create_comparison_student()

        print(f"\n[SUCCESS] 测试案例创建完成！")
        print(f"[INFO] 问题学生：{problem_student.name} (ID: {problem_student.student_id})")
        print(f"[INFO] 优秀学生：{excellent_student.name} (ID: {excellent_student.student_id})")
        print(f"\n现在可以使用这些学生数据进行 AI 学情分析测试！")

    except Exception as e:
        print(f"\n[ERROR] 创建失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)