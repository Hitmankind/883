from django.db import models
from django.contrib.auth.models import User
from students.models import Student
from django.utils import timezone
import json


class StudentAnalysis(models.Model):
    """学生学情分析模型"""

    ANALYSIS_TYPES = [
        ('academic_performance', '学业表现分析'),
        ('learning_progress', '学习进度分析'),
        ('strength_weakness', '优势劣势分析'),
        ('improvement_suggestions', '改进建议'),
        ('comprehensive', '综合分析'),
    ]

    STATUS_CHOICES = [
        ('pending', '待分析'),
        ('processing', '分析中'),
        ('completed', '已完成'),
        ('failed', '分析失败'),
    ]

    id = models.AutoField(primary_key=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name='学生')
    analysis_type = models.CharField(max_length=50, choices=ANALYSIS_TYPES, verbose_name='分析类型')
    title = models.CharField(max_length=200, verbose_name='分析标题')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='状态')

    # 输入数据
    input_data = models.JSONField(verbose_name='输入数据', help_text='用于分析的学生数据')

    # AI 分析结果
    analysis_result = models.TextField(null=True, blank=True, verbose_name='分析结果')
    ai_confidence = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True,
                                      verbose_name='AI 置信度', help_text='0.00-1.00')

    # 提示词工程
    prompt_template = models.TextField(verbose_name='提示词模板')
    actual_prompt = models.TextField(null=True, blank=True, verbose_name='实际使用的提示词')

    # 元数据
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    analyzed_at = models.DateTimeField(null=True, blank=True, verbose_name='分析完成时间')
    analyzed_by = models.CharField(max_length=100, default='DeepSeek AI', verbose_name='分析引擎')

    # 错误信息
    error_message = models.TextField(null=True, blank=True, verbose_name='错误信息')

    class Meta:
        verbose_name = '学生学情分析'
        verbose_name_plural = '学生学情分析'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student.name} - {self.get_analysis_type_display()}"

    def save(self, *args, **kwargs):
        if self.status == 'completed' and not self.analyzed_at:
            self.analyzed_at = timezone.now()
        super().save(*args, **kwargs)


class PromptTemplate(models.Model):
    """提示词模板模型"""

    ANALYSIS_TYPES = [
        ('academic_performance', '学业表现分析'),
        ('learning_progress', '学习进度分析'),
        ('strength_weakness', '优势劣势分析'),
        ('improvement_suggestions', '改进建议'),
        ('comprehensive', '综合分析'),
    ]

    name = models.CharField(max_length=100, unique=True, verbose_name='模板名称')
    analysis_type = models.CharField(max_length=50, choices=ANALYSIS_TYPES, verbose_name='分析类型')
    template = models.TextField(verbose_name='提示词模板')
    variables = models.JSONField(verbose_name='变量列表', help_text='模板中使用的变量列表')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '提示词模板'
        verbose_name_plural = '提示词模板'
        ordering = ['analysis_type', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_analysis_type_display()})"


class AIServiceLog(models.Model):
    """AI 服务调用日志"""

    REQUEST_TYPES = [
        ('analysis', '学情分析'),
        ('suggestion', '建议生成'),
        ('evaluation', '评估分析'),
    ]

    STATUS_CHOICES = [
        ('success', '成功'),
        ('failed', '失败'),
        ('timeout', '超时'),
    ]

    id = models.AutoField(primary_key=True)
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPES, verbose_name='请求类型')
    student_analysis = models.ForeignKey(StudentAnalysis, on_delete=models.CASCADE, null=True, blank=True, verbose_name='关联分析')

    # 请求信息
    request_prompt = models.TextField(verbose_name='请求提示词')
    request_data = models.JSONField(verbose_name='请求数据')

    # 响应信息
    response_content = models.TextField(null=True, blank=True, verbose_name='响应内容')
    response_time = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True,
                                      verbose_name='响应时间(秒)')

    # 状态信息
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, verbose_name='状态')
    error_message = models.TextField(null=True, blank=True, verbose_name='错误信息')

    # 元数据
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = 'AI 服务日志'
        verbose_name_plural = 'AI 服务日志'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_request_type_display()} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
