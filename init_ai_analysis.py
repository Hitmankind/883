#!/usr/bin/env python
"""
初始化 AI 分析提示词模板
"""

import os
import sys
import django

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grade_management.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

django.setup()

from ai_analysis.models import PromptTemplate

def init_prompt_templates():
    """初始化提示词模板"""

    templates = [
        {
            'name': '学业表现分析模板',
            'analysis_type': 'academic_performance',
            'template': '''你是一位专业的教育学分析师和AI学习顾问。现在需要你对学生的学业表现进行深入分析。

## 学生基本信息
- 姓名：{student_name}
- 学号：{student_id}
- 性别：{gender}
- 专业：{major}
- 学院：{college}

## 学业数据
{academic_data}

## 分析要求
请基于以上数据，进行全面的学业表现分析，包括：

### 1. 学业总体评估
- 整体学业水平评价
- 与同专业学生的对比分析
- 学业发展趋势

### 2. 学科能力分析
- 各学科能力等级评估（优秀/良好/中等/需改进）
- 强势学科和弱势学科识别
- 学科平衡性分析

### 3. 学习特征识别
- 学习类型：理论学习型/实践应用型/综合型
- 学习稳定性：持续稳定型/波动型/进步型
- 学习难度适应性

### 4. 关键指标分析
- 平均分、标准差等统计指标
- 及格率、优秀率等关键比率
- 学习进步/退步趋势

请提供详细的分析报告和建议。''',
            'variables': ['student_name', 'student_id', 'gender', 'major', 'college', 'academic_data']
        },
        {
            'name': '学习进度分析模板',
            'analysis_type': 'learning_progress',
            'template': '''作为一位教育心理学专家，请对学生的学习进度进行深度分析。

## 学生档案
- 学生：{student_name} ({student_id})
- 专业：{major} - {college}
- 分析时间段：{time_period}

## 学习进度数据
{progress_data}

## 课程完成情况
{course_completion_data}

请分析学生的学习节奏、知识掌握程度、学习发展趋势和潜在问题。''',
            'variables': ['student_name', 'student_id', 'major', 'time_period', 'progress_data', 'course_completion_data']
        },
        {
            'name': '优势劣势分析模板',
            'analysis_type': 'strength_weakness',
            'template': '''你是一位专业的教育评估专家，现在需要对学生进行全面的优势劣势分析。

## 学生基本信息
姓名：{student_name}
学号：{student_id}
专业：{major}
性别：{gender}

## 多维度数据
### 学术表现数据
{academic_data}

### 课程成绩详情
{course_details}

### 学习行为数据
{learning_behavior_data}

请使用 SWOT 分析框架，全面分析学生的优势、劣势、机会和挑战。''',
            'variables': ['student_name', 'student_id', 'major', 'gender', 'academic_data', 'course_details', 'learning_behavior_data']
        },
        {
            'name': '改进建议模板',
            'analysis_type': 'improvement_suggestions',
            'template': '''作为一位经验丰富的教育顾问，请为学生提供个性化、可操作的改进建议。

## 学生画像
- 姓名：{student_name}
- 学号：{student_id}
- 专业：{major}
- 当前学业状况：{academic_status}

## 分析基础数据
### 当前学业表现
{current_performance}

### 历史学习记录
{learning_history}

### 学习行为模式
{learning_patterns}

请提供详细的学业提升策略、能力发展计划、学习环境优化和心理支持建议。''',
            'variables': ['student_name', 'student_id', 'major', 'academic_status', 'current_performance', 'learning_history', 'learning_patterns']
        },
        {
            'name': '综合分析模板',
            'analysis_type': 'comprehensive',
            'template': '''作为一位资深的教育分析师和AI学习顾问，请对学生进行全面的360度学情分析。

## 学生完整档案
### 基本信息模块
- **姓名**：{student_name}
- **学号**：{student_id}
- **性别**：{gender}
- **年龄**：{age}
- **专业**：{major}
- **学院**：{college}

### 学业表现模块
{academic_performance_data}

### 学习行为模块
{learning_behavior_data}

### 课程修读模块
{course_enrollment_data}

### 成绩趋势模块
{grade_trend_data}

请提供包括学术维度、认知维度、行为维度、情感维度和发展维度的综合分析报告。''',
            'variables': ['student_name', 'student_id', 'gender', 'age', 'major', 'college', 'academic_performance_data', 'learning_behavior_data', 'course_enrollment_data', 'grade_trend_data']
        }
    ]

    created_count = 0
    for template_data in templates:
        template, created = PromptTemplate.objects.get_or_create(
            name=template_data['name'],
            analysis_type=template_data['analysis_type'],
            defaults={
                'template': template_data['template'],
                'variables': template_data['variables'],
                'is_active': True
            }
        )
        if created:
            created_count += 1
            print(f"[OK] 已创建模板: {template_data['name']}")
        else:
            print(f"[INFO] 模板已存在: {template_data['name']}")

    print(f"\n初始化完成，共创建 {created_count} 个新模板")
    print(f"当前系统中共有 {PromptTemplate.objects.count()} 个提示词模板")

if __name__ == '__main__':
    try:
        init_prompt_templates()
        print("\n[SUCCESS] AI 分析提示词模板初始化成功！")
    except Exception as e:
        print(f"\n[ERROR] 初始化失败: {e}")
        sys.exit(1)