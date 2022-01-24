# -*- coding: utf-8 -*-
import odoo
from odoo import models, fields, api, modules
import fcntl, datetime


class Cs(models.Model):
    _name = 'repair.cs'

    review_id = fields.Many2one('repair.baseinfo', string='review_id')
    repair = fields.Char(string='是否维修')
    charging_method = fields.Char(string='收费方式')
    charge_date = fields.Char(string='收费日期')
    maintenancea_mount = fields.Char(string='维修金额')
    charge_mount = fields.Char(string='收费金额')
    back_date = fields.Date(string='返品日期')
    reback = fields.Char(string='是否返还')
    remark = fields.Char(string='备注')


    init_user = fields.Many2one('xlcrm.users', store=True,
                                string='创建者')
    init_time = fields.Datetime(string='创建时间', default=lambda self: fields.Datetime.utc_now(self))
    update_user = fields.Many2one('xlcrm.users', store=True, string='更新者')
    customer_service = fields.Char(string='维修客服')
    update_time = fields.Datetime(string='更新时间', default=lambda self: fields.Datetime.utc_now(self))
    record_status = fields.Integer(string='提交状态', default=0)
