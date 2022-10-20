# -*- coding: utf-8 -*-

from ..controllers import controllers_base


class Public:

    def get_overdue(self, ccuscode, mssql):
        overdue = Overdue(ccuscode, mssql)
        return overdue.get_overdue()

    def get_payment(self, ccuscode, mssql):
        overdue = Overdue(ccuscode, mssql)
        return overdue.get_payment()


class Overdue(controllers_base.Base):
    def __init__(self, cus, mssql):
        self.cus = cus
        self.mssql = mssql

    def get_overdue(self):
        condition, ccuscode_temp = self.get_condition()
        sql = 'select companyName,b.dCusCreateDatetime,a.cName,sum(iSumYE2) as iSumYE2,a.cCusCode,a.cCusName,a.cexch_name,a.OrderType from dbo.V_GetAll_zlfx a '
        sql += "left join ErpCrmDB.dbo.v_Customer_CCF b on a.cCusCode=b.cCusCode and a.companyName=b.cCustype where dGatheringDate<=getdate() and a.ccusName in (%s) " % condition
        sql += "group by companyName,b.dCusCreateDatetime,a.cName,a.cCusCode,a.cCusName,a.cexch_name,a.OrderType"
        result = self.mssql.query(sql)
        discount_res = list(filter(lambda x: x[7] == '折扣销售', result))
        common_res = list(filter(lambda x: x[7] != '折扣销售', result))
        for res in common_res:
            tmp = {}
            tmp['companycodename'] = self.translation(res[0])
            tmp['dCusCreateDatetime'] = res[1]
            tmp['payDateRemark'] = res[2]
            tmp['ccusName'] = res[5]
            _res = list(filter(lambda x: x[0] == res[0] and x[5] == res[5], discount_res))
            discount = sum(list(map(lambda x: x[3], _res))) if _res else 0
            tmp['discount'] = '%.2f%s' % (discount, res[6])
            tmp['FaHuoChaiFeniSum'] = '%.2f%s' % (float(res[3]), res[6])
            ccuscode_temp[res[5]].append(tmp)

        overdue = [{'ccusName': item[0], 'data': item[1]} for item in
                   ccuscode_temp.items() if item[1]]
        return overdue

    def get_payment(self):
        try:
            condition, ccuscode_temp = self.get_condition()
            years = self.get_years()
            start, end = min(years), max(years)
            sql = "select distinct year(ddate) as year,month(ddate) as month, YuQiDays,cCusCode,ccusName,companycodename,dGatheringDate From v_sdo_so_customerReceivedPayment a " \
                  "where ccusName in (%s) and year(ddate) between %d and %d and FaHuoChaiFeniSum>0 and YuQiDays not in ('到期日不正确','未收款')  " \
                  "and not exists (select * from v_sdo_so_customerReceivedPayment b where b.ccusName in (%s) and a.cCusCode=b.cCusCode and a.companycodename=b.companycodename and convert(date,a.dGatheringDate) =convert(date,b.dGatheringDate) and b.YuQiDays not in ('到期日不正确','未收款') and b.FaHuoChaiFeniSum>0 and convert(int,a.YuQiDays)< convert(int,b.YuQiDays))" % (
                      condition, start, end, condition)
            result = self.mssql.query(sql)
            res_temp = []
            for res in result:
                tmp = {}
                tmp['year'] = res[0]
                tmp['month'] = res[1]
                tmp['YuQiDays'] = res[2]
                tmp['cCusCode'] = res[3]
                tmp['ccusName'] = self.translation(res[4])
                tmp['companycodename'] = self.translation(res[5])
                res_temp.append(tmp)
            payment = {}
            for cusname in ccuscode_temp:
                payment[cusname] = []
                for ca in set(map(lambda x: x['companycodename'],
                                  list(filter(lambda x: x['ccusName'] == cusname, res_temp)))):
                    for year in years:
                        data = list(filter(
                            lambda x: x['year'] == year and x['ccusName'] == cusname and x['companycodename'] == ca,
                            res_temp))
                        if data:
                            message = self._map(data)
                        else:
                            message = '无交易记录'
                        payment[cusname].append({'year': year, 'situation': message, 'companycodename': ca})
            payment = [{'ccusName': item[0], 'data': item[1]} for item in
                       payment.items()]
            return payment
        except Exception as e:
            raise Exception(str(e))

    def get_condition(self):
        index, condition = 0, ''
        ccuscode_temp = {}
        cus_name = set(map(lambda x: x['name'], self.cus))
        for name in cus_name:
            if name:
                ccuscode_temp[name] = []
                if condition:
                    condition += ",'%s'" % name
                else:
                    condition = "'%s'" % name
        return condition, ccuscode_temp

    def get_years(self):
        import datetime
        now = datetime.datetime.now().year
        return range(now - 3, now + 1)

    def get_cusname(self, code):
        cus_list = list(filter(lambda x: x['code'] == code, self.cus))
        return cus_list[0].get('name') if cus_list else ''

    def _map(self, data):
        message = []
        overdue29, overdue30, overdue60, overdue90 = self.__map_month(data)
        if overdue30 > 0 or overdue60 > 0 or overdue90 > 0:
            if overdue30 > 0:
                message.append('超期30天以上有（%d）次' % overdue30)
            if overdue60 > 0:
                message.append('超期60天以上有（%d）次' % overdue60)
            if overdue90 > 0:
                message.append('超期90天以上有（%d）次' % overdue90)
        elif overdue29 > 0:
            message.append('有逾期情况但无超30天记录')
        else:
            message.append('交易正常')
        return '；'.join(message)

    @staticmethod
    def __map_month(data):
        overdue29, overdue30, overdue60, overdue90 = 0, 0, 0, 0
        for mon in set(map(lambda x: x['month'], data)):
            overdue29_, overdue30_, overdue60_, overdue90_ = 0, 0, 0, 0
            for da in list(filter(lambda x: x['month'] == mon, data)):
                days = int(da['YuQiDays'])
                if days <= 0:
                    continue
                elif 0 < days < 30:
                    overdue29_ += 1
                elif days < 60:
                    overdue30_ += 1
                elif days < 90:
                    overdue60_ += 1
                else:
                    overdue90_ += 1

            if overdue90_ > 0:
                overdue90 += 1
            elif overdue60_ > 0:
                overdue60 += 1
            elif overdue30_ > 0:
                overdue30 += 1
            elif overdue29_ > 0:
                overdue29 += 1
        return overdue29, overdue30, overdue60, overdue90


