# -*- coding: utf-8 -*-

from odoo import fields, models


class AccountCus(models.Model):
    _name = 'xlcrm.account.cus'
    review_id = fields.Many2one('xlcrm.account', store=True)
    paid_capital_unit = fields.Char(string='实缴资本单位')
    salesment_unit = fields.Char(string='销售资本单位')
    guarantee = fields.Char(string='是否有担保')
    registered_capital = fields.Char(string='注册资本')
    on_time = fields.Char(string='合同付款情况是否准时')
    overdue_others = fields.Char(string='实缴资本单位')
    listed_company = fields.Char(string='该客户是否是上市公司')
    payment_unit = fields.Char(string='实缴资本单位')
    paid_capital_currency = fields.Char(string='注册资本币种')
    stock = fields.Char(string='有无库存')
    registered_capital_currency = fields.Char(string='实缴资本单位')
    insured_persons = fields.Char(string='参保人数')
    paid_capital = fields.Char(string='实缴资本')
    trade_terms = fields.Char(string='贸易条款')
    payment = fields.Char(string='之前一年的销售和付款金额')
    payment_currency = fields.Char(string='之前一年的销售和付款金额币种')
    overdue60 = fields.Char(string='实缴资本单位')
    registered_capital_unit = fields.Char(string='实缴资本单位')
    payment_account = fields.Char(string='实缴资本单位')
    remark = fields.Char(string='备注')
    salesment_currency = fields.Char(string='之前一年的销售金额币种')
    overdue30 = fields.Char(string='实缴资本单位')
    salesment_account = fields.Char(string='实缴资本单位')
