# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class Xlregion(models.Model):
    _name = 'xlcrm.region'
    region_id = fields.Integer(string='地区')
    parent_id = fields.Integer(string='上级地区')
    region_name = fields.Char(string='地区名称', required=True)
    sort = fields.Integer(string='排序')
    is_delete = fields.Integer(string='是否删除', default=0)

    create_user_id = fields.Many2one('xlcrm.users', store=True, string='创建人员', readonly=True)
    write_user_id = fields.Many2one('xlcrm.users', store=True, string='修改人员', readonly=True)
    create_user_name = fields.Char(related='create_user_id.username', string='创建人', store=False)
    write_user_name = fields.Char(related='write_user_id.username', string='修改人', store=False)