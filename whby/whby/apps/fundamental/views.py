import time
import logging

from fundamental.fund_utils import month

from django.db import connections
from psycopg2.extras import RealDictCursor

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from permissions import BasicData

logger = logging.getLogger('django')

# 基础数据---------------------------------------------------------------------------------------------------------------


class AnnualPlanMain(APIView):
    permission_classes = [BasicData]

    @staticmethod
    def get(request):
        conn = connections['default']
        conn.ensure_connection()
        cur = conn.connection.cursor(cursor_factory=RealDictCursor)

        # get query params
        year = request.query_params.get('year', str(time.localtime()[0]))
        # avoid sql injection

        if not year.isdigit():
            return Response({"res": 1, "errmsg": '非法参数!'}, status=status.HTTP_400_BAD_REQUEST)

        # query database
        sql = """
            select 
                date,
                output, 
                good_rate, 
                best_rate, 
                ng_rate, 
                production_days 
            from 
                wh_annual_plan 
            where 
                date like '{}%';"""
        try:
            cur.execute(sql.format(year))
            data = cur.fetchall()

            # process data
            result = list()
            result.append(['{}年'.format(year), '1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月',
                           '11月', '12月', '总计'])
            if data:
                result.append(['总产量'] + [i['output'] for i in data])
                result.append(['合格品率'] + [i['good_rate'] for i in data])
                result.append(['优等品率'] + [i['best_rate'] for i in data])
                result.append(['废品率'] + [i['ng_rate'] for i in data])
                result.append(['生产天数'] + [i['production_days'] for i in data])
            else:
                result.append(['总产量'] + [None for i in range(13)])
                result.append(['合格品率'] + [None for i in range(13)])
                result.append(['优等品率'] + [None for i in range(13)])
                result.append(['废品率'] + [None for i in range(13)])
                result.append(['生产天数'] + [None for i in range(13)])
        except Exception as e:
            logger.error(e)
            return Response({"res": 1, "errmsg": "服务器异常!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        cur.close()
        return Response(result, status=status.HTTP_200_OK)

    @staticmethod
    def put(request):
        conn = connections['default']
        conn.ensure_connection()
        cur = conn.connection.cursor(cursor_factory=RealDictCursor)

        data = request.data.get('update')

        year = data[0][0].strip('年')
        update_data = data[1:]

        sql = "insert into wh_annual_plan({}) values({}) on conflict(date) do update set {};"
        target = ['output', 'good_rate', 'best_rate', 'ng_rate', 'production_days']
        try:
            for i in range(13):
                if i < 12:
                    date = '{}-{}'.format(year, i+1)
                else:
                    date = '{}-total'.format(year)
                update = ','.join('%s = %s' % (key, repr(value[i+1])) for key, value in zip(target, update_data))
                insert_columns = "date," + ','.join(target)
                insert_values = "'{}',".format(date) + ','.join(repr(value[i + 1]) for value in update_data)
                cur.execute(sql.format(insert_columns, insert_values, update).replace('None', 'null'))
            conn.commit()
        except Exception as e:
            logger.error(e)
            return Response({"res": 1, "errmsg": "服务器异常!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        cur.close()
        return Response({"res": 0}, status=status.HTTP_200_OK)


class ScheduleMain(APIView):
    """会导致无法进入看板，不设置权限"""

    @staticmethod
    def get(request):
        conn = connections['default']
        conn.ensure_connection()
        cur = conn.connection.cursor(cursor_factory=RealDictCursor)

        sql = "select * from wh_schedules order by time desc;"

        try:
            cur.execute(sql)
            result = cur.fetchall()
        except Exception as e:
            logger.error(e)
            return Response({"res": 1, "errmsg": "服务器异常!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        cur.close()
        return Response(result, status=status.HTTP_200_OK)

    @staticmethod
    def post(request):
        conn = connections['default']
        conn.ensure_connection()
        cur = conn.connection.cursor(cursor_factory=RealDictCursor)

        id_ = request.data.get('id')
        name = request.data.get('name')
        time_ = int(time.time())

        sql_0 = "select count(1) from wh_schedules where name = '{}';".format(name)
        sql_1 = "select count(1) from wh_schedules where uuid = '{}';".format(id_)
        sql_2 = "insert into wh_schedules(uuid, name, time) values('{}', '{}', {});".format(id_, name, time_)

        try:
            cur.execute(sql_0)
            count = cur.fetchone()['count']
            if count:
                return Response({"res": 1, "errmsg": "此名称已存在!"}, status=status.HTTP_200_OK)
            cur.execute(sql_1)
            count = cur.fetchone()['count']
            if count:
                return Response({"res": 1, "errmsg": "此编码已存在!"}, status=status.HTTP_200_OK)

            cur.execute(sql_2)
            conn.commit()
        except Exception as e:
            logger.error(e)
            return Response({"res": 1, "errmsg": "服务器异常!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        cur.close()
        return Response({"res": 0}, status=status.HTTP_200_OK)

    # @staticmethod
    # def put(request):
    #     conn = connections['default']
    #     conn.ensure_connection()
    #     cur = conn.connection.cursor(cursor_factory=RealDictCursor)
    #
    #     id_ = request.data.get('id', '')
    #     name = request.data.get('name', '')
    #     uuid = request.data.get('uuid')
    #
    #     sql_0 = "select count(1) from wh_schedules where name = '{}' and uuid != '{}';".format(name, uuid)
    #     sql_1 = "select count(1) from wh_schedules where id = '{}' and uuid != '{}';".format(id_, uuid)
    #     sql_2 = "update wh_schedules set id = '{}', name = '{}' where uuid = '{}';".format(id_, name, uuid)
    #
    #     try:
    #         cur.execute(sql_0)
    #         count = cur.fetchone()['count']
    #         if count:
    #             return Response({"res": 1, "errmsg": "此名称已存在!"}, status=status.HTTP_200_OK)
    #         cur.execute(sql_1)
    #         count = cur.fetchone()['count']
    #         if count:
    #             return Response({"res": 1, "errmsg": "此编码已存在!"}, status=status.HTTP_200_OK)
    #
    #         cur.execute(sql_2)
    #         conn.commit()
    #     except Exception as e:
    #         logger.error(e)
    #         return Response({"res": 1, "errmsg": "服务器异常!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    #
    #     cur.close()
    #     return Response({"res": 0}, status=status.HTTP_200_OK)
    #
    # @staticmethod
    # def delete(request):
    #     conn = connections['default']
    #     conn.ensure_connection()
    #     cur = conn.connection.cursor(cursor_factory=RealDictCursor)
    #
    #     uuid = request.data.get('uuid')
    #
    #     sql = "delete from wh_schedules where uuid = '{}';".format(uuid)
    #
    #     try:
    #         cur.execute(sql)
    #         conn.commit()
    #     except Exception as e:
    #         logger.error(e)
    #         return Response({"res": 1, "errmsg": "服务器异常!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    #
    #     cur.close()
    #     return Response({"res": 0}, status=status.HTTP_200_OK)


class WorkshopMain(APIView):
    permission_classes = [BasicData]

    @staticmethod
    def get(request):
        conn = connections['default']
        conn.ensure_connection()
        cur = conn.connection.cursor(cursor_factory=RealDictCursor)

        sql = "select * from wh_workshop order by time desc;"

        try:
            cur.execute(sql)
            result = cur.fetchall()
        except Exception as e:
            logger.error(e)
            return Response({"res": 1, "errmsg": "服务器异常!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        cur.close()
        return Response(result, status=status.HTTP_200_OK)

    @staticmethod
    def post(request):
        conn = connections['default']
        conn.ensure_connection()
        cur = conn.connection.cursor(cursor_factory=RealDictCursor)

        id_ = request.data.get('id')
        name = request.data.get('name')
        time_ = int(time.time())

        sql_0 = "select count(1) from wh_workshop where name = '{}';".format(name)
        sql_1 = "select count(1) from wh_workshop where id = '{}';".format(id_)
        sql_2 = "insert into wh_workshop(id, name, time) values('{}', '{}', {});".format(id_, name, time_)

        try:
            cur.execute(sql_0)
            count = cur.fetchone()['count']
            if count:
                return Response({"res": 1, "errmsg": "此名称已存在!"}, status=status.HTTP_200_OK)
            cur.execute(sql_1)
            count = cur.fetchone()['count']
            if count:
                return Response({"res": 1, "errmsg": "此编码已存在!"}, status=status.HTTP_200_OK)

            cur.execute(sql_2)
            conn.commit()
        except Exception as e:
            logger.error(e)
            return Response({"res": 1, "errmsg": "服务器异常!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        cur.close()
        return Response({"res": 0}, status=status.HTTP_200_OK)

    @staticmethod
    def put(request):
        conn = connections['default']
        conn.ensure_connection()
        cur = conn.connection.cursor(cursor_factory=RealDictCursor)

        id_ = request.data.get('id', '')
        name = request.data.get('name', '')
        uuid = request.data.get('uuid')

        sql_0 = "select count(1) from wh_workshop where name = '{}' and uuid != '{}';".format(name, uuid)
        sql_1 = "select count(1) from wh_workshop where id = '{}' and uuid != '{}';".format(id_, uuid)
        sql_2 = "update wh_workshop set id = '{}', name = '{}' where uuid = '{}';".format(id_, name, uuid)

        try:
            cur.execute(sql_0)
            count = cur.fetchone()['count']
            if count:
                return Response({"res": 1, "errmsg": "此名称已存在!"}, status=status.HTTP_200_OK)
            cur.execute(sql_1)
            count = cur.fetchone()['count']
            if count:
                return Response({"res": 1, "errmsg": "此编码已存在!"}, status=status.HTTP_200_OK)

            cur.execute(sql_2)
            conn.commit()
        except Exception as e:
            logger.error(e)
            return Response({"res": 1, "errmsg": "服务器异常!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        cur.close()
        return Response({"res": 0}, status=status.HTTP_200_OK)

    @staticmethod
    def delete(request):
        conn = connections['default']
        conn.ensure_connection()
        cur = conn.connection.cursor(cursor_factory=RealDictCursor)

        uuid = request.data.get('uuid')

        sql = "delete from wh_workshop where uuid = '{}';".format(uuid)

        try:
            cur.execute(sql)
            conn.commit()
        except Exception as e:
            logger.error(e)
            return Response({"res": 1, "errmsg": "服务器异常!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        cur.close()
        return Response({"res": 0}, status=status.HTTP_200_OK)


class SectionMain(APIView):
    permission_classes = [BasicData]
    
    @staticmethod
    def get(request):
        conn = connections['default']
        conn.ensure_connection()
        cur = conn.connection.cursor(cursor_factory=RealDictCursor)

        sql = "select * from wh_section order by time desc;"

        try:
            cur.execute(sql)
            result = cur.fetchall()
        except Exception as e:
            logger.error(e)
            return Response({"res": 1, "errmsg": "服务器异常!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        cur.close()
        return Response(result, status=status.HTTP_200_OK)

    @staticmethod
    def post(request):
        conn = connections['default']
        conn.ensure_connection()
        cur = conn.connection.cursor(cursor_factory=RealDictCursor)

        id_ = request.data.get('id')
        name = request.data.get('name')
        time_ = int(time.time())

        sql_0 = "select count(1) from wh_section where name = '{}';".format(name)
        sql_1 = "select count(1) from wh_section where id = '{}';".format(id_)
        sql_2 = "insert into wh_section(id, name, time) values('{}', '{}', {});".format(id_, name, time_)

        try:
            cur.execute(sql_0)
            count = cur.fetchone()['count']
            if count:
                return Response({"res": 1, "errmsg": "此名称已存在!"}, status=status.HTTP_200_OK)
            cur.execute(sql_1)
            count = cur.fetchone()['count']
            if count:
                return Response({"res": 1, "errmsg": "此编码已存在!"}, status=status.HTTP_200_OK)

            cur.execute(sql_2)
            conn.commit()
        except Exception as e:
            logger.error(e)
            return Response({"res": 1, "errmsg": "服务器异常!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        cur.close()
        return Response({"res": 0}, status=status.HTTP_200_OK)

    @staticmethod
    def put(request):
        conn = connections['default']
        conn.ensure_connection()
        cur = conn.connection.cursor(cursor_factory=RealDictCursor)

        id_ = request.data.get('id', '')
        name = request.data.get('name', '')
        uuid = request.data.get('uuid')

        sql_0 = "select count(1) from wh_section where name = '{}' and uuid != '{}';".format(name, uuid)
        sql_1 = "select count(1) from wh_section where id = '{}' and uuid != '{}';".format(id_, uuid)
        sql_2 = "update wh_section set id = '{}', name = '{}' where uuid = '{}';".format(id_, name, uuid)

        try:
            cur.execute(sql_0)
            count = cur.fetchone()['count']
            if count:
                return Response({"res": 1, "errmsg": "此名称已存在!"}, status=status.HTTP_200_OK)
            cur.execute(sql_1)
            count = cur.fetchone()['count']
            if count:
                return Response({"res": 1, "errmsg": "此编码已存在!"}, status=status.HTTP_200_OK)

            cur.execute(sql_2)
            conn.commit()
        except Exception as e:
            logger.error(e)
            return Response({"res": 1, "errmsg": "服务器异常!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        cur.close()
        return Response({"res": 0}, status=status.HTTP_200_OK)

    @staticmethod
    def delete(request):
        conn = connections['default']
        conn.ensure_connection()
        cur = conn.connection.cursor(cursor_factory=RealDictCursor)

        uuid = request.data.get('uuid')

        sql = "delete from wh_section where uuid = '{}';".format(uuid)

        try:
            cur.execute(sql)
            conn.commit()
        except Exception as e:
            logger.error(e)
            return Response({"res": 1, "errmsg": "服务器异常!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        cur.close()
        return Response({"res": 0}, status=status.HTTP_200_OK)


class ProductMain(APIView):
    permission_classes = [BasicData]

    @staticmethod
    def get(request):
        conn = connections['default']
        conn.ensure_connection()
        cur = conn.connection.cursor(cursor_factory=RealDictCursor)

        sql = "select * from wh_product order by time desc;"

        try:
            cur.execute(sql)
            result = cur.fetchall()
        except Exception as e:
            logger.error(e)
            return Response({"res": 1, "errmsg": "服务器异常!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        cur.close()
        return Response(result, status=status.HTTP_200_OK)

    @staticmethod
    def post(request):
        conn = connections['default']
        conn.ensure_connection()
        cur = conn.connection.cursor(cursor_factory=RealDictCursor)

        id_ = request.data.get('id')
        name = request.data.get('name')
        time_ = int(time.time())

        sql_0 = "select count(1) from wh_product where name = '{}';".format(name)
        sql_1 = "select count(1) from wh_product where id = '{}';".format(id_)
        sql_2 = "insert into wh_product(id, name, time) values('{}', '{}', {});".format(id_, name, time_)

        try:
            cur.execute(sql_0)
            count = cur.fetchone()['count']
            if count:
                return Response({"res": 1, "errmsg": "此名称已存在!"}, status=status.HTTP_200_OK)
            cur.execute(sql_1)
            count = cur.fetchone()['count']
            if count:
                return Response({"res": 1, "errmsg": "此编码已存在!"}, status=status.HTTP_200_OK)

            cur.execute(sql_2)
            conn.commit()
        except Exception as e:
            logger.error(e)
            return Response({"res": 1, "errmsg": "服务器异常!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        cur.close()
        return Response({"res": 0}, status=status.HTTP_200_OK)

    @staticmethod
    def put(request):
        conn = connections['default']
        conn.ensure_connection()
        cur = conn.connection.cursor(cursor_factory=RealDictCursor)

        id_ = request.data.get('id', '')
        name = request.data.get('name', '')
        uuid = request.data.get('uuid')

        sql_0 = "select count(1) from wh_product where name = '{}' and uuid != '{}';".format(name, uuid)
        sql_1 = "select count(1) from wh_product where id = '{}' and uuid != '{}';".format(id_, uuid)
        sql_2 = "update wh_product set id = '{}', name = '{}' where uuid = '{}';".format(id_, name, uuid)

        try:
            cur.execute(sql_0)
            count = cur.fetchone()['count']
            if count:
                return Response({"res": 1, "errmsg": "此名称已存在!"}, status=status.HTTP_200_OK)
            cur.execute(sql_1)
            count = cur.fetchone()['count']
            if count:
                return Response({"res": 1, "errmsg": "此编码已存在!"}, status=status.HTTP_200_OK)

            cur.execute(sql_2)
            conn.commit()
        except Exception as e:
            logger.error(e)
            return Response({"res": 1, "errmsg": "服务器异常!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        cur.close()
        return Response({"res": 0}, status=status.HTTP_200_OK)

    @staticmethod
    def delete(request):
        conn = connections['default']
        conn.ensure_connection()
        cur = conn.connection.cursor(cursor_factory=RealDictCursor)

        uuid = request.data.get('uuid')

        sql = "delete from wh_product where uuid = '{}';".format(uuid)

        try:
            cur.execute(sql)
            conn.commit()
        except Exception as e:
            logger.error(e)
            return Response({"res": 1, "errmsg": "服务器异常!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        cur.close()
        return Response({"res": 0}, status=status.HTTP_200_OK)
