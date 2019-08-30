from django.shortcuts import render

# Create your views here.

import logging

from django.db import connection, transaction
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from permissions import DataInput

logger = logging.getLogger('django')


class SandingSawing(APIView):
    """砂光锯切记录 data/input/sanding_sawing"""
    permission_classes = [DataInput]

    def get(self, request):
        schedule = request.query_params.get("schedule")
        date = request.query_params.get("date")

        if schedule and not date:
            condition = " where t1_schedule = '{}' ".format(schedule)
        elif not schedule and date:
            condition = " where month = '{}' ".format(date)
        elif schedule and date:
            condition = " where t1_schedule = '{}' and month = '{}' ".format(schedule, date)
        else:
            condition = ""

        sql = """
        select *
        from (
               select p1.*, p2.name
               from (
                      select to_char(t1.date, 'yyyy-mm')   as month,
                             t1.date                       as t1_date,
                             t1.schedule as t1_schedule,
                             coalesce(t1.working_time, '') as working_time,
                             coalesce(t1.recorder, '')     as recorder,
                             coalesce(t1.reviewer, '')     as reviewer,
                             t2.*,
                             t1.uuid
                      from wh_sanding_sawing t1
                             left join
                           (
                             select date                      as t2_date,
                                    schedule                  as t2_schedule,
                                    array_agg(type)           as type,
                                    array_agg(stack_number)   as stack_number,
                                    array_agg(class)          as class,
                                    array_agg(specification1) as specification1,
                                    array_agg(specification2) as specification2,
                                    array_agg(specification3) as specification3,
                                    array_agg(count)          as count,
                                    array_agg(sanding_amount) as sanding_amount
                             from wh_sanding_sawing_data
                             group by date, schedule
                           ) t2
                           on
                             t1.date = t2.t2_date and t1.schedule = t2.t2_schedule
                    ) p1
                      left join wh_schedules p2 on p1.t1_schedule = p2.uuid
             ) t """ + condition + """
        order by t1_date desc;
        """

        cursor = connection.cursor()

        try:
            cursor.execute(sql)
            result = cursor.fetchall()
            data = list()
            for res in result:
                di, sanding, sawing, sum_sanding_count, sum_sanding_amount, sum_sawing_count, sum_sawing_amount = \
                    dict(), list(), list(), 0, 0, 0, 0
                di["date"], di["working_time"], di["recorder"], di["reviewer"], di["uuid"], di["schedule"] = res[1], \
                    res[3], res[4], res[5], res[-2], res[-1] if res[-1] else ""

                type_, stack_number, class_, specification1, specification2, specification3, count, sanding_amount = \
                    res[8] or [], res[9] or [], res[10] or [], res[11] or [], res[12] or [], res[13] or [], \
                    res[14] or [], res[15] or []
                combine_list = list(zip(type_, stack_number, class_, specification1, specification2, specification3,
                                        count, sanding_amount))
                for com in combine_list:
                    dt = dict()
                    dt["stack_number"], dt["class"], dt["specification1"], dt["specification2"], dt["specification3"], \
                        dt["count"], dt["sanding_amount"] = com[1] or "", com[2] or "", round(com[3], 2) or 0, \
                        round(com[4], 2) or 0, round(com[5], 2) or 0, round(com[6], 2) or 0, round(com[7], 2) or 0

                    if com[0] == "sanding":
                        sum_sanding_count += dt["count"]
                        sum_sanding_amount += dt["sanding_amount"]
                        sanding.append(dt)
                    else:
                        sum_sawing_count += dt["count"]
                        sum_sawing_amount += dt["sanding_amount"]
                        sawing.append(dt)
                di["sum_sanding_count"], di["sum_sanding_amount"], di["sum_sawing_count"], di["sum_sawing_amount"] = \
                    round(sum_sanding_count, 2), round(sum_sanding_amount, 2), round(sum_sawing_count, 2), \
                    round(sum_sawing_amount, 2)
                di["sanding"], di["sawing"] = sanding, sawing
                data.append(di)
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(e)
            return Response({"res": 1, "errmsg": "服务器错误！"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            cursor.close()

    def post(self, request):
        date = request.data.get("date")
        schedule = request.data.get("schedule")
        working_time = request.data.get("working_time")
        recorder = request.data.get("recorder")
        reviewer = request.data.get("reviewer")
        sanding = request.data.get("sanding", list())
        sawing = request.data.get("sawing", list())

        if not all([date, schedule, working_time, recorder, reviewer, sanding, sawing]):
            return Response({"res": 1, "errmsg": "缺少参数！"}, status=status.HTTP_200_OK)
        if not isinstance(sanding, list) or not isinstance(sawing, list):
            return Response({"res": 1, "errmsg": "sanding/sawing参数类型错误！"}, status=status.HTTP_200_OK)
        if date.count("-") != 2:
            return Response({"res": 1, "errmsg": "date参数格式错误！"}, status=status.HTTP_200_OK)
        if working_time not in ["早", "中", "晚"]:
            return Response({"res": 1, "errmsg": "working_time参数错误！"}, status=status.HTTP_200_OK)

        sql = """
        insert into
          wh_sanding_sawing_data (date, schedule, type, stack_number, class, specification1, specification2, specification3, 
          count, sanding_amount) 
        values
          ('%s', '%s', '%s', '%s', '%s', %f, %f, %f, %f, %f);
        """

        for d in sanding:
            if not d:
                return Response({"res": 1, "errmsg": "参数错误！"}, status=status.HTTP_200_OK)
            if "specification1" not in d or "specification2" not in d or "specification3" not in d \
                    or "count" not in d or "sanding_amount" not in d:
                return Response({"res": 1, "errmsg": "缺少参数！"}, status=status.HTTP_200_OK)
            if not d["specification1"] or not d["specification2"] or not d["specification3"] or not d["count"] \
                    or not d["sanding_amount"]:
                return Response({"res": 1, "errmsg": "请完善信息！"}, status=status.HTTP_200_OK)
            if d["specification1"].isalpha() or d["specification2"].isalpha() or \
                    d["specification3"].isalpha() or d["count"].isalpha() or d["sanding_amount"].isalpha():
                return Response({"res": 1, "errmsg": "请填写数字！"}, status=status.HTTP_200_OK)
        for w in sawing:
            if not w:
                return Response({"res": 1, "errmsg": "参数错误！"}, status=status.HTTP_200_OK)
            if "specification1" not in w or "specification2" not in w or "specification3" not in w \
                    or "count" not in w or "sanding_amount" not in w:
                return Response({"res": 1, "errmsg": "缺少参数！"}, status=status.HTTP_200_OK)
            if not w["specification1"] or not w["specification2"] or not w["specification3"] or not w["count"] \
                    or not w["sanding_amount"]:
                return Response({"res": 1, "errmsg": "请完善信息！"}, status=status.HTTP_200_OK)
            if w["specification1"].isalpha() or w["specification2"].isalpha() or \
                    w["specification3"].isalpha() or w["count"].isalpha() or w["sanding_amount"].isalpha():
                return Response({"res": 1, "errmsg": "请填写数字！"}, status=status.HTTP_200_OK)

        cursor = connection.cursor()

        try:
            cursor.execute(
                "select count(*) from wh_sanding_sawing where date = '{}' and schedule = '{}';".format(date, schedule))
            date_check = cursor.fetchone()[0]
            if date_check >= 1:
                return Response({"res": 1, "errmsg": "该日期数据已存在！"}, status=status.HTTP_200_OK)

            with transaction.atomic():
                cursor.execute("insert into wh_sanding_sawing (date, schedule, working_time, recorder, reviewer) "
                               "values ('{}', '{}', '{}', '{}', '{}');".format(date, schedule, working_time, recorder,
                                                                               reviewer))

                for d in sanding:
                    cursor.execute(sql % (date, schedule, "sanding", d["stack_number"], d["class"] or "",
                                          float(d["specification1"]), float(d["specification2"]),
                                          float(d["specification3"]), float(d["count"]), float(d["sanding_amount"])))
                for w in sawing:
                    cursor.execute(sql % (date, schedule, "sawing", w["stack_number"], w["class"] or "",
                                          float(w["specification1"]), float(w["specification2"]),
                                          float(w["specification3"]), float(w["count"]), float(w["sanding_amount"])))

            connection.commit()
            return Response({"res": 0}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(e)
            return Response({"res": 1, "errmsg": "服务器错误！"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            cursor.close()

    def put(self, request):
        uuid = request.data.get("uuid")
        date = request.data.get("date")
        schedule = request.data.get("schedule")
        working_time = request.data.get("working_time")
        recorder = request.data.get("recorder")
        reviewer = request.data.get("reviewer")
        sanding = request.data.get("sanding", list())
        sawing = request.data.get("sawing", list())

        if not all([uuid, date, schedule, working_time, recorder, reviewer, sanding, sawing]):
            return Response({"res": 1, "errmsg": "缺少参数！"}, status=status.HTTP_200_OK)
        if not isinstance(sanding, list) or not isinstance(sawing, list):
            return Response({"res": 1, "errmsg": "sanding/sawing参数类型错误！"}, status=status.HTTP_200_OK)
        if date.count("-") != 2:
            return Response({"res": 1, "errmsg": "date参数格式错误！"}, status=status.HTTP_200_OK)
        if working_time not in ["早", "中", "晚"]:
            return Response({"res": 1, "errmsg": "working_time参数错误！"}, status=status.HTTP_200_OK)

        sql = """
        update
          wh_sanding_sawing
        set
          date = '%s', schedule = '%s', working_time = '%s', recorder = '%s', reviewer = '%s'
        where 
          uuid = '%s';
        """

        sql_1 = """
        insert into
          wh_sanding_sawing_data (date, schedule, type, stack_number, class, specification1, specification2, 
          specification3, count, sanding_amount) 
        values
          ('%s', '%s', '%s', '%s', '%s', %f, %f, %f, %f, %f);
        """

        cursor = connection.cursor()

        for d in sanding:
            if not d:
                return Response({"res": 1, "errmsg": "参数错误！"}, status=status.HTTP_200_OK)
            if "specification1" not in d or "specification2" not in d or "specification3" not in d \
                    or "count" not in d or "sanding_amount" not in d:
                return Response({"res": 1, "errmsg": "缺少参数！"}, status=status.HTTP_200_OK)
            if not d["specification1"] or not d["specification2"] or not d["specification3"] or not d["count"] \
                    or not d["sanding_amount"]:
                return Response({"res": 1, "errmsg": "请完善信息！"}, status=status.HTTP_200_OK)
            if str(d["specification1"]).isalpha() or str(d["specification2"]).isalpha() or \
                    str(d["specification3"]).isalpha() or str(d["count"]).isalpha() or \
                    str(d["sanding_amount"]).isalpha():
                return Response({"res": 1, "errmsg": "请填写数字！"}, status=status.HTTP_200_OK)
        for w in sawing:
            if not w:
                return Response({"res": 1, "errmsg": "参数错误！"}, status=status.HTTP_200_OK)
            if "specification1" not in w or "specification2" not in w or "specification3" not in w \
                    or "count" not in w or "sanding_amount" not in w:
                return Response({"res": 1, "errmsg": "缺少参数！"}, status=status.HTTP_200_OK)
            if not w["specification1"] or not w["specification2"] or not w["specification3"] or not w["count"] \
                    or not w["sanding_amount"]:
                return Response({"res": 1, "errmsg": "请完善信息！"}, status=status.HTTP_200_OK)
            if str(w["specification1"]).isalpha() or str(w["specification2"]).isalpha() or \
                    str(w["specification3"]).isalpha() or str(w["count"]).isalpha() or \
                    str(w["sanding_amount"]).isalpha():
                return Response({"res": 1, "errmsg": "请填写数字！"}, status=status.HTTP_200_OK)

        try:
            cursor.execute("select count(*) from wh_sanding_sawing where uuid = '{}';".format(uuid))
            uuid_check = cursor.fetchone()[0]
            if uuid_check <= 0:
                return Response({"res": 1, "errmsg": "此uuid不存在！"}, status=status.HTTP_200_OK)

            cursor.execute(
                "select count(*) from wh_sanding_sawing where date = '{}' and schedule = '{}' and uuid != '{}';".format
                (date, schedule, uuid))
            date_check = cursor.fetchone()[0]
            if date_check >= 1:
                return Response({"res": 1, "errmsg": "该日期数据已存在！"}, status=status.HTTP_200_OK)

            with transaction.atomic():
                cursor.execute("select date, schedule from wh_sanding_sawing where uuid = '{}';".format(uuid))
                old_date, old_schedule = cursor.fetchone()

                cursor.execute(sql % (date, schedule, working_time, recorder, reviewer, uuid))
                cursor.execute("delete from wh_sanding_sawing_data where date = '{}' and schedule = '{}';".format(
                    old_date, old_schedule))
                for d in sanding:
                    cursor.execute(sql_1 % (date, schedule, "sanding", d["stack_number"], d["class"] or "",
                                            float(d["specification1"]), float(d["specification2"]),
                                            float(d["specification3"]), float(d["count"]), float(d["sanding_amount"])))
                for w in sawing:
                    cursor.execute(sql_1 % (date, schedule, "sawing", w["stack_number"], w["class"] or "",
                                            float(w["specification1"]), float(w["specification2"]),
                                            float(w["specification3"]), float(w["count"]), float(w["sanding_amount"])))

            connection.commit()
            return Response({"res": 0}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(e)
            return Response({"res": 1, "errmsg": "服务器错误！"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            cursor.close()


class PressOperation(APIView):
    """压机操作记录 data/input/press_operation"""
    permission_classes = [DataInput]

    def get(self, request):
        schedule = request.query_params.get("schedule")
        date = request.query_params.get("date")

        if schedule and not date:
            condition = " where schedule = '{}' ".format(schedule)
        elif not schedule and date:
            condition = " where month = '{}' ".format(date)
        elif schedule and date:
            condition = " where schedule = '{}' and month = '{}' ".format(schedule, date)
        else:
            condition = ""

        sql = """
        select *
        from (
               select to_char(t1.date, 'yyyy-mm')   as month,
                      coalesce(t1.schedule, '')     as schedule,
                      coalesce(t1.working_time, '') as working_time,
                      coalesce(t1.operator, '')     as operator,
                      coalesce(t1.reviewer, '')     as reviewer,
                      t1.uuid,
                      t2.date, t2.time, t2.content, t2.name
               from wh_press_operation t1
                      left join
                    (
                      select p1.*, p2.name
                      from (select date,
                                   schedule,
                                   array_agg(coalesce(time, ''))    as time,
                                   array_agg(coalesce(content, '')) as content
                            from wh_press_operation_data
                            group by date, schedule) p1
                             left join wh_schedules p2 on p1.schedule = p2.uuid
                    ) t2 on t1.date = t2.date and t1.schedule = t2.schedule
             ) t """ + condition + """
        order by date desc;
        """

        cursor = connection.cursor()

        try:
            cursor.execute(sql)
            result = cursor.fetchall()
            data = list()
            for res in result:
                di, data_inner = dict(), list()
                di["date"], di["working_time"], di["operator"], di["reviewer"], di["uuid"], di["schedule"],  = res[6], \
                    res[2], res[3], res[4], res[5], res[-1]

                time, content = res[7] or [], res[8] or []
                combine_list = list(zip(time, content))
                for com in combine_list:
                    dt = dict()
                    dt["time"], dt["content"] = com[0], com[1]
                    data_inner.append(dt)
                di["data"] = data_inner
                data.append(di)

            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(e)
            return Response({"res": 1, "errmsg": "服务器错误！"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            cursor.close()

    def post(self, request):
        date = request.data.get("date")
        schedule = request.data.get("schedule")
        working_time = request.data.get("working_time")
        operator = request.data.get("operator")
        reviewer = request.data.get("reviewer")
        data = request.data.get("data", list())

        if not all([date, schedule, working_time, operator, reviewer, data]):
            return Response({"res": 1, "errmsg": "缺少参数！"}, status=status.HTTP_200_OK)
        if not isinstance(data, list):
            return Response({"res": 1, "errmsg": "data参数类型错误！"}, status=status.HTTP_200_OK)
        if date.count("-") != 2:
            return Response({"res": 1, "errmsg": "date参数格式错误！"}, status=status.HTTP_200_OK)
        if working_time not in ["早", "中", "晚"]:
            return Response({"res": 1, "errmsg": "working_time参数错误！"}, status=status.HTTP_200_OK)

        sql = """
        insert into
          wh_press_operation_data (date, schedule, time, content) 
        values 
          ('%s', '%s', '%s', '%s');
        """

        cursor = connection.cursor()

        try:
            cursor.execute(
                "select count(*) from wh_press_operation where date = '%s' and schedule = '%s';" % (date, schedule))
            date_check = cursor.fetchone()[0]
            if date_check >= 1:
                return Response({"res": 1, "errmsg": "该日期数据已存在！"}, status=status.HTTP_200_OK)

            with transaction.atomic():
                cursor.execute("insert into wh_press_operation (date, schedule, working_time, operator, reviewer) "
                               "values ('%s', '%s', '%s', '%s', '%s');" % (date, schedule, working_time, operator,
                                                                           reviewer))

                for d in data:
                    cursor.execute(sql % (date, schedule, d["time"], d["content"]))
            connection.commit()
            return Response({"res": 0}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(e)
            return Response({"res": 1, "errmsg": "服务器错误！"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            cursor.close()

    def put(self, request):
        uuid = request.data.get("uuid")
        date = request.data.get("date")
        schedule = request.data.get("schedule")
        working_time = request.data.get("working_time")
        operator = request.data.get("operator")
        reviewer = request.data.get("reviewer")
        data = request.data.get("data", list())

        if not all([uuid, date, schedule, working_time, operator, reviewer, data]):
            return Response({"res": 1, "errmsg": "缺少参数！"}, status=status.HTTP_200_OK)
        if not isinstance(data, list):
            return Response({"res": 1, "errmsg": "data参数类型错误！"}, status=status.HTTP_200_OK)
        if date.count("-") != 2:
            return Response({"res": 1, "errmsg": "date参数格式错误！"}, status=status.HTTP_200_OK)
        if working_time not in ["早", "中", "晚"]:
            return Response({"res": 1, "errmsg": "working_time参数错误！"}, status=status.HTTP_200_OK)

        sql = """
        insert into
          wh_press_operation_data (date, time, content, schedule) 
        values 
          ('%s', '%s', '%s', '%s');
        """

        cursor = connection.cursor()

        try:
            cursor.execute("select count(*) from wh_press_operation where uuid = '{}';".format(uuid))
            uuid_check = cursor.fetchone()[0]
            if uuid_check <= 0:
                return Response({"res": 1, "errmsg": "此uuid不存在！"}, status=status.HTTP_200_OK)

            cursor.execute(
                "select count(*) from wh_press_operation where date = '%s' and schedule = '%s' and uuid != '%s';" %
                (date, schedule, uuid))
            date_check = cursor.fetchone()[0]
            if date_check >= 1:
                return Response({"res": 1, "errmsg": "此日期数据已存在！"}, status=status.HTTP_200_OK)

            with transaction.atomic():
                cursor.execute("select date, schedule from wh_press_operation where uuid = '{}';".format(uuid))
                old_date, old_schedule = cursor.fetchone()
                cursor.execute("delete from wh_press_operation_data where date = '{}' and schedule = '{}';".format(
                    old_date, old_schedule))

                cursor.execute("update wh_press_operation set date = '%s', schedule = '%s', working_time = '%s', "
                               "operator = '%s', reviewer = '%s' where uuid = '%s';" % (date, schedule, working_time,
                                                                                        operator, reviewer, uuid))

                for d in data:
                    cursor.execute(sql % (date, d["time"], d["content"], schedule))

            connection.commit()
            return Response({"res": 0}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(e)
            return Response({"res": 1, "errmsg": "服务器错误！"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            cursor.close()


class MaterialConsumption(APIView):
    """物资消耗 data/input/material_consumption"""
    permission_classes = [DataInput]

    def get(self, request):
        schedule = request.query_params.get("schedule")
        date = request.query_params.get("date")

        if schedule and not date:
            condition = " where schedule = '{}' ".format(schedule)
        elif not schedule and date:
            condition = " where month = '{}' ".format(date)
        elif schedule and date:
            condition = " where schedule = '{}' and month = '{}' ".format(schedule, date)
        else:
            condition = ""

        sql = """
        select *
        from (
               select to_char(t1.date, 'yyyy-mm')      as month,
                      t1.date,
                      t1.schedule,
                      t1.working_time,
                      coalesce(t1.fuel, 0)                as fuel,
                      coalesce(t1.glue, 0)                as glue,
                      coalesce(t1.waterproofing_agent, 0) as waterproofing_agent,
                      coalesce(t1.power_consumption, 0)   as power_consumption,
                      coalesce(t1.abrasive_belt, 0)       as abrasive_belt,
                      coalesce(t1.shaving_blade, 0)       as shaving_blade,
                      coalesce(t2.name, '')            as schedule_name,
                      t1.uuid
               from wh_material_consumption t1
                      left join
                    wh_schedules t2
                    on t1.schedule = t2.uuid) t """ + condition + """
        order by date desc;
        """

        cursor = connection.cursor()

        try:
            cursor.execute(sql)
            result = cursor.fetchall()
            data = list()
            for res in result:
                di = dict()
                di["date"] = res[1]
                di["working_time"] = res[3]
                di["fuel"] = round(res[4], 2)
                di["glue"] = round(res[5], 2)
                di["waterproofing_agent"] = round(res[6], 2)
                di["power_consumption"] = round(res[7], 2)
                di["abrasive_belt"] = round(res[8], 2)
                di["shaving_blade"] = round(res[9], 2)
                di["schedule"] = res[10]
                di["uuid"] = res[11]

                data.append(di)
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(e)
            return Response({"res": 1, "errmsg": "服务器错误！"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            cursor.close()

    def put(self, request):
        uuid = request.data.get("uuid")
        date = request.data.get("date")
        schedule = request.data.get("schedule")
        working_time = request.data.get("working_time")
        fuel = request.data.get("fuel")
        glue = request.data.get("glue")
        waterproofing_agent = request.data.get("waterproofing_agent")
        power_consumption = request.data.get("power_consumption")
        abrasive_belt = request.data.get("abrasive_belt")
        shaving_blade = request.data.get("shaving_blade")

        if not all([uuid, date, schedule, working_time, fuel, glue, waterproofing_agent, power_consumption,
                    abrasive_belt, shaving_blade]):
            return Response({"res": 1, "errmsg": "缺少参数！"}, status=status.HTTP_200_OK)
        if date.count("-") != 2:
            return Response({"res": 1, "errmsg": "date参数格式错误！"}, status=status.HTTP_200_OK)
        if working_time not in ["早", "中", "晚"]:
            return Response({"res": 1, "errmsg": "working_time参数错误！"}, status=status.HTTP_200_OK)

        cursor = connection.cursor()

        sql = """
        update
          wh_material_consumption
        set
          date = '%s', schedule = '%s', working_time = '%s', fuel = '%f', glue = '%f', waterproofing_agent = '%f', 
          power_consumption = '%f', abrasive_belt = '%f', shaving_blade = '%f'
        where 
          uuid = '%s';
        """

        try:
            cursor.execute("select count(*) from wh_material_consumption where uuid = '%s';" % uuid)
            uuid_check = cursor.fetchone()[0]
            if uuid_check <= 0:
                return Response({"res": 1, "errmsg": "此uuid不存在！"}, status=status.HTTP_200_OK)

            cursor.execute("select count(*) from wh_material_consumption where date = '%s' and schedule = '%s' "
                           "and uuid != '%s';" % (date, schedule, uuid))
            date_check = cursor.fetchone()[0]
            if date_check >= 1:
                return Response({"res": 1, "errmsg": "此日期数据已存在！"}, status=status.HTTP_200_OK)

            cursor.execute(sql % (date, schedule, working_time, fuel, glue, waterproofing_agent, power_consumption,
                                  abrasive_belt, shaving_blade, uuid))
            connection.commit()

            return Response({"res": 0}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(e)
            return Response({"res": 1, "errmsg": "服务器错误！"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            cursor.close()

    def post(self, request):
        date = request.data.get("date")
        schedule = request.data.get("schedule")
        working_time = request.data.get("working_time")
        fuel = request.data.get("fuel")
        glue = request.data.get("glue")
        waterproofing_agent = request.data.get("waterproofing_agent")
        power_consumption = request.data.get("power_consumption")
        abrasive_belt = request.data.get("abrasive_belt")
        shaving_blade = request.data.get("shaving_blade")

        if not all([date, schedule, working_time, fuel, glue, waterproofing_agent, power_consumption, abrasive_belt,
                    shaving_blade]):
            return Response({"res": 1, "errmsg": "缺少参数！"}, status=status.HTTP_200_OK)
        if date.count("-") != 2:
            return Response({"res": 1, "errmsg": "date参数格式错误！"}, status=status.HTTP_200_OK)
        if working_time not in ["早", "中", "晚"]:
            return Response({"res": 1, "errmsg": "working_time参数错误！"}, status=status.HTTP_200_OK)

        cursor = connection.cursor()

        sql = """
        insert into
          wh_material_consumption (date, schedule, working_time, fuel, glue, waterproofing_agent, power_consumption, 
          abrasive_belt, shaving_blade)
        values 
          ('%s', '%s', '%s', '%f', '%f', '%f', '%f', '%f', '%f');
        """

        try:
            cursor.execute("select count(*) from wh_material_consumption where date = '%s' and schedule = '%s';" %
                           (date, schedule))
            date_check = cursor.fetchone()[0]
            if date_check >= 1:
                return Response({"res": 1, "errmsg": "此日期数据已存在！"}, status=status.HTTP_200_OK)

            cursor.execute(sql % (date, schedule, working_time, fuel, glue, waterproofing_agent, power_consumption,
                                  abrasive_belt, shaving_blade))
            connection.commit()

            return Response({"res": 0}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(e)
            return Response({"res": 1, "errmsg": "服务器错误！"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            cursor.close()
