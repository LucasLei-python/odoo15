# -*- coding: utf-8 -*-

from odoo import api, fields, models


class XlaccountSales(models.Model):
    _name = 'xlcrm.account.customer'
    review_id = fields.Many2one('xlcrm.account', store=True, string='申请单据')
    content = fields.Char('Sales说明')
    init_time = fields.Datetime(string='创建时间', default=lambda self: fields.Datetime.utc_now(self))
    init_user = fields.Many2one('xlcrm.users', store=True, string='创建者')
    update_time = fields.Datetime('更新时间')
    update_user = fields.Many2one('xlcrm.users', store=True, string='更新者')
    station_no = fields.Integer('签核站别')
    registered_capital = fields.Char('注册资本')
    # registered_capital_unit = fields.Char('注册资本单位')
    registered_capital_currency = fields.Char('注册资本币种')
    paid_capital = fields.Char('实缴资本')
    # paid_capital_unit = fields.Char('实缴资本单位')
    paid_capital_currency = fields.Char('实缴资本币种')
    insured_persons = fields.Char('参保人数')
    on_time = fields.Char('付款是否准时')
    overdue30 = fields.Char('超30天次数')
    overdue60 = fields.Char('超60天次数')
    overdue_others = fields.Char('其他超过天数')
    payment = fields.Char('销售和付款金额')
    payment_currency = fields.Char('付款币种')
    # payment_unit = fields.Char('付款金额单位')
    payment_account = fields.Char('付款金额')
    # salesment_unit = fields.Char('销售金额单位')
    salesment_currency = fields.Char('销售币种')
    salesment_account = fields.Char('销售金额')
    stock = fields.Char('有无库存')
    guarantee = fields.Char('有无担保')

    _sql_constraints = [
        ('review_id_uniq', 'unique (review_id)', "已经提交"),
    ]
