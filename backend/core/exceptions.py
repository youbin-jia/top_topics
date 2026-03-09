"""
自定义异常处理
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    自定义异常处理器

    Args:
        exc: 异常对象
        context: 上下文信息

    Returns:
        Response对象
    """
    # 调用REST framework默认异常处理器
    response = exception_handler(exc, context)

    if response is not None:
        # 自定义错误响应格式
        custom_response_data = {
            'success': False,
            'message': '请求失败',
            'errors': {}
        }

        if isinstance(response.data, dict):
            if 'detail' in response.data:
                custom_response_data['message'] = response.data['detail']
            else:
                custom_response_data['errors'] = response.data
        elif isinstance(response.data, list):
            custom_response_data['message'] = response.data[0]

        response.data = custom_response_data

    else:
        # 处理非API异常
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        response = Response(
            {
                'success': False,
                'message': '服务器内部错误',
                'errors': str(exc)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return response
