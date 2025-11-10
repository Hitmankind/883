#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
初始化用户脚本
用于创建测试用的教师和学生用户
"""

import os
import django
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 初始化Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grade_management.settings')
django.setup()

from students.models import CustomUser, Student
from django.contrib.auth.hashers import make_password

def create_test_users():
    """创建测试用户"""
    print("开始创建测试用户...")
    
    # 创建教师用户
    teacher_data = [
        {'username': 'admin', 'email': 'admin@example.com', 'role': 'teacher', 'password': 'admin123'},
        {'username': 'teacher1', 'email': 'teacher1@example.com', 'role': 'teacher', 'password': 'teacher123'},
    ]
    
    for data in teacher_data:
        try:
            user, created = CustomUser.objects.get_or_create(
                username=data['username'],
                defaults={
                    'email': data['email'],
                    'role': data['role'],
                    'password': make_password(data['password']),
                    'is_staff': True,
                    'is_active': True
                }
            )
            if created:
                print(f"✓ 创建教师用户: {data['username']}")
            else:
                print(f"⚠️  教师用户已存在: {data['username']}")
        except Exception as e:
            print(f"✗ 创建教师用户失败 {data['username']}: {str(e)}")
    
    # 创建学生用户（关联已有的学生数据）
    try:
        # 尝试获取一些学生数据
        students = Student.objects.all()[:5]
        for i, student in enumerate(students):
            try:
                username = student.student_id  # 使用学号作为用户名
                user, created = CustomUser.objects.get_or_create(
                    username=username,
                    defaults={
                        'email': f"{username}@example.com",
                        'role': 'student',
                        'password': make_password('student123'),  # 默认密码
                        'is_active': True,  # 确保用户是活跃的
                        'student': student
                    }
                )
                if created:
                    print(f"✓ 创建学生用户: {username} ({student.name})")
                else:
                    print(f"⚠️  学生用户已存在: {username}")
            except Exception as e:
                print(f"✗ 创建学生用户失败 {student.student_id}: {str(e)}")
    
        # 如果没有学生数据，创建默认学生
        if not students.exists():
            print("⚠️  未找到学生数据，创建默认学生用户...")
            default_student = Student.objects.create(
                student_id="20240001",
                name="默认学生",
                gender="男",
                birth_date="2002-01-01",
                major="计算机科学与技术",
                college="信息学院"
            )
            user, created = CustomUser.objects.get_or_create(
                username="20240001",
                defaults={
                    'email': "20240001@example.com",
                    'role': 'student',
                    'password': make_password('student123'),
                    'is_active': True,  # 确保用户是活跃的
                    'student': default_student
                }
            )
            print(f"✓ 创建默认学生用户: 20240001 (默认学生)")
            
    except Exception as e:
        print(f"✗ 学生用户创建过程出错: {str(e)}")
    
    print("\n测试用户创建完成！")
    print("\n教师账号:")
    print("  用户名: admin, 密码: admin123")
    print("  用户名: teacher1, 密码: teacher123")
    print("\n学生账号:")
    print("  用户名: [学号], 密码: student123")
    print("  (如果没有学生数据，默认账号: 20240001, 密码: student123)")

if __name__ == "__main__":
    print("========== 学生成绩管理系统 - 用户初始化脚本 ==========\n")
    create_test_users()
    print("\n==================================================\n")