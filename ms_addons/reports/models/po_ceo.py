# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ReportPoCeo(models.Model):
    _name = 'report.poceo'
    review_id = fields.Many2one('reports.pobase', store=True, string='申请单据')
    init_time = fields.Datetime(string='创建时间', default=lambda self: fields.Datetime.utc_now(self))
    init_user = fields.Many2one('xlcrm.users', store=True, string='创建者')
    update_time = fields.Datetime('更新时间')
    update_user = fields.Many2one('xlcrm.users', store=True, string='更新者')
    station_no = fields.Integer('签核站别')
    content = fields.Char('ceo填写')
    _sql_constraints = [
        ('review_id_uniq', 'unique (review_id,init_user)', "已经提交"),
    ]
