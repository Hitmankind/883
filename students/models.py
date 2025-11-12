from django.db import models
from django.core.validators import RegexValidator
from decimal import Decimal
import os
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class Student(models.Model):
    """学生数据模型"""
    GENDER_CHOICES = [
        ('男', '男'),
        ('女', '女'),
        ('M', 'M'),
        ('F', 'F'),
    ]
    
    student_id = models.CharField(
        max_length=8, 
        primary_key=True,
        validators=[RegexValidator(r'^\d{8}$', '学号必须是8位数字')],
        verbose_name='学号'
    )
    name = models.CharField(max_length=20, verbose_name='姓名')
    gender = models.CharField(max_length=4, choices=GENDER_CHOICES, verbose_name='性别')
    birth_date = models.DateField(verbose_name='出生日期')
    major = models.CharField(max_length=20, verbose_name='专业')
    college = models.CharField(max_length=20, verbose_name='学院')
    
    class Meta:
        verbose_name = '学生'
        verbose_name_plural = '学生'
        
    def __str__(self):
        return f"{self.student_id} {self.name}"
    
    def save_to_file(self):
        """保存到student.dat文件"""
        file_path = os.path.join(settings.BASE_DIR, 'data', 'student.dat')
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # 读取现有数据
        students = []
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        parts = line.split('\t')
                        if len(parts) >= 6:
                            students.append(parts)
        
        # 更新或添加当前学生数据
        current_data = [
            self.student_id, self.name, self.gender, 
            str(self.birth_date), self.major, self.college
        ]
        
        # 查找是否已存在
        found = False
        for i, student in enumerate(students):
            if student[0] == self.student_id:
                students[i] = current_data
                found = True
                break
        
        if not found:
            students.append(current_data)
        
        # 写入文件
        with open(file_path, 'w', encoding='utf-8') as f:
            for student in students:
                f.write('\t'.join(student) + '\n')
    
    @classmethod
    def load_from_file(cls):
        """从student.dat文件加载数据到数据库"""
        file_path = os.path.join(settings.BASE_DIR, 'data', 'student.dat')
        if not os.path.exists(file_path):
            return 0
        
        count = 0
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    parts = line.split('\t')
                    if len(parts) >= 6:
                        student_id, name, gender, birth_date, major, college = parts[:6]
                        try:
                            # 使用get_or_create避免重复创建
                            student, created = cls.objects.get_or_create(
                                student_id=student_id,
                                defaults={
                                    'name': name,
                                    'gender': gender,
                                    'birth_date': birth_date,
                                    'major': major,
                                    'college': college
                                }
                            )
                            if created:
                                count += 1
                        except Exception as e:
                            print(f"导入学生数据失败: {student_id} - {e}")
        return count


class Course(models.Model):
    """课程数据模型"""
    COURSE_TYPE_CHOICES = [
        ('JCKC', '基础课程'),
        ('ZYBX', '专业必修'),
        ('ZYXX', '专业选修'),
        ('BYSJ', '毕业设计'),
    ]
    
    course_id = models.CharField(
        max_length=12, 
        primary_key=True,
        validators=[RegexValidator(r'^[A-Z]{3,4}\d{3,4}$', '课程号格式不正确')],
        verbose_name='课程号'
    )
    course_name = models.CharField(max_length=100, verbose_name='课程名称')
    credits = models.IntegerField(verbose_name='学分')
    
    class Meta:
        verbose_name = '课程'
        verbose_name_plural = '课程'
        
    def __str__(self):
        return f"{self.course_id} {self.course_name}"
    
    def save_to_file(self):
        """保存到course.dat文件"""
        file_path = os.path.join(settings.BASE_DIR, 'data', 'course.dat')
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # 读取现有数据
        courses = []
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                courses = [line.strip().split('\t') for line in f if line.strip()]
        
        # 更新或添加当前课程数据
        course_data = [self.course_id, self.course_name, str(self.credits)]
        
        # 查找是否已存在
        found = False
        for i, course in enumerate(courses):
            if course[0] == self.course_id:
                courses[i] = course_data
                found = True
                break
        
        if not found:
            courses.append(course_data)
        
        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            for course in courses:
                f.write('\t'.join(course) + '\n')
    
    @classmethod
    def load_from_file(cls):
        """从course.dat文件加载数据到数据库"""
        file_path = os.path.join(settings.BASE_DIR, 'data', 'course.dat')
        if not os.path.exists(file_path):
            return 0
        
        count = 0
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    parts = line.split('\t')
                    if len(parts) >= 3:
                        course_id, course_name, credits = parts[:3]
                        try:
                            # 使用get_or_create避免重复创建
                            course, created = cls.objects.get_or_create(
                                course_id=course_id,
                                defaults={
                                    'course_name': course_name,
                                    'credits': int(credits)
                                }
                            )
                            if created:
                                count += 1
                        except Exception as e:
                            print(f"导入课程数据失败: {course_id} - {e}")
        return count


