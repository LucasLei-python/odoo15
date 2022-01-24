# -*- coding: utf-8 -*-

from odoo import api, fields, models


class XlaccountPur(models.Model):
    _name = 'xlcrm.account.pur'
    review_id = fields.Many2one('xlcrm.account', store=True, string='申请单据')
    content=fields.Char('Sales说明')
    init_time = fields.Datetime(string='创建时间', default=lambda self: fields.Datetime.utc_now(self))
    init_user = fields.Many2one('xlcrm.users', store=True, string='创建者')
    update_time = fields.Datetime('更新时间')
    update_user = fields.Many2one('xlcrm.users', store=True, string='更新者')
    station_no = fields.Integer('签核站别')
    brand = fields.Char('物料品牌')
    stock = fields.Char('是否有库存')
    stock_remark = fields.Char('库存种类')
    po = fields.Char('是否有在途po')
    po_remark = fields.Char('po种类')
    checkprice = fields.Char('是否查看附件价格')
    brandname = fields.Char('品牌')
    _sql_constraints = [
        ('review_id_uniq', 'unique (review_id,brandname)', "已经提交"),
    ]
