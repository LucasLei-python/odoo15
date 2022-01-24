# -*- coding: utf-8 -*-

from odoo import fields, models


class Xlwechatlog(models.Model):
    _name = 'xlcrm.wechatlogs'
    openid = fields.Char(string='openid')
    init_time = fields.Datetime(string='更新时间', default=lambda self: fields.Datetime.utc_now(self))
