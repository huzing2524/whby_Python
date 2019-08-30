# -*- coding: utf-8 -*-
# @Time   : 19-6-22 上午10:16
# @Author : huziying
# @File   : middleware.py

import jwt
from django.conf import settings
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin
from django.db import connection
from rest_framework import status
from django_redis import get_redis_connection

from .constants import REDIS_CACHE


class JwtTokenMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # print(request.path)
        token = request.META.get("HTTP_AUTHORIZATION")
        if token:
            try:
                token = token.split(" ")[-1]
                # print(token)
                payload = jwt.decode(token, key=settings.JWT_SECRET_KEY, verify=True)
                if "username" in payload and "exp" in payload:
                    # print("payload=", payload)
                    REDIS_CACHE["username"] = payload["username"]
                    request.redis_cache = REDIS_CACHE
                    # print("request.redis_cache=", request.redis_cache)
                else:
                    raise jwt.InvalidTokenError
            except jwt.ExpiredSignatureError:
                return HttpResponse("jwt token已过期！", status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return HttpResponse("非法的jwt token！", status=status.HTTP_401_UNAUTHORIZED)
        else:
            return HttpResponse("缺少jwt token！", status=status.HTTP_401_UNAUTHORIZED)


class RedisMiddleware(MiddlewareMixin):
    """Redis读取缓存, hash类型
    key: "13212345678"
    field: value
    {"factory_id": "QtfjtzpNcM9DuGgR6e"},
    {"permission": "3,4,5,6,7,8,11"},
    {"whby_role": "2,3,4,5,6"}
    """

    def process_request(self, request):
        phone = request.redis_cache["username"]
        conn = get_redis_connection("default")
        # print(phone), print(conn.hvals(phone))
        if phone.isdigit():
            permission = conn.hget(phone, "permission")
            whby_role = conn.hget(phone, "whby_role")

            if not permission or not whby_role:
                cursor = connection.cursor()
                cursor.execute("select rights from wh_roles where phone = '%s';" % phone)
                result = cursor.fetchone()
                if result:
                    if len(result[0]) > 1:
                        conn.hset(phone, "whby_role", ','.join(result[0]))
                        whby_role = ','.join(result[0])
                    else:
                        conn.hset(phone, "whby_role", result[0][0])
                        whby_role = result[0][0]

                cursor.execute("select rights from factory_users where phone = '%s';" % phone)
                result2 = cursor.fetchone()
                if result2:
                    if len(result2[0]) > 1:
                        conn.hset(phone, "permission", ",".join(result2[0]))
                        permission = ",".join(result2[0])
                    else:
                        conn.hset(phone, "permission", result2[0][0])
                        permission = result2[0][0]

                cursor.close()

            request.redis_cache["permission"] = permission
            request.redis_cache["whby_role"] = whby_role
        else:
            return None
