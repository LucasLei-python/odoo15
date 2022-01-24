# -*- coding: utf-8 -*-

from odoo import api, fields, models


class Xlaccount(models.Model):
    _name = 'report.purchase'
    version = fields.Char(string='版本号')
    cinvCode = fields.Char(string="cinvCode")
    HKST = fields.Integer(string='HKST')
    PL = fields.Char(string="PL")
    SO = fields.Integer(string='SO')
    SZST = fields.Integer(string='SZST')
    BGQty = fields.Integer(string='BGQty')
    cCusName = fields.Char(string="cCusName")
    PO = fields.Integer(string='PO')
    GAPQty = fields.Integer(string='GAPQty')
    cCusExch_name = fields.Char(string="cCusExch_name")
    init_time = fields.Datetime(string='创建时间', default=lambda self: fields.Datetime.utc_now(self))
    init_user = fields.Many2one('xlcrm.users', store=True, string='创建者')

    # _sql_constraints = [
    #     ('review_title_uniq', 'unique (review_title)', "评审已经存在!"),
    # ]
