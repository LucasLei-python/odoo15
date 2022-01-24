# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ReportPoPm(models.Model):
    _name = 'report.popm'
    review_id = fields.Many2one('report.pobase', store=True, string='申请单据')
    apply_user = fields.Char(string='申请者')
    apply_date = fields.Date(string='申请时间')
    init_time = fields.Datetime(string='创建时间', default=lambda self: fields.Datetime.utc_now(self))
    init_user = fields.Many2one('xlcrm.users', store=True, string='创建者')
    update_time = fields.Datetime('更新时间')
    update_user = fields.Many2one('xlcrm.users', store=True, string='更新者')
    station_no = fields.Integer('签核站别')
    supplier_c = fields.Char('供应商（中文）')
    supplier_nature = fields.Char('供应商性质')
    supplier_e = fields.Char('供应商（英文）')
    account = fields.Char('账期')
    a_company = fields.Char('交易主体')
    amount = fields.Float('金额')
    avg_profit = fields.Float('平均利率')
    others = fields.Char('其他')
    content = fields.Char('PM备货填写')
    _sql_constraints = [
        ('review_id_uniq', 'unique (review_id,init_user)', "已经提交"),
    ]
