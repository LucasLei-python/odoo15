# -*- coding: utf-8 -*-

from odoo import fields, models


class AccountCusHis(models.Model):
    _name = 'xlcrm.account.cus.his'
    # cus_id = fields.Many2one('xlcrm.account.cs', store=True)
    review_id = fields.Many2one('xlcrm.account', store=True)
    a_company = fields.Char(string='交易主体')
    salesment_account = fields.Char(string='之前一年的销售金额')
    salesment_currency = fields.Char(string='之前一年的销售金额币种')
    payment_account = fields.Char(string='之前一年的付款金额')
    payment_currency = fields.Char(string='之前一年的付款金额币种')
