# -*- coding: utf-8 -*-
import odoo
from odoo import models, fields, api, modules
import fcntl, datetime


class RepairPro(models.Model):
    _name = 'repair.products'

    ts_id = fields.Many2one('repair.testing', string='工程师ID')
    pro_no = fields.Char(string='配件存货名称')
    pro_name = fields.Char(string='产品名称')
    brand = fields.Char(string='品牌')
    count = fields.Char(string='数量')
    unit_price = fields.Char(string='单价')
    price = fields.Char(string='总价')
    remark = fields.Char(string='备注')

    init_user = fields.Many2one('xlcrm.users', store=True,
                                string='创建者')
    init_time = fields.Datetime(string='创建时间', default=lambda self: fields.Datetime.utc_now(self))
    update_user = fields.Many2one('xlcrm.users', store=True, string='更新者')
    update_time = fields.Datetime(string='更新时间', default=lambda self: fields.Datetime.utc_now(self))
