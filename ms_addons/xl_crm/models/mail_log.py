# -*- coding: utf-8 -*-

from odoo import api, fields, models
import pytz,datetime


class Xlmaillog(models.Model):
    _name = 'xlcrm.maillogs'
    subject = fields.Char(string='主旨')
    content = fields.Char(string='内容')
    to_email = fields.Char(string='to')
    cc_email = fields.Char(string='cc')
    message = fields.Char(string='错误信息')
    code = fields.Integer(string='信息代码')
    init_time = fields.Datetime(string='更新时间', default=lambda self: fields.Datetime.now(self))
    # _sql_constraints = [
    #     ('review_title_uniq', 'unique (review_title)', "评审已经存在!"),
    # ]
