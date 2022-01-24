# -*- coding: utf-8 -*-

from odoo import api, fields, models


class XlaccountSpecialSigners(models.Model):
    _name = 'xlcrm.account.special.signers'
    code = fields.Char('收付款协议编码')
    name = fields.Char('收付款协议名称')
    date = fields.Char('建档日期')
    fd = fields.Integer('是否需要财务签核', default=0)
    lg = fields.Integer('是否需要财务签核', default=0)
    riskm = fields.Integer('是否需要财务签核', default=0)
    init_time = fields.Datetime(string='创建时间', default=lambda self: fields.Datetime.utc_now(self))
    init_user = fields.Many2one('xlcrm.users', store=True, string='创建者')
    update_time = fields.Datetime('更新时间')
    update_user = fields.Many2one('xlcrm.users', store=True, string='更新者')

    _sql_constraints = [
        ('union_uniq', 'unique (code)', "收付款协议编码已经存在!"),
    ]
