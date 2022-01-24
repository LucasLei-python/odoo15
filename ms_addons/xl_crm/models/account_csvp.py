# -*- coding: utf-8 -*-

from odoo import api, fields, models


class Xlaccountcsvp(models.Model):
    _name = 'xlcrm.account.csvp'
    review_id = fields.Many2one('xlcrm.account', store=True, string='申请单据')
    content=fields.Char('Sales说明')
    init_time = fields.Datetime(string='创建时间', default=lambda self: fields.Datetime.utc_now(self))
    init_user = fields.Many2one('xlcrm.users', store=True, string='创建者')
    update_time = fields.Datetime('更新时间')
    update_user = fields.Many2one('xlcrm.users', store=True, string='更新者')
    update_nickname = fields.Char(related='update_user.nickname', store=False, string='签核人昵称')
    station_no=fields.Integer('签核站别')

    _sql_constraints = [
        ('review_id_uniq', 'unique (review_id)', "已经提交"),
    ]
