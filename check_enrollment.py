#!/usr/bin/env python
import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grade_management.settings')
django.setup()

from students.models import Enrollment, Student, Course

print('选课记录总数:', Enrollment.objects.count())
print('学生总数:', Student.objects.count())
print('课程总数:', Course.objects.count())
print('\n前5条选课记录:')
for e in Enrollment.objects.all()[:5]:
    print(f'  {e.student.student_id} - {e.student.name} 选修 {e.course.course_id} - {e.course.course_name}')

print('\n检查特定学生的选课记录:')
students = Student.objects.all()[:3]
for student in students:
    enrollments = Enrollment.objects.filter(student=student)
    print(f'{student.student_id} - {student.name}: {enrollments.count()}门课程')
    for enrollment in enrollments:
        print(f'  - {enrollment.course.course_id} {enrollment.course.course_name}')