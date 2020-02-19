import xlrd


def to_num(s):
    try:
        return round(float(s), 2)
    except ValueError:
        return 0


def read_batch(name):
    """
    制版生产日报表解析
    :return:
    """
    data = xlrd.open_workbook(name)
    table = data.sheets()[0]
    title = table.row_values(0)

    day = title.index('时间')
    schedule = title.index('班次')
    index1 = title.index('成品产量(m3)')
    index2 = title.index('废品产量(m3)')
    index3 = title.index('总刨花(T/m3)')
    index4 = title.index('MDI胶水(Kg/m3)')
    index5 = title.index('表芯层石蜡(Kg/m3)')
    index6 = title.index('表芯层增粘剂(Kg/m3)')
    index7 = title.index('脱模剂(Kg/m3)')

    all = {}
    schedule_dic = {}
    for r in range(1, table.nrows):
        if table.cell(r, 1).value:
            # k = str(int(table.cell(r, day).value)) + table.cell(r, schedule).value
            # 不区分班次
            all_k = int(table.cell(r, day).value)
            schedule_k = table.cell(r, schedule).value
            if not schedule_dic.get(schedule_k):
                schedule_dic[schedule_k] = {}
            schedule_data = schedule_dic.get(schedule_k)

            if schedule_data.get(all_k):
                data = all.get(all_k)
                i1 = to_num(table.cell(r, index1).value) + data[0]
                i2 = to_num(table.cell(r, index2).value) + data[1]
                i3 = to_num(table.cell(r, index3).value) + data[2]
                i4 = to_num(table.cell(r, index4).value) + data[3]
                i5 = to_num(table.cell(r, index5).value) + data[4]
                i6 = to_num(table.cell(r, index6).value) + data[5]
                i7 = to_num(table.cell(r, index6).value) + data[6]
                data = [i1, i2, i3, i4, i5, i6, i7]
                schedule_data[all_k] = [round(x, 2) for x in data]
            else:
                i1 = to_num(table.cell(r, index1).value)
                i2 = to_num(table.cell(r, index2).value)
                i3 = to_num(table.cell(r, index3).value)
                i4 = to_num(table.cell(r, index4).value)
                i5 = to_num(table.cell(r, index5).value)
                i6 = to_num(table.cell(r, index6).value)
                i7 = to_num(table.cell(r, index7).value)
                data = [i1, i2, i3, i4, i5, i6, i7]
                schedule_data[all_k] = [round(x, 2) for x in data]

            if all.get(all_k):
                data = all.get(all_k)
                i1 = to_num(table.cell(r, index1).value) + data[0]
                i2 = to_num(table.cell(r, index2).value) + data[1]
                i3 = to_num(table.cell(r, index3).value) + data[2]
                i4 = to_num(table.cell(r, index4).value) + data[3]
                i5 = to_num(table.cell(r, index5).value) + data[4]
                i6 = to_num(table.cell(r, index6).value) + data[5]
                i7 = to_num(table.cell(r, index6).value) + data[6]
                data = [i1, i2, i3, i4, i5, i6, i7]
                all[all_k] = [round(x, 2) for x in data]
            else:
                i1 = to_num(table.cell(r, index1).value)
                i2 = to_num(table.cell(r, index2).value)
                i3 = to_num(table.cell(r, index3).value)
                i4 = to_num(table.cell(r, index4).value)
                i5 = to_num(table.cell(r, index5).value)
                i6 = to_num(table.cell(r, index6).value)
                i7 = to_num(table.cell(r, index7).value)
                data = [i1, i2, i3, i4, i5, i6, i7]
                all[all_k] = [round(x, 2) for x in data]
    return all, schedule_dic


def read_quality(name):
    data = xlrd.open_workbook(name)
    table = data.sheets()[2]
    all_data = {}

    for r in range(3, table.nrows):
        schedule = table.cell(r, 3).value
        if schedule:
            schedule_data = all_data.get(schedule)
            row = table.row_values(r)
            (y, m, d, h, mm, s) = xlrd.xldate_as_tuple(table.cell(r, 2).value, 0)
            row[2] = d
            row = row[1:]
            if schedule_data:
                schedule_data.append(row)
            else:
                all_data[schedule] = [row]
    return all_data
