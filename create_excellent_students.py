#!/usr/bin/env python
"""
创建优秀学生数据脚本
生成不同水平的学生，特别是高分的优秀学生
"""

import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grade_management.settings')
django.setup()

from students.models import Student, Course, Score
from django.contrib.auth.models import User

def create_excellent_students():
    """创建优秀学生数据"""

    print("开始创建优秀学生数据...")

    # 优秀学生数据
    excellent_students_data = [
        {
            'name': '王小明',
            'student_id': '20210001',
            'gender': '男',
            'birth_date': '2003-05-15',
            'major': '计算机科学与技术',
            'college': '信息工程学院',
            'scores': [
                ('高等数学', 95.0),
                ('线性代数', 92.0),
                ('概率论', 94.0),
                ('数据结构', 96.0),
                ('计算机网络', 93.0),
                ('操作系统', 91.0),
                ('数据库系统', 94.0),
                ('软件工程', 95.0),
                ('英语', 88.0),
                ('思想政治', 90.0)
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
                ('高等数学', 98.0),
                ('线性代数', 97.0),
                ('概率论', 99.0),
                ('数据结构', 95.0),
                ('计算机网络', 96.0),
                ('操作系统', 94.0),
                ('数据库系统', 97.0),
                ('编译原理', 93.0),
                ('英语', 95.0),
                ('思想政治', 92.0)
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
                ('高等数学', 89.0),
                ('线性代数', 91.0),
                ('数据结构', 94.0),
                ('计算机网络', 92.0),
                ('Web开发', 96.0),
                ('移动应用开发', 95.0),
                ('人工智能导论', 93.0),
                ('机器学习', 91.0),
                ('项目管理', 88.0),
                ('英语', 90.0)
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
                ('高等数学', 94.0),
                ('线性代数', 93.0),
                ('概率论', 95.0),
                ('数据结构', 97.0),
                ('计算机网络', 96.0),
                ('信息安全', 98.0),
                ('密码学', 95.0),
                ('网络安全', 96.0),
                ('数据库系统', 92.0),
                ('英语', 93.0)
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
                ('高等数学', 96.0),
                ('线性代数', 94.0),
                ('数据结构', 98.0),
                ('计算机网络', 97.0),
                ('操作系统', 95.0),
                ('计算机组成原理', 96.0),
                ('算法设计', 99.0),
                ('编程竞赛', 98.0),
                ('英语', 89.0),
                ('思想政治', 91.0)
            ]
        }
    ]

    # 良好水平学生数据
    good_students_data = [
        {
            'name': '赵文静',
            'student_id': '20220001',
            'gender': '女',
            'birth_date': '2004-02-18',
            'major': '软件工程',
            'college': '信息工程学院',
            'scores': [
                ('高等数学', 85.0),
                ('线性代数', 82.0),
                ('数据结构', 87.0),
                ('计算机网络', 84.0),
                ('数据库系统', 86.0),
                ('软件工程', 83.0),
                ('英语', 80.0),
                ('思想政治', 85.0)
            ]
        },
        {
            'name': '孙建国',
            'student_id': '20220002',
            'gender': '男',
            'birth_date': '2004-06-12',
            'major': '计算机科学与技术',
            'college': '信息工程学院',
            'scores': [
                ('高等数学', 88.0),
                ('线性代数', 86.0),
                ('概率论', 84.0),
                ('数据结构', 87.0),
                ('计算机网络', 85.0),
                ('Web开发', 89.0),
                ('英语', 82.0),
                ('思想政治', 86.0)
            ]
        }
    ]

    # 中等水平学生数据
    average_students_data = [
        {
            'name': '周小波',
            'student_id': '20230001',
            'gender': '男',
            'birth_date': '2005-01-30',
            'major': '信息管理',
            'college': '管理学院',
            'scores': [
                ('高等数学', 75.0),
                ('线性代数', 72.0),
                ('数据结构', 78.0),
                ('计算机网络', 74.0),
                ('数据库系统', 76.0),
                ('英语', 70.0),
                ('思想政治', 73.0)
            ]
        },
        {
            'name': '吴佳琪',
            'student_id': '20230002',
            'gender': '女',
            'birth_date': '2005-09-16',
            'major': '电子商务',
            'college': '管理学院',
            'scores': [
                ('高等数学', 78.0),
                ('线性代数', 76.0),
                ('数据结构', 74.0),
                ('计算机网络', 77.0),
                ('软件工程', 75.0),
                ('英语', 72.0),
                ('思想政治', 76.0)
            ]
        }
    ]

    try:
        # 合并所有学生数据
        all_students_data = excellent_students_data + good_students_data + average_students_data

        for student_data in all_students_data:
            print(f"\n创建学生: {student_data['name']}")

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
                print(f"  ✓ 新建学生: {student.name}")
            else:
                print(f"  ✓ 学生已存在: {student.name}")

            # 为每个课程创建成绩
            scores_count = 0
            for course_name, score_value in student_data['scores']:
                # 生成课程代码
                course_code = f'CRSE{Course.objects.count() + 1:03d}'
                # 为常见的课程分配固定代码
                course_code_mapping = {
                    '高等数学': 'MATH001',
                    '线性代数': 'MATH002',
                    '概率论': 'MATH003',
                    '数据结构': 'CS001',
                    '计算机网络': 'CS002',
                    '操作系统': 'CS003',
                    '数据库系统': 'CS004',
                    '软件工程': 'CS005',
                    '编译原理': 'CS006',
                    'Web开发': 'CS007',
                    '移动应用开发': 'CS008',
                    '人工智能导论': 'AI001',
                    '机器学习': 'AI002',
                    '信息安全': 'SEC001',
                    '密码学': 'SEC002',
                    '网络安全': 'SEC003',
                    '计算机组成原理': 'CS009',
                    '算法设计': 'CS010',
                    '编程竞赛': 'CS011',
                    '项目管理': 'MGMT001',
                    '英语': 'ENG001',
                    '思想政治': 'POL001'
                }

                course_code = course_code_mapping.get(course_name, course_code)

                course, _ = Course.objects.get_or_create(
                    course_id=course_code,
                    defaults={
                        'course_name': course_name,
                        'credits': 3  # 默认学分
                    }
                )

                # 创建成绩记录
                score, created = Score.objects.get_or_create(
                    student=student,
                    course=course,
                    defaults={'score': score_value, 'date': '2024-01-15'}
                )

                if created:
                    scores_count += 1
                    print(f"    ✓ 新建成绩: {course_name} - {score_value}")
                else:
                    print(f"    ✓ 成绩已存在: {course_name} - {score.score}")

            print(f"  总共创建/更新了 {scores_count} 条成绩记录")

        # 统计信息
        print("\n" + "="*50)
        print("数据创建完成！统计信息：")
        print(f"  学生总数: {Student.objects.count()}")
        print(f"  课程总数: {Course.objects.count()}")
        print(f"  成绩记录总数: {Score.objects.count()}")

        # 按学生统计平均分
        print("\n学生平均分排名:")
        students_with_avg = []
        for student in Student.objects.all():
            scores = Score.objects.filter(student=student)
            if scores:
                avg_score = sum(s.score for s in scores) / len(scores)
                students_with_avg.append((student.name, avg_score, scores.count()))

        # 按平均分排序
        students_with_avg.sort(key=lambda x: x[1], reverse=True)

        for i, (name, avg, count) in enumerate(students_with_avg, 1):
            print(f"  {i:2d}. {name:8s} - 平均分: {avg:5.1f} (课程数: {count})")

        print("\n✅ 数据创建成功！现在可以测试AI分析功能了。")

    except Exception as e:
        print(f"❌ 创建数据时出错: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_excellent_students()