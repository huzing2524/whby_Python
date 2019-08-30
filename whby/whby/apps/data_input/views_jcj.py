import logging

from django.db import connections
from psycopg2.extras import RealDictCursor
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from permissions import DataInput

logger = logging.getLogger('django')


class DataInputPressRecords(APIView):
    permission_classes = [DataInput]

    @staticmethod
    def get(request):
        conn = connections['default']
        conn.ensure_connection()
        cur = conn.connection.cursor(cursor_factory=RealDictCursor)

        date = request.query_params.get('date')  # 2019-03
        schedule = request.query_params.get('schedule')

        sql = """
            select 
                t1.*,
                t2.name as schedule
            from 
                wh_press_record t1 
            left join 
                wh_schedules t2
            on 
                t1.schedule = t2.uuid
            where 
                to_char(date, 'yyyy-mm') = '{}' 
                and schedule = '{}' 
            order by 
                date desc;"""

        try:
            cur.execute(sql.format(date, schedule))
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

        data = dict(request.data)
        if 'output' in data:
            data['output'] = '{' + ','.join(str(i) for i in data['output']) + '}'
        if 'scrap' in data:
            data['scrap'] = '{' + ','.join(str(i) for i in data['scrap']) + '}'
        columns = ",".join(data.keys())
        values = ",".join(repr(i) for i in data.values())

        check_sql = "select count(1) from wh_press_record where date = '{}' and schedule = '{}';".format(data['date'],
                                                                                                         data['schedule'])
        sql = "insert into wh_press_record({}) values({});"

        try:
            cur.execute(check_sql)
            check = cur.fetchone()
            if check['count'] != 0:
                return Response({"res": 1, "errmsg": "相同日期和班次的记录已存在!"}, status=status.HTTP_200_OK)
            cur.execute(sql.format(columns, values))
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

        uuid = request.data.get('uuid')
        data = request.data.get('update')
        if 'output' in data:
            data['output'] = '{' + ','.join(str(i) for i in data['output']) + '}'
        if 'scrap' in data:
            data['scrap'] = '{' + ','.join(str(i) for i in data['scrap']) + '}'
        update = ",".join('{} = {}'.format(column, repr(value)) for column, value in data.items())

        check_sql = """
            select 
                count(1) 
            from 
                wh_press_record 
            where 
                date = '{}' and 
                schedule = '{}' 
                and uuid != '{}';
            """.format(data['date'], data['schedule'], uuid)
        sql = "update wh_press_record set {} where uuid = '{}';"

        try:
            cur.execute(check_sql)
            check = cur.fetchone()
            if check['count'] != 0:
                return Response({"res": 1, "errmsg": "相同日期和班次的记录已存在!"}, status=status.HTTP_200_OK)
            cur.execute(sql.format(update, uuid))
            conn.commit()
        except Exception as e:
            logger.error(e)
            return Response({"res": 1, "errmsg": "服务器异常!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        cur.close()
        return Response({"res": 0}, status=status.HTTP_200_OK)


class DataInputMaterialRecords(APIView):
    permission_classes = [DataInput]

    @staticmethod
    def get(request):
        conn = connections['default']
        conn.ensure_connection()
        cur = conn.connection.cursor(cursor_factory=RealDictCursor)

        date = request.query_params.get('date')  # 2019-03
        schedule = request.query_params.get('schedule')

        sql = """
            select 
                t1.*,
                t2.name as schedule
            from 
                wh_material_record t1 
            left join 
                wh_schedules t2
            on 
                t1.schedule = t2.uuid
            where 
                to_char(date, 'yyyy-mm') = '{}' 
                and schedule = '{}' 
            order by 
                date desc;"""

        try:
            cur.execute(sql.format(date, schedule))
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

        data = dict(request.data)
        if 'output' in data:
            data['output'] = '{' + ','.join(str(i) for i in data['output']) + '}'
        if 'scrap' in data:
            data['scrap'] = '{' + ','.join(str(i) for i in data['scrap']) + '}'
        columns = ",".join(data.keys())
        values = ",".join(repr(_) for _ in data.values())

        check_sql = "select count(1) from wh_material_record where date = '{}' and schedule = '{}';".format(data['date'],
                                                                                                         data['schedule'])
        sql = "insert into wh_material_record({}) values({});"

        try:
            cur.execute(check_sql)
            check = cur.fetchone()
            if check['count'] != 0:
                return Response({"res": 1, "errmsg": "相同日期和班次的记录已存在!"}, status=status.HTTP_200_OK)
            cur.execute(sql.format(columns, values))
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

        uuid = request.data.get('uuid')
        data = request.data.get('update')
        if 'output' in data:
            data['output'] = '{' + ','.join(str(i) for i in data['output']) + '}'
        if 'scrap' in data:
            data['scrap'] = '{' + ','.join(str(i) for i in data['scrap']) + '}'
        update = ",".join('{} = {}'.format(column, repr(value)) for column, value in data.items())

        check_sql = """
            select 
                count(1) 
            from 
                wh_material_record 
            where 
                date = '{}' and 
                schedule = '{}' 
                and uuid != '{}';
            """.format(data['date'], data['schedule'], uuid)
        sql = "update wh_material_record set {} where uuid = '{}';"

        try:
            cur.execute(check_sql)
            check = cur.fetchone()
            if check['count'] != 0:
                return Response({"res": 1, "errmsg": "相同日期和班次的记录已存在!"}, status=status.HTTP_200_OK)
            cur.execute(sql.format(update, uuid))
            conn.commit()
        except Exception as e:
            logger.error(e)
            return Response({"res": 1, "errmsg": "服务器异常!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        cur.close()
        return Response({"res": 0}, status=status.HTTP_200_OK)


class DataInputShutdownRecords(APIView):
    permission_classes = [DataInput]

    @staticmethod
    def get(request):
        conn = connections['default']
        conn.ensure_connection()
        cur = conn.connection.cursor(cursor_factory=RealDictCursor)

        date = request.query_params.get('date')  # 2019-03
        schedule = request.query_params.get('schedule')

        sql = """
            select 
                t1.*,
                t2.name as schedule
            from 
                wh_shutdown_record t1 
            left join 
                wh_schedules t2
            on 
                t1.schedule = t2.uuid
            where 
                to_char(date, 'yyyy-mm') = '{}' 
                and schedule = '{}' 
            order by 
                date desc;"""

        try:
            cur.execute(sql.format(date, schedule))
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

        data = dict(request.data)
        columns = ",".join(data.keys())
        values = ",".join(repr(i) for i in data.values())

        check_sql = "select count(1) from wh_shutdown_record where date = '{}' and schedule = '{}';".format(data['date'],
                                                                                                         data['schedule'])
        sql = "insert into wh_shutdown_record({}) values({});"

        try:
            cur.execute(check_sql)
            check = cur.fetchone()
            if check['count'] != 0:
                return Response({"res": 1, "errmsg": "相同日期和班次的记录已存在!"}, status=status.HTTP_200_OK)
            cur.execute(sql.format(columns, values))
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

        uuid = request.data.get('uuid')
        data = request.data.get('update')
        update = ",".join('{} = {}'.format(column, repr(value)) for column, value in data.items())

        check_sql = """
            select 
                count(1) 
            from 
                wh_shutdown_record 
            where 
                date = '{}' and 
                schedule = '{}' 
                and uuid != '{}';
            """.format(data['date'], data['schedule'], uuid)
        sql = "update wh_shutdown_record set {} where uuid = '{}';"

        try:
            cur.execute(check_sql)
            check = cur.fetchone()
            if check['count'] != 0:
                return Response({"res": 1, "errmsg": "相同日期和班次的记录已存在!"}, status=status.HTTP_200_OK)
            cur.execute(sql.format(update, uuid))
            conn.commit()
        except Exception as e:
            logger.error(e)
            return Response({"res": 1, "errmsg": "服务器异常!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        cur.close()
        return Response({"res": 0}, status=status.HTTP_200_OK)


class BoardShutdownStats(APIView):
    @staticmethod
    def get(request):
        conn = connections['default']
        conn.ensure_connection()
        cur = conn.connection.cursor(cursor_factory=RealDictCursor)

        start = request.query_params.get('start')  # 2019-03-01
        end = request.query_params.get('end')  # 2019-03-06
        schedule = request.query_params.get('schedule')

        if start.count('-') == 2:
            date_type = " date >= '{}' and date <= '{}' ".format(start, end)
        elif start.count('-') == 1:
            date_type = " date >= to_date('YYYY-MM', '{}') and date <= to_date('YYYY-MM', '{}') ".format(start, end)
        else:
            date_type = " date >= to_date('YYYY', '{}') and date <= to_date('YYYY', '{}') ".format(start, end)

        sql = """
            select 
                COALESCE(sum(total_time), 0) as total_time,
                COALESCE(sum(elec_device), 0) as elec_device, 
                COALESCE(sum(mach_device), 0) as mach_device,  
                COALESCE(sum(product), 0) as product,  
                COALESCE(sum(metal_alarm), 0) as metal_alarm,   
                COALESCE(sum(plan_check), 0) as plan_check,   
                COALESCE(sum(out_poweroff), 0) as out_poweroff,   
                COALESCE(sum(outsourcing), 0) as outsourcing,   
                COALESCE(sum(prevent_fire), 0) as prevent_fire,   
                COALESCE(sum(other), 0) as other
            from 
                wh_shutdown_record 
            where 
                {}
                and schedule = '{}';"""
        try:
            cur.execute(sql.format(date_type, schedule))
            result = cur.fetchone()
        except Exception as e:
            logger.error(e)
            return Response({"res": 1, "errmsg": "服务器异常!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        cur.close()
        return Response(result, status=status.HTTP_200_OK)
