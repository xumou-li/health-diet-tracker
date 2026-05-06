"""统一响应格式"""
from flask import jsonify


def success(data=None, message='success', code=200):
    """成功响应"""
    response = {
        'code': code,
        'message': message,
        'data': data
    }
    return jsonify(response), code


def error(message='error', code=400, data=None):
    """错误响应"""
    response = {
        'code': code,
        'message': message,
        'data': data
    }
    return jsonify(response), code
