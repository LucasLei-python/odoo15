# -*- coding: utf-8 -*-
import connect_mssql

test_con = connect_mssql.Mssql('sales')
# print test_con.in_up_de(
#     "insert into dbo.BusinessTemplateMsg(templateType,userId,url,first,key1,key2)values('帐期额度申请单待审核通知', '雷辉，leihui@szsunray.com', 'www.baidu.com', 'test,hello world', 'lucas', '2020-06-29')")
# print test_con.in_up_de(
#     "insert into dbo.BusinessTemplateMsg(templateType,userId,url,first,key1,key2)values('%s','%s','%s','%s','%s','%s')" %
#     ("账期额度申请单待审核通知", '雷辉，leihui@szsunray.com', 'www.baidu.com', 'test,hello world', 'lucas', '2020-06-29'), )
# print test_con.query('select * from dbo.BusinessTemplateMsg where templateType=%s and userId=%s',
#                      ('账期额度申请单待审核通知', '雷辉，leihui@szsunray.com'))

print test_con.query("select top 1 * from V_DispatchLists_all")
test_con.close()
