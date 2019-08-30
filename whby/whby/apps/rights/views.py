from django.shortcuts import render

# Create your views here.

import logging
import re
import arrow

from django.db import connection
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django_redis import get_redis_connection

from permissions import SystemSettings

logger = logging.getLogger('django')


class Rights(APIView):
    """权限管理 /rights"""
    permission_classes = [SystemSettings]

    def get(self, request):
        """权限主页列表"""
        cursor = connection.cursor()

        data = list()
        try:
            cursor.execute("select phone, coalesce(name, '') as name, rights from wh_roles order by time desc;")
            result = cursor.fetchall()
            for res in result:
                di = dict()
                di["phone"] = res[0]
                di["name"] = res[1]
                di["rights"] = res[2] or list()
                data.append(di)
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(e)
            return Response({"res": 1, "errmsg": "服务器错误！"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            cursor.close()

    def post(self, request):
        """新增管理员"""
        phone = request.data.get("phone")
        name = request.data.get("name", "")
        rights = request.data.get("rights", list())

        if not all([phone, rights]):
            return Response({"res": 1, "errmsg": "缺少参数！"}, status=status.HTTP_200_OK)
        if not re.match("^(13[0-9]|14[579]|15[0-3,5-9]|16[6]|17[0135678]|18[0-9]|19[89])\\d{8}$", phone):
            return Response({"res": 1, "errmsg": "电话号码格式错误！"}, status=status.HTTP_200_OK)
        if not isinstance(rights, list):
            return Response({"res": 1, "errmsg": "参数类型错误！"}, status=status.HTTP_200_OK)
        rights = sorted(list(set(rights)))
        rights.remove("1") if "1" in rights else rights

        cursor = connection.cursor()

        try:
            redis_conn = get_redis_connection("default")
            redis_conn.hdel(phone, "permission", "whby_role")

            cursor.execute("select count(*) from wh_roles where phone = '{}';".format(phone))
            phone_check = cursor.fetchone()[0]
            if phone_check >= 1:
                return Response({"res": 1, "errmsg": "此号码已存在！"}, status=status.HTTP_200_OK)

            cursor.execute("select count(*) from factory_users where phone = '%s';" % phone)
            factory_check = cursor.fetchone()[0]
            if factory_check >= 1:
                return Response({"res": 1, "errmsg": "此号码已加入其它公司！"}, status=status.HTTP_200_OK)

            timestamp = arrow.now().timestamp
            cursor.execute("insert into wh_roles (phone, name, rights, time) values ('%s', '%s', '{%s}', %d);" % (
                phone, name, ','.join(rights), timestamp))
            cursor.execute("insert into factory_users (phone, name, rights, time, factory) values ('%s', '%s', '{11}', "
                           "%d, 'whby');" % (phone, name, timestamp))

            connection.commit()
            return Response({"res": 0}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(e)
            return Response({"res": 1, "errmsg": "服务器错误！"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            cursor.close()

    def put(self, request):
        """修改管理员"""
        phone = request.data.get("phone")
        name = request.data.get("name", "")
        rights = request.data.get("rights", list())

        if not all([phone, rights]):
            return Response({"res": 1, "errmsg": "缺少参数！"}, status=status.HTTP_200_OK)
        if not re.match("^(13[0-9]|14[579]|15[0-3,5-9]|16[6]|17[0135678]|18[0-9]|19[89])\\d{8}$", phone):
            return Response({"res": 1, "errmsg": "电话号码格式错误！"}, status=status.HTTP_200_OK)
        if not isinstance(rights, list):
            return Response({"res": 1, "errmsg": "参数类型错误！"}, status=status.HTTP_200_OK)
        rights = sorted(list(set(rights)))
        rights.remove("1") if "1" in rights else rights

        cursor = connection.cursor()

        try:
            redis_conn = get_redis_connection("default")
            redis_conn.hdel(phone, "permission", "whby_role")

            cursor.execute("select count(*) from wh_roles where phone = '{}';".format(phone))
            phone_check = cursor.fetchone()[0]
            if phone_check <= 0:
                return Response({"res": 1, "errmsg": "此号码不存在！"}, status=status.HTTP_200_OK)

            cursor.execute("select rights from wh_roles where phone = '{}';".format(phone))
            rights_check = cursor.fetchone()[0]
            if "1" in rights_check:
                return Response({"res": 1, "errmsg": "不能修改超级管理权限！"}, status=status.HTTP_200_OK)

            cursor.execute("update wh_roles set name = '%s', rights = '{%s}' where phone = '%s';" %
                           (name, ','.join(rights), phone))

            connection.commit()
            return Response({"res": 0}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(e)
            return Response({"res": 1, "errmsg": "服务器错误！"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            cursor.close()

    def delete(self, request):
        """删除管理员"""
        phone = request.data.get("phone")

        if not phone:
            return Response({"res": 1, "errmsg": "缺少参数！"}, status=status.HTTP_200_OK)

        cursor = connection.cursor()

        try:
            cursor.execute("select count(*) from wh_roles where phone = '{}';".format(phone))
            phone_check = cursor.fetchone()[0]
            if phone_check <= 0:
                return Response({"res": 1, "errmsg": "此用户不存在！"}, status=status.HTTP_200_OK)

            cursor.execute("select rights, phone from wh_roles where phone = '{}';".format(phone))
            rights_check, phone = cursor.fetchone()
            if "1" in rights_check:
                return Response({"res": 1, "errmsg": "不能删除超级管理权限！"}, status=status.HTTP_200_OK)

            redis_conn = get_redis_connection("default")
            redis_conn.hdel(phone, "permission", "whby_role")

            cursor.execute("delete from wh_roles where phone = '%s';" % phone)
            cursor.execute("delete from factory_users where factory = 'whby' and phone = '%s';" % phone)

            connection.commit()
            return Response({"res": 0}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(e)
            return Response({"res": 1, "errmsg": "服务器错误！"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            cursor.close()
