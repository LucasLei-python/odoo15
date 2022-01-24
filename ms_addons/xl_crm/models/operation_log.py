# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

class Xloperationlog(models.Model):
    _name = 'xlcrm.operation.log'
    name = fields.Char(string='操作名称', required=True,readonly=True, index=True)
    operator_name = fields.Char(string='当时操作人员')
    operation_date_time = fields.Datetime(string='操作时间', default=lambda self: fields.Datetime.utc_now(self))
    content = fields.Text(string='操作内容')
    operation_result = fields.Text(string='操作结果')
    result_desc = fields.Text(string='结果说明')
    res_id =  fields.Integer(string='操作对象ID')
    res_model = fields.Char(string='操作对象名称')
    res_id_related = fields.Integer(string='操作对象ID')
    res_model_related = fields.Char(string='操作对象名称')
    old_data = fields.Text(string='原始数据')
    new_data = fields.Text(string='修改数据')
    operation_level = fields.Integer(string='操作级别ID', Default=0)
    operation_type = fields.Integer(string='操作类型ID', Default=0)
    operation_category = fields.Char(string='操作类别')
    operation_IP = fields.Char(string='操作IP地址')
    operator_user_id = fields.Many2one('xlcrm.users', store=True, string='操作人员ID', readonly=True)
    operator_user_name = fields.Char(related='operator_user_id.username', string='操作人员', store=False)
    operator_user_nick_name = fields.Char(related='operator_user_id.nickname', string='操作人员名称', store=False)
    user_group_name = fields.Char(related='operator_user_id.user_group_name', string='用户组', store=False)

