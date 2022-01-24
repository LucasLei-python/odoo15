# -*- coding: utf-8 -*-
from odoo import models, fields

class SdoProductLine(models.Model):
    _name = 'sdo.product.line'
    product_number = fields.Float(string='器件用量', default = 0)
    product_price = fields.Float(string='产品价格', default = 0)
    product_price_currency = fields.Char(string='产品价格币种', default='元')
    product_profit = fields.Float(string='产品毛利', default = 0)
    product_id = fields.Many2one('sdo.product', store=True, string='产品', readonly=True)
    project_id = fields.Many2one('xlcrm.project', store=True, string='项目', readonly=True)
    create_date_time = fields.Datetime(string='创建时间', default=lambda self: fields.Datetime.utc_now(self))
    brandname = fields.Char(related='product_id.brand_name', string='产品品牌', store=False)
    product_name = fields.Char(related='product_id.name', string='产品名称', store=False)
    product_no = fields.Char(related='product_id.product_no', string='产品编号', store=False)
    product_type = fields.Char(related='product_id.product_type', string='产品规格', store=False)
    product_attribute = fields.Char(related='product_id.product_attribute', string='产品属性', store=False)
    category_name = fields.Char(related='product_id.category_name', string='产品类别', store=False)
    unit = fields.Char(related='product_id.unit', string='计量单位', store=False)
    default_price = fields.Float(related='product_id.price', string='默认价格', store=False)

    create_user_id = fields.Many2one('xlcrm.users', store=True, string='创建人员', readonly=True)
    write_user_id = fields.Many2one('xlcrm.users', store=True, string='修改人员', readonly=True)
    create_user_name = fields.Char(related='create_user_id.username', string='创建人', store=False)
    write_user_name = fields.Char(related='write_user_id.username', string='修改人', store=False)