#!/usr/bin/env python
"""
显示分析结果
"""

import os
import sys
import django

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grade_management.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

django.setup()

from students.models import Student
from ai_analysis.models import StudentAnalysis

def show_analysis_results():
    """显示所有分析结果"""

    print("="*80)
    print("STUDENT AI ANALYSIS RESULTS")
    print("="*80)

    # 显示所有学生
    students = Student.objects.all()
    print(f"\n系统中的学生：")
    for student in students:
        print(f"  - {student.name} ({student.student_id}) - {student.major}")

    # 显示所有分析
    analyses = StudentAnalysis.objects.select_related('student').order_by('-created_at')
    print(f"\nAI 分析记录：")

    if not analyses.exists():
        print("  暂无分析记录")
        return

    for i, analysis in enumerate(analyses, 1):
        print(f"\n{i}. {analysis.title}")
        print(f"   学生：{analysis.student.name} ({analysis.student.student_id})")
        print(f"   分析类型：{analysis.get_analysis_type_display()}")
        print(f"   状态：{analysis.get_status_display()}")
        print(f"   创建时间：{analysis.created_at.strftime('%Y-%m-%d %H:%M:%S')}")

        if analysis.status == 'completed':
            print(f"   分析引擎：{analysis.analyzed_by}")
            if analysis.ai_confidence:
                print(f"   AI 置信度：{analysis.ai_confidence:.2f}")
            if analysis.analyzed_at:
                print(f"   完成时间：{analysis.analyzed_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   结果长度：{len(analysis.analysis_result or '')} 字符")

            # 显示结果摘要
            if analysis.analysis_result:
                lines = analysis.analysis_result.split('\n')
                print(f"   结果摘要：")
                for line in lines[:5]:  # 显示前5行
                    if line.strip():
                        print(f"     {line.encode('gbk', 'ignore').decode('gbk')}")
                if len(lines) > 5:
                    print(f"     ... (还有 {len(lines) - 5} 行)")
        else:
            print(f"   错误信息：{analysis.error_message or '未知错误'}")

def show_problem_student_analysis():
    """显示问题学生的详细分析"""

    try:
        student = Student.objects.get(student_id='20230015')
        analysis = StudentAnalysis.objects.filter(student=student).first()

        print(f"\n" + "="*80)
        print(f"问题学生详细分析：{student.name}")
        print(f"="*80)

        if not analysis:
            print("未找到分析记录")
            return

        print(f"\n基本信息：")
        print(f"  姓名：{student.name}")
        print(f"  学号：{student.student_id}")
        print(f"  专业：{student.major}")
        print(f"  学院：{student.college}")

        print(f"\n分析概要：")
        print(f"  标题：{analysis.title}")
        print(f"  类型：{analysis.get_analysis_type_display()}")
        print(f"  状态：{analysis.get_status_display()}")
        print(f"  置信度：{analysis.ai_confidence:.2f}")

        if analysis.analysis_result:
            print(f"\n完整分析报告：")
            print("-" * 80)
            print(analysis.analysis_result.encode('gbk', 'ignore').decode('gbk'))
            print("-" * 80)

        print(f"\n访问链接：")
        print(f"  - 主页：http://127.0.0.1:8000/")
        print(f"  - AI 演示：http://127.0.0.1:8000/ai/demo/")
        print(f"  - 学生管理：http://127.0.0.1:8000/students/")

    except Student.DoesNotExist:
        print("问题学生不存在")
    except Exception as e:
        print(f"显示分析结果出错：{e}")

if __name__ == '__main__':
    try:
        show_analysis_results()
        show_problem_student_analysis()

        print(f"\n[SUCCESS] 分析结果显示完成！")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()