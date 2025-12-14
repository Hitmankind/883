"""
DeepSeek API 集成客户端
用于学生学情分析的 AI 服务接口
"""

import requests
import json
import time
import logging
from typing import Dict, Optional, Any
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from .models import AIServiceLog

# 配置日志
logger = logging.getLogger(__name__)


class DeepSeekClient:
    """DeepSeek API 客户端类"""

    def __init__(self, api_key: str = None, base_url: str = None):
        """
        初始化 DeepSeek 客户端

        Args:
            api_key: DeepSeek API 密钥
            base_url: DeepSeek API 基础 URL
        """
        self.api_key = api_key or getattr(settings, 'DEEPSEEK_API_KEY', None)
        self.base_url = base_url or getattr(settings, 'DEEPSEEK_BASE_URL', 'https://api.deepseek.com/v1')

        if not self.api_key:
            raise ImproperlyConfigured("DEEPSEEK_API_KEY not configured in settings")

        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'Django-Student-Analysis/1.0'
        }

        # 模型配置
        self.model = getattr(settings, 'DEEPSEEK_MODEL', 'deepseek-chat')
        self.max_tokens = getattr(settings, 'DEEPSEEK_MAX_TOKENS', 4000)
        self.temperature = getattr(settings, 'DEEPSEEK_TEMPERATURE', 0.7)
        self.timeout = getattr(settings, 'DEEPSEEK_TIMEOUT', 60)

    def _make_request(self, endpoint: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        发送 HTTP 请求到 DeepSeek API

        Args:
            endpoint: API 端点
            data: 请求数据

        Returns:
            API 响应数据或 None
        """
        url = f"{self.base_url}/{endpoint}"

        try:
            response = requests.post(
                url,
                headers=self.headers,
                json=data,
                timeout=self.timeout
            )

            response.raise_for_status()
            return response.json()

        except requests.exceptions.Timeout:
            logger.error(f"DeepSeek API 请求超时: {endpoint}")
            return None

        except requests.exceptions.RequestException as e:
            logger.error(f"DeepSeek API 请求失败: {e}")
            return None

        except json.JSONDecodeError as e:
            logger.error(f"DeepSeek API 响应解析失败: {e}")
            return None

    def generate_analysis(
        self,
        prompt: str,
        student_analysis_id: Optional[int] = None,
        request_type: str = 'analysis'
    ) -> Dict[str, Any]:
        """
        生成学生学情分析

        Args:
            prompt: 分析提示词
            student_analysis_id: 学生分析记录ID
            request_type: 请求类型

        Returns:
            包含分析结果和元数据的字典
        """
        start_time = time.time()

        # 记录请求日志
        service_log = AIServiceLog.objects.create(
            request_type=request_type,
            request_prompt=prompt,
            request_data={'model': self.model, 'max_tokens': self.max_tokens},
            status='processing'
        )

        if student_analysis_id:
            service_log.student_analysis_id = student_analysis_id
            service_log.save()

        # 构建请求数据
        request_data = {
            'model': self.model,
            'messages': [
                {
                    'role': 'system',
                    'content': '你是一位专业的教育学分析师和AI学习顾问，擅长学生学情分析和个性化学习建议。请基于提供的数据进行全面、客观、准确的分析。'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
            'stream': False,
            'top_p': 0.95,
            'frequency_penalty': 0.1,
            'presence_penalty': 0.1
        }

        try:
            # 发送请求
            response = self._make_request('chat/completions', request_data)

            if not response:
                service_log.status = 'failed'
                service_log.error_message = 'API 请求失败'
                service_log.save()

                return {
                    'success': False,
                    'error': 'API 请求失败',
                    'response_time': time.time() - start_time,
                    'log_id': service_log.id
                }

            # 解析响应
            content = response.get('choices', [{}])[0].get('message', {}).get('content', '')
            usage = response.get('usage', {})

            response_time = time.time() - start_time

            # 更新日志
            service_log.response_content = content
            service_log.response_time = response_time
            service_log.status = 'success'
            service_log.save()

            return {
                'success': True,
                'content': content,
                'usage': usage,
                'response_time': response_time,
                'model': self.model,
                'log_id': service_log.id
            }

        except Exception as e:
            logger.error(f"生成分析时发生错误: {e}")

            service_log.status = 'failed'
            service_log.error_message = str(e)
            service_log.save()

            return {
                'success': False,
                'error': str(e),
                'response_time': time.time() - start_time,
                'log_id': service_log.id
            }

    def validate_response(self, content: str) -> Dict[str, Any]:
        """
        验证 AI 响应的质量和格式

        Args:
            content: AI 生成的响应内容

        Returns:
            验证结果字典
        """
        validation_result = {
            'is_valid': True,
            'issues': [],
            'confidence_score': 0.8,
            'suggestions': []
        }

        # 基本格式检查
        if not content or len(content.strip()) < 100:
            validation_result['is_valid'] = False
            validation_result['issues'].append('响应内容过短')
            validation_result['confidence_score'] = 0.2

        # Markdown 格式检查
        if not any(marker in content for marker in ['#', '##', '###', '**', '*']):
            validation_result['issues'].append('缺少 Markdown 格式标记')
            validation_result['confidence_score'] -= 0.1

        # 结构化内容检查
        required_sections = ['总体评估', '分析', '建议']
        missing_sections = []
        for section in required_sections:
            if section not in content:
                missing_sections.append(section)

        if missing_sections:
            validation_result['issues'].append(f'缺少必要章节: {", ".join(missing_sections)}')
            validation_result['confidence_score'] -= 0.2

        # 内容质量检查
        if len(content) > 10000:
            validation_result['suggestions'].append('响应内容过长，建议精简')

        # 置信度评估
        validation_result['confidence_score'] = max(0, validation_result['confidence_score'])

        return validation_result

    def estimate_confidence(self, content: str, student_data_size: int) -> float:
        """
        估算 AI 分析的置信度

        Args:
            content: AI 生成的响应内容
            student_data_size: 学生数据量

        Returns:
            置信度分数 (0-1)
        """
        confidence = 0.5  # 基础置信度

        # 基于数据量调整
        if student_data_size > 50:
            confidence += 0.2
        elif student_data_size > 20:
            confidence += 0.1
        elif student_data_size < 5:
            confidence -= 0.2

        # 基于内容长度调整
        content_length = len(content)
        if content_length > 2000:
            confidence += 0.1
        elif content_length < 500:
            confidence -= 0.1

        # 基于结构化程度调整
        if '# ' in content and '## ' in content:
            confidence += 0.1

        # 基于详细程度调整
        if content.count('**') > 10:
            confidence += 0.1

        return min(1.0, max(0.0, confidence))

    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息

        Returns:
            模型信息字典
        """
        return {
            'model': self.model,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
            'timeout': self.timeout,
            'base_url': self.base_url,
            'features': [
                '学情分析',
                '个性化建议',
                '多维度评估',
                '趋势分析',
                'SWOT分析'
            ]
        }

    def health_check(self) -> bool:
        """
        检查 API 服务健康状态

        Returns:
            服务是否可用
        """
        try:
            test_prompt = "请回复'服务正常'"
            result = self.generate_analysis(test_prompt, request_type='evaluation')
            return result.get('success', False)
        except Exception:
            return False


# 创建全局客户端实例
try:
    deepseek_client = DeepSeekClient()
except ImproperlyConfigured:
    logger.warning("DeepSeek API not configured, using mock client")
    deepseek_client = None


def get_deepseek_client() -> DeepSeekClient:
    """
    获取 DeepSeek 客户端实例

    Returns:
        DeepSeekClient 实例
    """
    if deepseek_client is None:
        raise ImproperlyConfigured("DeepSeek API not properly configured")
    return deepseek_client