# -*- coding: utf-8 -*-

from odoo import api, fields, models


class XlaccountSales(models.Model):
    _name = 'xlcrm.account.sales'
    review_id = fields.Many2one('xlcrm.account', store=True, string='申请单据')
    content = fields.Char('Sales说明')
    init_time = fields.Datetime(string='创建时间', default=lambda self: fields.Datetime.utc_now(self))
    init_user = fields.Many2one('xlcrm.users', store=True, string='创建者')
    update_time = fields.Datetime('更新时间')
    update_user = fields.Many2one('xlcrm.users', store=True, string='更新者')
    station_no = fields.Integer('签核站别')
    customer_type = fields.Char('客户类型')
    manufacturer = fields.Char('生产厂家')
    manufacturer_brand = fields.Char('生产厂家品牌')
    traders = fields.Char('贸易商')
    foundry = fields.Char('代工长/货代')
    traders_brand = fields.Char('贸易商品牌')
    customer_type_others = fields.Char('客户类型其他')
    main_products = fields.Char('客户主要产品')
    annual_turnover = fields.Char('客户年营业额')
    # turnover_unit = fields.Char('营业额单位')
    turnover_currency = fields.Char('营业额币种')
    employees = fields.Char('客户员工人数')
    key_customers = fields.Char('客户的主要客户')
    main_charge = fields.Char('客户主要股东')
    settlement_method = fields.Char('客户对供应商主要结算方式')
    settlement_method_days = fields.Char('月结天数')
    settlement_method_others = fields.Char('其他结算方式')
    others = fields.Char('其他说明')
    products = fields.Char('我司供应产品品牌')
    licensor = fields.Char('授权商名称')
    _sql_constraints = [
        ('review_id_uniq', 'unique (review_id)', "已经提交"),
    ]
