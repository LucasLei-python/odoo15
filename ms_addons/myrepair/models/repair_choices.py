# -*- coding: utf-8 -*-
import odoo
from odoo import models, fields, api, modules
import fcntl, datetime


class Cs(models.Model):
    _name = 'repair.choices'
    uid = fields.Many2one('xlcrm.users', store=True,
                          string='创建者')
    columns = fields.Char(string='选择栏位')
    init_user = fields.Many2one('xlcrm.users', store=True,
                                string='创建者')
    init_time = fields.Datetime(string='创建时间', default=lambda self: fields.Datetime.utc_now(self))
    update_user = fields.Many2one('xlcrm.users', store=True, string='更新者')
    update_time = fields.Datetime(string='更新时间', default=lambda self: fields.Datetime.utc_now(self))
