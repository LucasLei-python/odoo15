# -*- coding: utf-8 -*-

from odoo import api, fields, models


class XlaccountLg(models.Model):
    _name = 'xlcrm.account.lg'
    review_id = fields.Many2one('xlcrm.account', store=True, string='申请单据')
    content = fields.Char('Sales说明')
    rd_license_q = fields.Char(string='营业执照是否合格')
    rd_receipt = fields.Char(string='收货人确认方式')
    rd_receipt_q = fields.Char(string='收货人验证')
    rd_receipt_address = fields.Char(string='收货地址确认方式')
    rd_receipt_address_q = fields.Char(string='收货地址验证')
    rd_agree = fields.Char(string='是否同意')
    init_time = fields.Datetime(string='创建时间', default=lambda self: fields.Datetime.utc_now(self))
    init_user = fields.Many2one('xlcrm.users', store=True, string='创建者')
    update_time = fields.Datetime('更新时间')
    update_user = fields.Many2one('xlcrm.users', store=True, string='更新者')
    station_no = fields.Integer('签核站别')
    license = fields.Char('营业执照')
    consignee = fields.Char('收货人确认')
    consignee_verification = fields.Char('收货人确认验证')
    address = fields.Char('收货地址')
    address_verification = fields.Char('收货地址验证')
    remark = fields.Char('备注说明')
    agree = fields.Char('是否同意')
    authorization = fields.Char('采购授权书')
    _sql_constraints = [
        ('review_id_uniq', 'unique (review_id)', "已经提交"),
    ]
