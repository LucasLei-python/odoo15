# -*- coding: utf-8 -*-

from odoo import api, fields, models


class PoChangeLog(models.Model):
    _name = 'report.pochangelog'
    review_id = fields.Many2one('reports.pobase', store=True, string='申请单据')
    init_time = fields.Datetime(string='创建时间', default=lambda self: fields.Datetime.utc_now(self))
    init_user = fields.Many2one('xlcrm.users', store=True, string='创建者')
    cinvcode = fields.Char('存货编码')
    versions = fields.Char('版本号')
    old = fields.Integer('原数据')
    new = fields.Integer('更新后的数据')
