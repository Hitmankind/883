#!/usr/bin/env python
"""
测试脚本：验证AI分析功能的个性化
"""

import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grade_management.settings')
django.setup()

from ai_analysis.agent_views import generate_local_analysis
from ai_analysis.utils import collect_student_data
from django.contrib.auth.models import User
from students.models import Student

def test_ai_analysis():
    """测试AI分析是否为学生生成个性化报告"""

    print("开始测试AI分析功能...\n")

    # 获取测试学生
    try:
        # 获取所有学生
        students = Student.objects.all()[:3]  # 测试前3个学生

        if not students:
            print("❌ 没有找到学生数据")
            return

        print(f"✅ 找到 {len(students)} 个学生用于测试\n")

        analyses = []

        for i, student in enumerate(students, 1):
            print(f"📊 测试学生 {i}: {student.name}")

            # 收集学生数据
            student_data = collect_student_data(student)

            # 生成AI分析
            analysis_result = generate_local_analysis(student_data, student)

            # 存储分析结果用于比较
            analyses.append({
                'student': student.name,
                'content': analysis_result['content'],
                'confidence': analysis_result['confidence'],
                'avg_score': student_data.get('statistics', {}).get('average_score', 0),
                'total_scores': student_data.get('statistics', {}).get('total_scores', 0),
                'courses': [c['course_name'] for c in student_data.get('courses', [])]
            })

            print(f"   - 平均分: {analyses[-1]['avg_score']:.1f}")
            print(f"   - 课程数: {len(analyses[-1]['courses'])}")
            print(f"   - 置信度: {analyses[-1]['confidence']:.2f}")
            print()

        # 比较分析报告
        print("🔍 比较分析报告的个性化程度...\n")

        # 检查是否有重复的分析内容
        unique_contents = set()
        for analysis in analyses:
            # 提取关键内容进行比较（移除学生名字）
            content_without_name = analysis['content'].replace(analysis['student'], 'STUDENT_NAME')
            unique_contents.add(content_without_name)

        print(f"📈 结果统计:")
        print(f"   - 测试学生数: {len(students)}")
        print(f"   - 不同分析报告数: {len(unique_contents)}")
        print(f"   - 个性化程度: {(len(unique_contents) / len(students)) * 100:.1f}%")

        if len(unique_contents) == len(students):
            print("✅ 成功！每个学生都获得了不同的分析报告")
        else:
            print("⚠️  部分分析报告仍然相似，需要进一步优化")

        # 详细展示差异
        print("\n📋 详细分析对比:")
        for i, analysis in enumerate(analyses, 1):
            print(f"\n学生 {i}: {analysis['student']} (平均分: {analysis['avg_score']:.1f})")

            # 提取关键部分进行展示
            lines = analysis['content'].split('\n')

            # 找到Academic Standing
            for line in lines:
                if "Academic Standing" in line:
                    print(f"   学术表现: {line.split(':')[-1].strip()}")
                    break

            # 找到Strengths部分的第一点
            in_strengths = False
            for line in lines:
                if "Personalized Strengths" in line:
                    in_strengths = True
                    continue
                if in_strengths and line.strip().startswith('-'):
                    print(f"   优势分析: {line.strip()}")
                    break

            # 找到课程表现分析
            for line in lines:
                if "⭐" in line or "⚠️" in line:
                    print(f"   课程亮点: {line.strip()}")
                    break

        print("\n🎯 测试完成！")

    except Exception as e:
        print(f"❌ 测试过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ai_analysis()