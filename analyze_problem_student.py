#!/usr/bin/env python
"""
使用 AI 分析系统分析问题学生李小明
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
from ai_analysis.views import prepare_student_data, format_prompt
from ai_analysis.deepseek_client import get_deepseek_client

def analyze_problem_student():
    """分析问题学生李小明"""

    print("[INFO] 开始分析问题学生李小明...")

    # 获取学生
    try:
        student = Student.objects.get(student_id='20230015')
        print(f"[OK] 找到学生：{student.name} ({student.student_id})")
    except Student.DoesNotExist:
        print("[ERROR] 学生李小明不存在，请先运行 create_problem_student.py")
        return

    # 先准备数据
    print("[INFO] 准备分析数据...")
    input_data = prepare_student_data(student, 'comprehensive')

    # 创建综合分析
    print("[INFO] 创建综合分析...")
    analysis = StudentAnalysis.objects.create(
        student=student,
        analysis_type='comprehensive',
        title=f'{student.name}的综合学情分析',
        status='pending',
        prompt_template='',  # 将使用默认模板
        input_data=input_data  # 添加输入数据
    )

    print(f"[OK] 数据准备完成，包含 {len(input_data)} 个字段")

    # 显示数据概要
    print(f"\n[INFO] 数据概要：")
    print(f"  - 学生姓名：{student.name}")
    print(f"  - 专业：{student.major}")
    print(f"  - 课程数量：{input_data.get('course_count', 0)}")
    print(f"  - 平均分：{input_data.get('average_score', 0):.1f}")
    print(f"  - 最高分：{input_data.get('max_score', 0)}")
    print(f"  - 最低分：{input_data.get('min_score', 0)}")

    try:
        # 获取 AI 客户端并进行分析
        print("\n[INFO] 开始 AI 分析...")
        client = get_deepseek_client()

        # 准备提示词
        prompt = format_prompt(analysis)
        print(f"[OK] 提示词准备完成，长度：{len(prompt)} 字符")

        # 保存实际使用的提示词
        analysis.actual_prompt = prompt
        analysis.save()

        # 更新状态为处理中
        analysis.status = 'processing'
        analysis.save()

        print("[INFO] 正在调用 DeepSeek API...")
        print("[INFO] 这可能需要1-2分钟，请耐心等待...")

        # 调用 AI API
        result = client.generate_analysis(
            prompt=prompt,
            student_analysis_id=analysis.id,
            request_type='analysis'
        )

        if result['success']:
            # 验证响应质量
            validation = client.validate_response(result['content'])
            confidence = client.estimate_confidence(
                result['content'],
                len(analysis.input_data) if analysis.input_data else 0
            )

            # 更新分析结果
            analysis.status = 'completed'
            analysis.analysis_result = result['content']
            analysis.ai_confidence = confidence
            analysis.analyzed_at = django.utils.timezone.now()
            analysis.save()

            print(f"\n[SUCCESS] AI 分析完成！")
            print(f"  - 响应时间：{result.get('response_time', 0):.2f} 秒")
            print(f"  - 置信度：{confidence:.2f}")
            print(f"  - 分析结果长度：{len(result['content'])} 字符")

            # 显示分析结果摘要
            print(f"\n[INFO] 分析结果摘要：")
            lines = result['content'].split('\n')
            for line in lines[:20]:  # 显示前20行
                if line.strip():
                    print(f"  {line}")
            if len(lines) > 20:
                print(f"  ... (还有 {len(lines) - 20} 行)")

            print(f"\n[INFO] 完整分析报告已保存到数据库")
            print(f"  分析ID：{analysis.id}")
            print(f"  可通过 http://127.0.0.1:8000/ai/detail/{analysis.id}/ 查看")

        else:
            analysis.status = 'failed'
            analysis.error_message = result.get('error', '未知错误')
            analysis.save()

            print(f"\n[ERROR] AI 分析失败：{analysis.error_message}")

    except Exception as e:
        print(f"\n[ERROR] 分析过程出错：{str(e)}")
        analysis.status = 'failed'
        analysis.error_message = str(e)
        analysis.save()

def create_specific_analysis():
    """为特定分析类型创建分析"""

    # 获取学生
    try:
        student = Student.objects.get(student_id='20230015')
    except Student.DoesNotExist:
        print("[ERROR] 学生不存在")
        return

    analysis_types = [
        ('academic_performance', '学业表现分析'),
        ('strength_weakness', '优势劣势分析'),
        ('improvement_suggestions', '改进建议分析'),
    ]

    for analysis_type, title_suffix in analysis_types:
        print(f"\n[INFO] 创建 {title_suffix}...")

        # 检查是否已存在
        existing = StudentAnalysis.objects.filter(
            student=student,
            analysis_type=analysis_type
        ).first()

        if existing:
            print(f"[INFO] {title_suffix} 已存在，跳过")
            continue

        # 创建分析
        analysis = StudentAnalysis.objects.create(
            student=student,
            analysis_type=analysis_type,
            title=f'{student.name}的{title_suffix}',
            status='pending',
            prompt_template='',
        )

        # 准备数据
        input_data = prepare_student_data(student, analysis_type)
        analysis.input_data = input_data
        analysis.save()

        print(f"[OK] {title_suffix} 创建完成，ID：{analysis.id}")

if __name__ == '__main__':
    try:
        # 先运行综合分析
        analyze_problem_student()

        # 创建其他类型的分析（可选）
        create_specific_analysis()

        print(f"\n[SUCCESS] 问题学生分析完成！")
        print(f"现在可以通过以下链接查看分析结果：")
        print(f"  - AI 分析演示页：http://127.0.0.1:8000/ai/demo/")
        print(f"  - 学生管理：http://127.0.0.1:8000/students/")

    except Exception as e:
        print(f"\n[ERROR] 脚本执行失败：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)