import os
import csv
from django.conf import settings
from .models import Student, Course, Score, Enrollment
from datetime import datetime

class DataFileManager:
    """数据文件管理器"""
    
    def __init__(self):
        self.data_dir = os.path.join(settings.BASE_DIR, 'data')
        os.makedirs(self.data_dir, exist_ok=True)
    
    def load_students_from_file(self):
        """从student.dat文件加载学生数据"""
        file_path = os.path.join(self.data_dir, 'student.dat')
        students = []
        
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        parts = line.strip().split('\t')
                        if len(parts) >= 6:
                            students.append({
                                'student_id': parts[0],
                                'name': parts[1],
                                'gender': parts[2],
                                'birth_date': parts[3],
                                'major': parts[4],
                                'college': parts[5]
                            })
        return students
    
    def load_courses_from_file(self):
        """从course.dat文件加载课程数据"""
        file_path = os.path.join(self.data_dir, 'course.dat')
        courses = []
        
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        parts = line.strip().split('\t')
                        if len(parts) >= 3:
                            courses.append({
                                'course_id': parts[0],
                                'course_name': parts[1],
                                'credits': int(parts[2])
                            })
        return courses
    
    def load_scores_from_file(self):
        """从score.dat文件加载成绩数据"""
        file_path = os.path.join(self.data_dir, 'score.dat')
        scores = []
        
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        parts = line.strip().split('\t')
                        if len(parts) >= 6:
                            scores.append({
                                'student_id': parts[0],
                                'student_name': parts[1],
                                'course_id': parts[2],
                                'course_name': parts[3],
                                'score': float(parts[4]),
                                'date': parts[5]
                            })
        return scores
    
    def delete_student_from_file(self, student_id):
        """从student.dat文件删除学生数据"""
        file_path = os.path.join(self.data_dir, 'student.dat')
        if not os.path.exists(file_path):
            return
        
        students = []
        with open(file_path, 'r', encoding='utf-8') as f:
            students = [line.strip().split('\t') for line in f if line.strip()]
        
        # 过滤掉要删除的学生
        students = [s for s in students if s[0] != student_id]
        
        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            for student in students:
                f.write('\t'.join(student) + '\n')
    
    def delete_course_from_file(self, course_id):
        """从course.dat文件删除课程数据"""
        file_path = os.path.join(self.data_dir, 'course.dat')
        if not os.path.exists(file_path):
            return
        
        courses = []
        with open(file_path, 'r', encoding='utf-8') as f:
            courses = [line.strip().split('\t') for line in f if line.strip()]
        
        # 过滤掉要删除的课程
        courses = [c for c in courses if c[0] != course_id]
        
        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            for course in courses:
                f.write('\t'.join(course) + '\n')
    
    def delete_score_from_file(self, student_id, course_id):
        """从score.dat文件删除成绩数据"""
        file_path = os.path.join(self.data_dir, 'score.dat')
        if not os.path.exists(file_path):
            return
        
        scores = []
        with open(file_path, 'r', encoding='utf-8') as f:
            scores = [line.strip().split('\t') for line in f if line.strip()]
        
        # 过滤掉要删除的成绩
        scores = [s for s in scores if not (len(s) >= 3 and s[0] == student_id and s[2] == course_id)]
        
        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            for score in scores:
                f.write('\t'.join(score) + '\n')
    
    def sync_database_to_files(self):
        """将数据库数据同步到文件"""
        # 同步学生数据
        for student in Student.objects.all():
            student.save_to_file()
        
        # 同步课程数据
        for course in Course.objects.all():
            course.save_to_file()
        
        # 同步成绩数据
        for score in Score.objects.all():
            score.save_to_file()
    
    def sync_files_to_database(self):
        """将文件数据同步到数据库"""
        # 同步学生数据
        students_data = self.load_students_from_file()
        for student_data in students_data:
            student, created = Student.objects.get_or_create(
                student_id=student_data['student_id'],
                defaults={
                    'name': student_data['name'],
                    'gender': student_data['gender'],
                    'birth_date': datetime.strptime(student_data['birth_date'], '%Y-%m-%d').date(),
                    'major': student_data['major'],
                    'college': student_data['college']
                }
            )
            if not created:
                # 更新现有记录
                student.name = student_data['name']
                student.gender = student_data['gender']
                student.birth_date = datetime.strptime(student_data['birth_date'], '%Y-%m-%d').date()
                student.major = student_data['major']
                student.college = student_data['college']
                student.save()
        
        # 同步课程数据
        courses_data = self.load_courses_from_file()
        for course_data in courses_data:
            course, created = Course.objects.get_or_create(
                course_id=course_data['course_id'],
                defaults={
                    'course_name': course_data['course_name'],
                    'credits': course_data['credits']
                }
            )
            if not created:
                # 更新现有记录
                course.course_name = course_data['course_name']
                course.credits = course_data['credits']
                course.save()
        
        # 同步成绩数据
        scores_data = self.load_scores_from_file()
        for score_data in scores_data:
            try:
                student = Student.objects.get(student_id=score_data['student_id'])
                course = Course.objects.get(course_id=score_data['course_id'])
                
                score, created = Score.objects.get_or_create(
                    student=student,
                    course=course,
                    defaults={
                        'score': score_data['score'],
                        'date': datetime.strptime(score_data['date'], '%Y-%m-%d').date()
                    }
                )
                if not created:
                    # 更新现有记录
                    score.score = score_data['score']
                    score.date = datetime.strptime(score_data['date'], '%Y-%m-%d').date()
                    score.save()
            except (Student.DoesNotExist, Course.DoesNotExist):
                # 如果学生或课程不存在，跳过这条成绩记录
                continue


def get_grade_level(score):
    """根据分数获取等级"""
    if score >= 90:
        return '优秀'
    elif score >= 80:
        return '良好'
    elif score >= 70:
        return '中等'
    elif score >= 60:
        return '及格'
    else:
        return '不及格'


def calculate_grade_statistics(scores):
    """计算成绩统计信息"""
    if not scores:
        return {
            '优秀': 0, '良好': 0, '中等': 0, '及格': 0, '不及格': 0
        }
    
    stats = {'优秀': 0, '良好': 0, '中等': 0, '及格': 0, '不及格': 0}
    
    for score in scores:
        grade_level = get_grade_level(float(score))
        stats[grade_level] += 1
    
    return stats