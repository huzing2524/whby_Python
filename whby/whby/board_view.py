import logging
import json

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django_redis import get_redis_connection
from django.db import connection

logger = logging.getLogger('django')


class DailyReport(APIView):
    def get(self, request):
        date = request.query_params.get("date")
        schedule = request.query_params.get("schedule")
        conn = get_redis_connection()
        cache_data = conn.hget(date, 'BATCH-' + schedule)
        cache_plan = conn.hget(date, 'PLAN')
        cache_days = conn.hget(date, 'PROD_DAYS')
        res = {
            'plan': 0,
            'product': 0,
            'average': 0,
            'data': 0
        }
        if cache_plan and cache_days:
            res['plan'] = cache_plan
            res['average'] = round(int(cache_plan) / int(cache_days), 2)
        else:
            # BUG: date=201902, str(int('201902'[-2:]))=2, int()会把浮点数转换成整形, 丢掉前面的0. 导致sql查询的时候date日期匹配错误
            # sql = "select output, production_days from wh_annual_plan where date = '{}'".format(
            #     date[0:4] + '-' + str(int(date[-2:])))

            sql = "select output, production_days from wh_annual_plan where date = '{}'".format(
                date[0:4] + '-' + date[-2:].zfill(2))  # 补0

            cursor = connection.cursor()
            try:
                cursor.execute(sql)
                result = cursor.fetchone()
                if result:
                    res['plan'] = result[0]
                    res['average'] = round(int(result[0]) / int(result[1]), 2)
                    conn.hset(date, 'PLAN', result[0])
                    conn.hset(date, 'PROD_DAYS', result[1])
            except Exception as e:
                logger.error(e)
            finally:
                cursor.close()

        if cache_data:
            data = json.loads(cache_data)
            data_res = []
            total, n = 0, 0

            for key in data:
                total += sum(data[key])
                data_res.append(key)
                res['product'] = total
                res['data'] = data_res

            # for i in range(1, 32):
            #     row = data.get(str(i))  # BUG: data字典遍历错误, get(键)不是取索引
            #     if row:
            #         n += 1
            #         total += row[1]
            #         row.insert(0, str(i))
            #         data_res.append(row)
            #         res['product'] = total
            #         res['data'] = data_res

        return Response(res, status=status.HTTP_200_OK)


class OutPut(APIView):
    def get(self, request):
        date = request.query_params.get("date")
        schedule = request.query_params.get("schedule")
        conn = get_redis_connection()
        cache_data = conn.hget(date, 'BATCH-' + schedule)
        if cache_data:
            data = json.loads(cache_data)
            data_res = []
            date_list, n = [], 0

            for key in data:
                row = data.get(key)
                date_list.append(key)
                data_res.extend(row)

            # for i in range(1, 32):
            #     row = data.get(str(i))  # BUG: data字典遍历错误, get(键)不是取索引
            #     if row:
            #         date_list.append(str(i))
            #         data_res.append(row[1])
            res = {
                'date': date_list,
                'data': data_res
            }
            return Response(res, status=status.HTTP_200_OK)
        else:
            return Response({'date': [], 'data': []}, status=status.HTTP_200_OK)


class IncomingQuality(APIView):
    def get(self, request):
        date = request.query_params.get("date")
        schedule = request.query_params.get("schedule")
        conn = get_redis_connection()
        cache_data = conn.hget(date, 'Quality-' + schedule)
        res = {
            "total": 0,
            "high": 0,
            "qualified": 0,
            "waste": 0,
            "make": 0
        }
        reflection = {
            '自制品': 'make',
            '废品': 'waste',
            '优等品': 'high',
            '合格品': 'qualified'
        }
        if cache_data:
            result = json.loads(cache_data)
            for x in result:
                level = x[11]
                count = x[12]
                res['total'] += count
                if reflection.get(level):
                    res[reflection[level]] += count
            return Response(res, status=status.HTTP_200_OK)
        else:
            return Response(res, status=status.HTTP_200_OK)
