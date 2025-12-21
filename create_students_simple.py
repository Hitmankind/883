#!/usr/bin/env python
"""
创建优秀学生数据脚本 - 简化版
"""

import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grade_management.settings')
django.setup()

from students.models import Student, Course, Score
from decimal import Decimal

def create_students():
    """创建优秀学生数据"""

    print("开始创建学生数据...")

    # 学生数据
    students_data = [
        {
            'name': '王小明',
            'student_id': '20210001',
            'gender': '男',
            'birth_date': '2003-05-15',
            'major': '计算机科学与技术',
            'college': '信息工程学院',
            'scores': [
                ('MATH001', '高等数学', 95.0),
                ('MATH002', '线性代数', 92.0),
                ('CS001', '数据结构', 96.0),
                ('CS002', '计算机网络', 93.0),
                ('CS003', '操作系统', 91.0),
                ('CS004', '数据库系统', 94.0),
                ('CS005', '软件工程', 95.0),
                ('ENG001', '英语', 88.0)
            ]
        },
        {
            'name': '张丽华',
            'student_id': '20210002',
            'gender': '女',
            'birth_date': '2003-08-22',
            'major': '软件工程',
            'college': '信息工程学院',
            'scores': [
                ('MATH001', '高等数学', 98.0),
                ('MATH002', '线性代数', 97.0),
                ('MATH003', '概率论', 99.0),
                ('CS001', '数据结构', 95.0),
                ('CS002', '计算机网络', 96.0),
                ('CS003', '操作系统', 94.0),
                ('CS004', '数据库系统', 97.0),
                ('CS006', '编译原理', 93.0),
                ('ENG001', '英语', 95.0)
            ]
        },
        {
            'name': '李思源',
            'student_id': '20210003',
            'gender': '男',
            'birth_date': '2003-03-10',
            'major': '人工智能',
            'college': '信息工程学院',
            'scores': [
                ('MATH001', '高等数学', 89.0),
                ('MATH002', '线性代数', 91.0),
                ('CS001', '数据结构', 94.0),
                ('CS002', '计算机网络', 92.0),
                ('CS007', 'Web开发', 96.0),
                ('AI001', '人工智能导论', 93.0),
                ('AI002', '机器学习', 91.0),
                ('ENG001', '英语', 90.0)
            ]
        },
        {
            'name': '陈雨萱',
            'student_id': '20210004',
            'gender': '女',
            'birth_date': '2003-11-28',
            'major': '网络安全',
            'college': '信息工程学院',
            'scores': [
                ('MATH001', '高等数学', 94.0),
                ('MATH002', '线性代数', 93.0),
                ('MATH003', '概率论', 95.0),
                ('CS001', '数据结构', 97.0),
                ('CS002', '计算机网络', 96.0),
                ('SEC001', '信息安全', 98.0),
                ('SEC002', '密码学', 95.0),
                ('SEC003', '网络安全', 96.0),
                ('ENG001', '英语', 93.0)
            ]
        },
        {
            'name': '刘志强',
            'student_id': '20210005',
            'gender': '男',
            'birth_date': '2003-07-05',
            'major': '计算机科学与技术',
            'college': '信息工程学院',
            'scores': [
                ('MATH001', '高等数学', 96.0),
                ('MATH002', '线性代数', 94.0),
                ('CS001', '数据结构', 98.0),
                ('CS002', '计算机网络', 97.0),
                ('CS003', '操作系统', 95.0),
                ('CS009', '计算机组成原理', 96.0),
                ('CS010', '算法设计', 99.0),
                ('CS011', '编程竞赛', 98.0),
                ('ENG001', '英语', 89.0)
            ]
        },
        {
            'name': '赵文静',
            'student_id': '20220001',
            'gender': '女',
            'birth_date': '2004-02-18',
            'major': '软件工程',
            'college': '信息工程学院',
            'scores': [
                ('MATH001', '高等数学', 85.0),
                ('MATH002', '线性代数', 82.0),
                ('CS001', '数据结构', 87.0),
                ('CS002', '计算机网络', 84.0),
                ('CS004', '数据库系统', 86.0),
                ('CS005', '软件工程', 83.0),
                ('ENG001', '英语', 80.0)
            ]
        },
        {
            'name': '周小波',
            'student_id': '20230001',
            'gender': '男',
            'birth_date': '2005-01-30',
            'major': '信息管理',
            'college': '管理学院',
            'scores': [
                ('MATH001', '高等数学', 75.0),
                ('MATH002', '线性代数', 72.0),
                ('CS001', '数据结构', 78.0),
                ('CS002', '计算机网络', 74.0),
                ('CS004', '数据库系统', 76.0),
                ('ENG001', '英语', 70.0)
            ]
        }
    ]

    try:
        for student_data in students_data:
            print(f"\n处理学生: {student_data['name']}")

            # 创建或获取学生
            student, created = Student.objects.get_or_create(
                student_id=student_data['student_id'],
                defaults={
                    'name': student_data['name'],
                    'gender': student_data['gender'],
                    'birth_date': student_data['birth_date'],
                    'major': student_data['major'],
                    'college': student_data['college']
                }
            )

            if created:
                print(f"  [OK] 新建学生: {student.name}")
            else:
                print(f"  [OK] 学生已存在: {student.name}")

            # 为每个课程创建成绩
            scores_count = 0
            for course_id, course_name, score_value in student_data['scores']:
                # 获取或创建课程
                course, course_created = Course.objects.get_or_create(
                    course_id=course_id,
                    defaults={
                        'course_name': course_name,
                        'credits': 3
                    }
                )

                # 创建成绩记录
                score, score_created = Score.objects.get_or_create(
                    student=student,
                    course=course,
                    defaults={'score': Decimal(str(score_value))}
                )

                if score_created:
                    scores_count += 1
                    print(f"    [NEW] 成绩: {course_name} - {score_value}")
                else:
                    print(f"    [EXIST] 成绩: {course_name} - {score.score}")

            print(f"  处理了 {scores_count} 条新成绩记录")

        # 统计信息
        print("\n" + "="*50)
        print("数据创建完成！")
        print(f"学生总数: {Student.objects.count()}")
        print(f"课程总数: {Course.objects.count()}")
        print(f"成绩记录总数: {Score.objects.count()}")

        # 显示学生排名
        print("\n学生平均分排名:")
        students = []
        for student in Student.objects.all():
            scores = Score.objects.filter(student=student)
            if scores:
                avg_score = sum(float(s.score) for s in scores) / len(scores)
                students.append((student.name, avg_score, len(scores)))

        students.sort(key=lambda x: x[1], reverse=True)
        for i, (name, avg, count) in enumerate(students[:10], 1):
            print(f"  {i:2d}. {name:10s} - 平均分: {avg:5.1f} (课程数: {count})")

        print("\n成功！现在可以测试AI分析功能了。")

    except Exception as e:
        print(f"创建数据时出错: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_students()