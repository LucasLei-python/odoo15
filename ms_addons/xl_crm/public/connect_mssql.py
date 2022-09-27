# -*- coding: utf-8 -*-


import pymssql, psycopg2


class Mssql(object):
    def __init__(self, dbselect):
        self.__connect(dbselect)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __connect(self, dbselect):
        dict_db = {
            "wechart": {
                'host': '192.168.0.159',
                'user': 'crm',
                'password': 'crm',
                'database': 'WecatDB',
                'port': 1433,
                'charset': 'utf8'
            },
            "sales": {
                'host': '192.168.0.154',
                'user': 'crm',
                'password': 'crm',
                'database': 'UFDATA_101_2017',
                'port': 1433,
                'charset': 'utf8'
            },
            "sales_": {
                'host': '192.168.0.154',
                'user': 'crm',
                'password': 'crm',
                'database': 'UFDATA_999_2017',
                'port': 1433,
                'charset': 'utf8'
            },
            "stock": {
                'host': '192.168.0.159',
                'user': 'crm',
                'password': 'crm',
                'database': 'SdoOdm',
                'port': 1433,
                'charset': 'utf8'
            },
            "ErpCrmDB": {
                'host': '192.168.0.159',
                'user': 'crm',
                'password': 'crm',
                'database': 'ErpCrmDB',
                'port': 1433,
                'charset': 'utf8'
            },
            "158_601": {
                'host': '192.168.0.158',
                'user': 'leihui',
                'password': 'leihui',
                'database': 'UFDATA_601_2017',
                'port': 1433,
                'charset': 'utf8'
            },
            "158_999": {
                'host': '192.168.0.158',
                'user': 'leihui',
                'password': 'leihui',
                'database': 'UFDATA_999_2017',
                'port': 1433,
                'charset': 'utf8'
            },
            "154_999": {
                'host': '192.168.0.154',
                'user': 'crm',
                'password': 'crm',
                'database': 'UFDATA_999_2017',
                'port': 1433,
                'charset': 'utf8'
            },
            "168": {
                'host': '192.168.0.168',
                'user': 'odoosunray',
                'password': '111111',
                'database': 'odoosunray',
                'port': 5432,
            },
            "161": {
                'host': '192.168.0.161',
                'user': 'odoosunray',
                'password': '111111',
                'database': 'odoosunray',
                'port': 5432
            }
        }
        condb = psycopg2 if dbselect in ('168', '161') else pymssql
        self.__db = condb.connect(**dict_db[dbselect])

    # 查询
    def query(self, sql, list_paramers=None, size=None):
        """
        ex:sql=select *from test where id=%s
           list_paramenrs=[15]
        :param sql: 需执行的sql语句
        :param list_paramers: 参数集合，可不传
        :return: 成功返回元祖结果或空，否则返回失败以及失败原因
        """
        self.__cur = self.__db.cursor()
        try:
            self.__cur.execute(sql, list_paramers)
            if size:
                return self.__cur.fetchmany(size=size)
            return self.__cur.fetchall()
        except Exception as e:
            return "查询失败：" + str(e)

    # 增、删、改
    def in_up_de(self, sql, list_paramers=None, ):
        """
            单笔增、删、改方法
        :param sql:
        :param list_paramers: 参数集合，可不传,mssql 如果list_paramers含中文可能会插入后中文乱码
        :return: 成功返回操作成功，失败返回操作失败
        """
        self.__cur = self.__db.cursor()
        try:
            self.__cur.execute(sql, list_paramers)
            return True
        except Exception as e:
            self.__db.rollback()
            return False

    # 批量多次增、删、改不同语句类型
    def batch_in_up_de(self, sql_list):
        """
        ex:my01.batch_in_up_de([["update person set id=%s where id=%s",
                         [(10, 1), (20, 2)]],["delete from person where id=%s",
                                              [1, 2]]])
        :param sql_list: 同一类型语句的二维列表，
        :return: 成功返回操作成功，失败返回操作失败
        """
        self.__cur = self.__db.cursor()
        try:
            for sql in sql_list:
                self.__cur.executemany(sql[0], sql[1])
            return True
        except Exception as e:
            self.__db.rollback()
            # raise repr(e)

    def close(self):
        if hasattr(self, "__cur"):
            self.__cur.close()
        if hasattr(self, "__db"):
            self.__db.close()

    def commit(self):
        self.__db.commit()

    def __del__(self):
        self.close()
