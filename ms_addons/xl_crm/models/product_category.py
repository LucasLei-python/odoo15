# -*- coding: utf-8 -*-
from odoo import models, fields

class SdoProductCategory(models.Model):
    _name = 'sdo.product.category'
    name = fields.Char(string='产品类别', required=True)
    parent_id = fields.Many2one('sdo.product.category', string='上级类别', index=True)
    sort = fields.Integer(string='排序值')
    status = fields.Integer('状态', required=True, default=1)
    description = fields.Text('类别描述')
    create_date_time = fields.Datetime(string='创建时间', default=lambda self: fields.Datetime.utc_now(self))

    parent_name = fields.Char(related='parent_id.name', string='上级类别名称', store=False)
    create_user_id = fields.Many2one('xlcrm.users', store=True, string='创建人员', readonly=True)
    write_user_id = fields.Many2one('xlcrm.users', store=True, string='修改人员', readonly=True)
    create_user_name = fields.Char(related='create_user_id.username', string='创建人', store=False)
    write_user_name = fields.Char(related='write_user_id.username', string='修改人', store=False)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "产品类别已经存在!"),
    ]