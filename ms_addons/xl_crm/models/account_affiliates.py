# -*- coding: utf-8 -*-

from odoo import api, fields, models


class AccountAffiliates(models.Model):
    _name = 'xlcrm.account.affiliates'
    code = fields.Char(string='客户代码')
    name = fields.Char(string='客户名称')
    account = fields.Many2one('xlcrm.account', store=True, string='ccf申请单')
