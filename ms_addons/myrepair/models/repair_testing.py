# -*- coding: utf-8 -*-
import odoo
from odoo import models, fields, api, modules
import fcntl, datetime


class Testing(models.Model):
    _name = 'repair.testing'

    review_id = fields.Many2one('repair.baseinfo', string='review_id')
    engineer = fields.Char(string='维修工程师')
    functional_testing = fields.Char(string='功能测试')
    test_date = fields.Date(string='检测日期')
    led_display = fields.Char(string='LED显示')
    appearance = fields.Char(string='外观')
    reproducibility = fields.Char(string='再现性')
    alarm_record = fields.Char(string='报警记录')
    result = fields.Char(string='检查结果说明')
    analysis = fields.Char(string='故障分析')
    repair_content = fields.Char(string='修理内容')
    repair_instructions = fields.Char(string='修理说明')
    repair_cost = fields.Char(string='修理费用')
    repair_maintenance_plan = fields.Char(string='修理计划')

    init_user = fields.Many2one('xlcrm.users', store=True,
                                string='创建者')
    init_time = fields.Datetime(string='创建时间', default=lambda self: fields.Datetime.utc_now(self))
    update_user = fields.Many2one('xlcrm.users', store=True, string='更新者')
    update_time = fields.Datetime(string='更新时间', default=lambda self: fields.Datetime.utc_now(self))
    record_status = fields.Integer(string='提交状态', default=0)
