# ====================================
# 5. audit_log/middleware.py
# ====================================

import time
import logging
from .signals import _thread_locals

logger = logging.getLogger('request_timing')


class AuditLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.request = request

        try:
            response = self.get_response(request)
        finally:
            if hasattr(_thread_locals, 'request'):
                delattr(_thread_locals, 'request')

        return response


class RequestTimingMiddleware:
    """
    Middleware لتسجيل وقت كل request
    يسجل: المسار، الطريقة، الوقت المستغرق، كود الاستجابة
    """

    # الحد الأدنى للتسجيل (بالثانية) - يسجل فقط الطلبات البطيئة
    SLOW_REQUEST_THRESHOLD = 0.5  # نصف ثانية

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # تجاهل الملفات الثابتة
        if request.path.startswith(('/static/', '/media/')):
            return self.get_response(request)

        start_time = time.time()

        response = self.get_response(request)

        duration = time.time() - start_time

        # تسجيل جميع الطلبات البطيئة
        if duration >= self.SLOW_REQUEST_THRESHOLD:
            logger.warning(
                f"SLOW REQUEST | {request.method} {request.path} | "
                f"{duration:.2f}s | Status: {response.status_code} | "
                f"User: {request.user if request.user.is_authenticated else 'Anonymous'}"
            )
        else:
            # تسجيل الطلبات العادية بمستوى INFO
            logger.info(
                f"{request.method} {request.path} | "
                f"{duration:.3f}s | Status: {response.status_code}"
            )

        # إضافة header للتوقيت (مفيد للتصحيح)
        response['X-Request-Duration'] = f"{duration:.3f}s"

        return response
