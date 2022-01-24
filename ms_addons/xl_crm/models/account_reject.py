# -*- coding: utf-8 -*-

from odoo import api, fields, models


class Xlaccountreject(models.Model):
    _name = 'xlcrm.account.reject'
    review_id = fields.Many2one('xlcrm.account', store=True, string='申请单据')
    reason = fields.Char('驳回原因')
    init_time = fields.Datetime(string='创建时间', default=lambda self: fields.Datetime.utc_now(self))
    init_user = fields.Many2one('xlcrm.users', store=True, string='创建者')
    station_no = fields.Integer('驳回站别')