def u8_account_name(code, enviroment):
    name = {
        'TEST': {
            "103": "UFDATA_103_2017",
            "601": "UFDATA_601_2017",
            "606": "UFDATA_606_2021",
            "101": "UFDATA_101_2017",
            "109": "UFDATA_109_2022",
            "110": "UFDATA_110_2021",
            "151": "UFDATA_151_2017",
            "602": "UFDATA_602_2017",
            "611": "UFDATA_611_2017",
            "201": "UFDATA_201_2017",
            "106": "UFDATA_106_2017",
            "108": "UFDATA_108_2017",
            "613": "UFDATA_613_2017",
            "133": "UFDATA_133_2017",
            "111": "UFDATA_111_2017",
            "999": "UFDATA_999_2017"
        },
        'PRODUCT': {
            '101': 'UFDATA_101_2017',
            '103': 'UFDATA_103_2017',
            '106': 'UFDATA_106_2017',
            '107': 'UFDATA_107_2022',
            '108': 'UFDATA_108_2017',
            '603': 'UFDATA_603_2017',
            '105': 'UFDATA_105_2018',
            '109': 'UFDATA_109_2022',
            '604': 'UFDATA_604_2017',
            '605': 'UFDATA_605_2022',
            '601': 'UFDATA_601_2017',
            '602': 'UFDATA_602_2017',
            '606': 'UFDATA_606_2021',
            '102': 'UFDATA_102_2017',
            "999": "UFDATA_999_2017"
        },
    }
    return name[enviroment][code]
