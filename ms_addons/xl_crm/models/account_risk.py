# -*- coding: utf-8 -*-

from odoo import api, fields, models


class XlaccountRisk(models.Model):
    _name = 'xlcrm.account.risk'
    review_id = fields.Many2one('xlcrm.account', store=True, string='申请单据')
    content = fields.Char('Sales说明')
    init_time = fields.Datetime(string='创建时间', default=lambda self: fields.Datetime.utc_now(self))
    init_user = fields.Many2one('xlcrm.users', store=True, string='创建者')
    update_time = fields.Datetime('更新时间')
    update_user = fields.Many2one('xlcrm.users', store=True, string='更新者')
    station_no = fields.Integer('签核站别')
    overdue_arrears = fields.Char('有无超期贷款')
    contract = fields.Char('合同执行情况')
    others = fields.Char('其他')
    products_overdue = fields.Char('超期品牌')
    products_contract = fields.Char('不正常品牌')
    istrue = fields.Char('是否属实')
    istrue_remark = fields.Char('不属实备注说明')
    contract_remark = fields.Char('之前合同执行情况不正常备注说明')
    _sql_constraints = [
        ('review_id_uniq', 'unique (review_id,init_user)', "已经提交"),
    ]
