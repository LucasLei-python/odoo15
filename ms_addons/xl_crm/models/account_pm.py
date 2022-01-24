# -*- coding: utf-8 -*-

from odoo import api, fields, models


class Xlaccountpm(models.Model):
    _name = 'xlcrm.account.pm'
    review_id = fields.Many2one('xlcrm.account', store=True, string='申请单据')
    content = fields.Char('Sales说明')
    init_time = fields.Datetime(string='创建时间', default=lambda self: fields.Datetime.utc_now(self))
    init_user = fields.Many2one('xlcrm.users', store=True, string='创建者')
    update_time = fields.Datetime('更新时间')
    update_user = fields.Many2one('xlcrm.users', store=True, string='更新者')
    station_no = fields.Integer('签核站别')
    source = fields.Char('业务来源')
    material_type = fields.Char('物料类型')
    sales_scale = fields.Char('销售规模')
    # scale_unit = fields.Char('销售规模单位')
    scale_currency = fields.Char('销售规模币种')
    account_period = fields.Char('给我司账期')
    delivery_time = fields.Char('原厂交货时间')
    stock_up = fields.Char('是否备货')
    profit = fields.Char('毛利率')
    others = fields.Char('其他')
    brandname = fields.Char('品牌')
    agree_loa = fields.Char('是否同意loa')
    material_profit = fields.Char('料号对应毛利率')
    _sql_constraints = [
        ('review_id_uniq', 'unique (review_id,brandname)', "已经提交"),
    ]
