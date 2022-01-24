# -*- coding: utf-8 -*-

from odoo import api, fields, models


class XlaccountFd(models.Model):
    _name = 'xlcrm.account.fd'
    review_id = fields.Many2one('xlcrm.account', store=True, string='申请单据')
    content = fields.Char('Sales说明')
    init_time = fields.Datetime(string='创建时间', default=lambda self: fields.Datetime.utc_now(self))
    init_user = fields.Many2one('xlcrm.users', store=True, string='创建者')
    update_time = fields.Datetime('更新时间')
    update_user = fields.Many2one('xlcrm.users', store=True, string='更新者')
    station_no = fields.Integer('签核站别')
    payment_overdue = fields.Char('回款超期')
    overdue_days = fields.Char('超期天数')
    overdue_days_remark = fields.Char('超期天数说明')
    permit = fields.Char('开户许可证')
    permit_explain = fields.Char('无开户许可证说明')
    factoring = fields.Char('申请保理额度')
    factoring_limit = fields.Char('保理额度')
    factoring_explain = fields.Char('正在申请保理额度说明')
    _sql_constraints = [
        ('review_id_uniq', 'unique (review_id,init_user)', "已经提交"),
    ]
