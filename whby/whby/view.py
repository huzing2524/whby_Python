import logging
import json
import os
from django.db import connection
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django_redis import get_redis_connection

from .loadexcel import read_batch, read_quality
from permissions import ReportTemplate, ReportImport

logger = logging.getLogger('django')


class TragetDiff(APIView):
    """生产差异表"""
    permission_classes = [ReportTemplate]

    def get(self, request):
        """权限主页列表"""
        cursor = connection.cursor()
        try:
            cursor.execute("select data from wh_product_target_diff;")
            result = cursor.fetchone()
            if not result:
                return Response({'data': []}, status=status.HTTP_200_OK)
            else:
                return Response({'data': result[0]}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(e)
            return Response({"res": 1, "errmsg": "服务器错误！"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            cursor.close()

    def post(self, request):
        """生产差异表"""
        month = request.data.get("month")
        data = request.data.get("data")
        if not data or not month:
            return Response({"res": 1, "errmsg": "输入数据有误"}, status=status.HTTP_400_BAD_REQUEST)

        sql = "insert into wh_product_target_diff values ('{0}', array{1}) on conflict (month) " \
              "do update set data = array{1} ".format(month, data)
        cursor = connection.cursor()
        try:
            cursor.execute(sql)
            connection.commit()
            return Response({"res": 0}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(e)
            return Response({"res": 1, "errmsg": "服务器错误！"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            cursor.close()


class TragetDiffType(APIView):
    """生产差异表类型"""
    permission_classes = [ReportTemplate]

    def get(self, request):
        """权限主页列表"""
        cursor = connection.cursor()
        try:
            cursor.execute("select data from wh_product_target_type;")
            result = cursor.fetchone()
            if not result:
                return Response({'data': []}, status=status.HTTP_200_OK)
            else:
                return Response(result[0], status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(e)
            return Response({"res": 1, "errmsg": "服务器错误！"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            cursor.close()

    def post(self, request):
        """生产差异表"""
        data = request.data.get("data")
        if not data:
            return Response({"res": 1, "errmsg": "输入数据有误"}, status=status.HTTP_400_BAD_REQUEST)

        sql = "insert into wh_product_target_type (id, data) values (1, '{0}') on conflict (id) " \
              "do update set data = '{0}' ".format(json.dumps({'data': data}))
        cursor = connection.cursor()
        try:
            cursor.execute(sql)
            connection.commit()
            return Response({"res": 0}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(e)
            return Response({"res": 1, "errmsg": "服务器错误！"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            cursor.close()


class ProductBatch(APIView):
    permission_classes = [ReportImport]

    def post(self, request):
        file = request.FILES['upfile']
        month = request.data.get('month')
        f = open(file.name, "wb")
        # print('upload file name ', file.name)
        f.write(file.read())
        f.close()
        cursor = connection.cursor()
        try:
            all_data, schedule = read_batch(file.name)
            conn = get_redis_connection()
            conn.hset(month, 'BATCH-ALL', json.dumps(all_data))
            for key, value in schedule.items():
                conn.hset(month, 'BATCH-' + key, json.dumps(value))
            sql = "insert into wh_product_batch values ('{0}', '{1}', '{2}') on conflict (month) " \
                  "do update set all_data = '{1}', schedule = '{2}' ".format(month, json.dumps(all_data),
                                                                             json.dumps(schedule))
            cursor.execute(sql)
            connection.commit()
            return Response({"res": 0}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(e)
            return Response({"res": 1, "errmsg": "服务器错误！"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            os.remove(file.name)
            cursor.close()

    def get(self, request):
        month = request.query_params.get("month")
        schedule = request.query_params.get("schedule")
        if not month or not schedule:
            return Response({"res": 1, "errmsg": "输入数据有误"}, status=status.HTTP_400_BAD_REQUEST)
        header = [
            ['时间', '班次', '成品产量(m3)', '废品产量(m3)', '刨花(T/m3)', 'MDI(KG/M3)', '石腊(KG/M3)',
             '增粘剂(KG/M3)', '脱模剂(KG/M3)']]
        conn = get_redis_connection()
        cache_data = conn.hget(month, 'BATCH-' + schedule)
        if not cache_data:
            sql = "select all_data, schedule from wh_product_batch where month = '{}'".format(month)
            cursor = connection.cursor()
            try:
                cursor.execute(sql)
                res = cursor.fetchone()
                if not res:
                    return Response({"data": header}, status=status.HTTP_200_OK)
                if schedule == 'ALL':
                    result = res[0]
                else:
                    result = res[1][schedule]
                conn.hset(month, 'BATCH-ALL', json.dumps(res[0]))
                for key, value in res[1].items():
                    conn.hset(month, 'BATCH-' + key, json.dumps(value))
            except KeyError:
                return Response({"data": header}, status=status.HTTP_200_OK)
            except Exception as e:
                logger.error(e)
                return Response({"res": 1, "errmsg": "服务器错误！"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            finally:
                cursor.close()
        else:
            result = json.loads(cache_data)
        res = []
        for i in range(1, 32):
            row = result.get(str(i))
            if row:
                row.insert(0, str(i))
                row.insert(1, str(schedule))
                res.append(row)
        header.extend(res)
        return Response({"data": header}, status=status.HTTP_200_OK)


class ProductQuality(APIView):
    permission_classes = [ReportImport]

    def post(self, request):
        file = request.FILES['upfile']
        month = request.data.get('month')
        f = open(file.name, "wb")
        print('upload file name ', file.name)
        f.write(file.read())
        f.close()
        all_data = read_quality(file.name)
        conn = get_redis_connection()
        for key, value in all_data.items():
            conn.hset(month, 'Quality-' + key, json.dumps(value))
        sql = "insert into wh_product_quality values ('{0}', '{1}') on conflict (month) " \
              "do update set all_data = '{1}'".format(month, json.dumps(all_data))
        cursor = connection.cursor()
        try:
            cursor.execute(sql)
            connection.commit()
            return Response({"res": 0}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(e)
            return Response({"res": 1, "errmsg": "服务器错误！"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            os.remove(file.name)
            cursor.close()

    def get(self, request):
        month = request.query_params.get("month")
        schedule = request.query_params.get("schedule")
        header = [['周期', '详细日期', '检验班次', '上班时间', '检验员', '批次', '胶水型号', '产品名称(新)',
                   '长', '宽', '厚', '产品等级', '入库总件数',
                   '包装(张/件)', '入库总张数', '总产量(m3)', '降级说明', '备注']]
        conn = get_redis_connection()
        cache_data = conn.hget(month, 'Quality-' + schedule)
        if not cache_data:
            sql = "select all_data from wh_product_quality where month = '{}'".format(month)
            cursor = connection.cursor()
            try:
                cursor.execute(sql)
                res = cursor.fetchone()
                if not res:
                    return Response({"data": header}, status=status.HTTP_200_OK)
                result = res[0][schedule]
                for key, value in res[0].items():
                    conn.hset(month, 'Quality-' + key, json.dumps(value))
            except KeyError:
                return Response({"data": header}, status=status.HTTP_200_OK)
            except Exception as e:
                logger.error(e)
                return Response({"res": 1, "errmsg": "服务器错误！"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            finally:
                cursor.close()
        else:
            result = json.loads(cache_data)
        header.extend(result)
        return Response({"data": header}, status=status.HTTP_200_OK)
