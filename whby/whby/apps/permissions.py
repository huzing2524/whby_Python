# -*- coding: utf-8 -*-
# @Time   : 19-6-22 上午10:16
# @Author : huziying
# @File   : permissions.py

from rest_framework.permissions import BasePermission


# 权限 1: 超级管理员, 2: 系统设置, 3: 数据录入, 4: 报表导入, 5: 报表模板, 6: 基础数据, 7: 报表查询

class SuperAdminPermission(BasePermission):
    """超级管理员权限: 1"""

    # 无权限的显示信息
    message = "您没有权限查看！"

    def has_permission(self, request, view):
        role = request.redis_cache["whby_role"]
        if role:
            if role == "1":
                return True
            else:
                return False
        else:
            return False


class SystemSettings(BasePermission):
    """系统设置权限: 2"""

    message = "您没有权限查看！"

    def has_permission(self, request, view):
        role = request.redis_cache["whby_role"]  # <class 'str'>
        if role:
            if "1" in role or "2" in role:
                return True
            else:
                return False
        else:
            return False


class DataInput(BasePermission):
    """数据录入: 3"""

    message = "您没有权限查看！"

    def has_permission(self, request, view):
        role = request.redis_cache["whby_role"]
        if role:
            if "1" in role or "3" in role:
                return True
            else:
                return False
        else:
            return False


class ReportImport(BasePermission):
    """报表导入: 4"""

    message = "您没有权限查看！"

    def has_permission(self, request, view):
        role = request.redis_cache["whby_role"]
        if role:
            if "1" in role or "4" in role:
                return True
            else:
                return False
        else:
            return False


class ReportTemplate(BasePermission):
    """报表模板: 5"""

    message = "您没有权限查看！"

    def has_permission(self, request, view):
        role = request.redis_cache["whby_role"]
        if role:
            if "1" in role or "5" in role:
                return True
            else:
                return False
        else:
            return False


class BasicData(BasePermission):
    """基础数据: 6"""

    message = "您没有权限查看！"

    def has_permission(self, request, view):
        role = request.redis_cache["whby_role"]
        if role:
            if "1" in role or "6" in role:
                return True
            else:
                return False
        else:
            return False


class ReportInquiry(BasePermission):
    """报表查询: 7"""

    message = "您没有权限查看！"

    def has_permission(self, request, view):
        role = request.redis_cache["whby_role"]
        if role:
            if "1" in role or "7" in role:
                return True
            else:
                return False
        else:
            return False