class Score(models.Model):
    """成绩数据模型"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name='学生')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, verbose_name='课程')
    score = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='成绩')
    date = models.DateField(auto_now=True, verbose_name='录入日期')
    
    class Meta:
        verbose_name = '成绩'
        verbose_name_plural = '成绩'
        unique_together = ['student', 'course']  # 一个学生一门课程只能有一个成绩
        
    def __str__(self):
        return f"{self.student.name} - {self.course.course_name}: {self.score}"
    
    def save_to_file(self):
        """保存到score.dat文件"""
        file_path = os.path.join(settings.BASE_DIR, 'data', 'score.dat')
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # 读取现有数据
        scores = []
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                scores = [line.strip().split('\t') for line in f if line.strip()]
        
        # 更新或添加当前成绩数据
        score_data = [
            self.student.student_id, self.student.name,
            self.course.course_id, self.course.course_name,
            str(self.score), self.date.strftime('%Y-%m-%d')
        ]
        
        # 查找是否已存在（根据学号和课程号）
        found = False
        for i, score in enumerate(scores):
            if len(score) >= 3 and score[0] == self.student.student_id and score[2] == self.course.course_id:
                scores[i] = score_data
                found = True
                break
        
        if not found:
            scores.append(score_data)
        
        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            for score in scores:
                f.write('\t'.join(score) + '\n')
    
    @classmethod
    def load_from_file(cls):
        """从score.dat文件加载数据到数据库"""
        file_path = os.path.join(settings.BASE_DIR, 'data', 'score.dat')
        if not os.path.exists(file_path):
            return 0
        
        count = 0
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    parts = line.split('\t')
                    if len(parts) >= 5:
                        student_id, student_name, course_id, course_name, score_value = parts[:5]
                        try:
                            # 查找学生和课程
                            student = Student.objects.get(student_id=student_id)
                            course = Course.objects.get(course_id=course_id)
                            
                            # 使用get_or_create避免重复创建
                            score, created = cls.objects.get_or_create(
                                student=student,
                                course=course,
                                defaults={
                                    'score': Decimal(score_value)
                                }
                            )
                            if created:
                                count += 1
                        except (Student.DoesNotExist, Course.DoesNotExist) as e:
                            print(f"导入成绩数据失败，找不到学生或课程: {student_id}-{course_id} - {e}")
                        except Exception as e:
                            print(f"导入成绩数据失败: {student_id}-{course_id} - {e}")
        return count


class Enrollment(models.Model):
    """选课记录模型"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name='学生')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, verbose_name='课程')
    enrollment_date = models.DateField(auto_now_add=True, verbose_name='选课日期')
    
    class Meta:
        verbose_name = '选课记录'
        verbose_name_plural = '选课记录'
        unique_together = ['student', 'course']
        
    def __str__(self):
        return f"{self.student.name} 选修 {self.course.course_name}"


class CustomUser(AbstractUser):
    """自定义用户模型，区分学生和教师"""
    ROLE_CHOICES = [
        ('student', '学生'),
        ('teacher', '教师'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, verbose_name='角色')
    # 关联到学生模型
    student = models.OneToOneField(Student, on_delete=models.CASCADE, null=True, blank=True, verbose_name='关联学生')
    
    class Meta:
        verbose_name = '用户'
        verbose_name_plural = '用户'
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
