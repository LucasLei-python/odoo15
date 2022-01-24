# -*- coding: utf-8 -*-
from odoo import models, fields


class SdoProduct(models.Model):
    _name = 'sdo.product'
    name = fields.Char(string='产品名称', required=True)
    product_no = fields.Char(string='产品编号', required=True)
    product_type = fields.Char(string='产品规格')
    product_attribute = fields.Char(string='产品属性')
    unit = fields.Char(string='计量单位')
    price = fields.Float(string='单价')
    sort = fields.Integer(string='排序值')
    status = fields.Integer('状态', required=True, default=1)
    description = fields.Text('备注')
    create_date_time = fields.Datetime(string='创建时间', default=lambda self: fields.Datetime.utc_now(self))

    category_id = fields.Many2one('sdo.product.category', store=True, string='所属类别', readonly=True)
    category_name = fields.Char(related='category_id.name', string='类别名称', store=False)
    brand_id = fields.Many2one('sdo.product.brand', store=True, string='产品品牌', readonly=True)
    brand_name = fields.Char(related='brand_id.name', string='品牌名称', store=False)

    department_id = fields.Many2one('sdo.department', store=True, string='产品部门')
    department_name = fields.Char(related='department_id.name', string='部门名称', store=False)

    create_user_id = fields.Many2one('xlcrm.users', store=True, string='创建人员', readonly=True)
    write_user_id = fields.Many2one('xlcrm.users', store=True, string='修改人员', readonly=True)
    create_user_name = fields.Char(related='create_user_id.username', string='创建人', store=False)
    write_user_name = fields.Char(related='write_user_id.username', string='修改人', store=False)
    test=fields.Char(string='test')
    _sql_constraints = [
        ('product_no_uniq', 'unique (product_no)', "产品编号已经存在!"),
    ]