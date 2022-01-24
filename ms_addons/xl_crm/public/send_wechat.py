def send_wechat(subject, to_wechart, url, content, init_user, init_time):
    from . import connect_mssql
    wechart = connect_mssql.Mssql('wechart')
    send_wechart = wechart.in_up_de(
        "insert into dbo.BusinessTemplateMsg(templateType,userId,url,first,key1,key2)values('" + subject + "','" + to_wechart + "','" + url + "', '" + content + "', '" + init_user + "', '" + init_time + "')")

    return wechart if send_wechart else send_wechart