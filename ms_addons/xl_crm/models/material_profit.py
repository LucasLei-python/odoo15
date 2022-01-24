# -*- coding: utf-8 -*-

from odoo import fields, models


class MaterialProfit(models.Model):
    _name = 'xlcrm.material.profit'
    pm_id = fields.Integer('表单ID')
    material = fields.Char('料号')
    profit = fields.Char('毛利率')
    init_time = fields.Datetime(string='创建时间', default=lambda self: fields.Datetime.utc_now(self))
    init_user = fields.Many2one('xlcrm.users', store=True, string='创建者')
    update_time = fields.Datetime('更新时间')
    update_user = fields.Many2one('xlcrm.users', store=True, string='更新者')

    # _sql_constraints = [
    #     ('review_title_uniq', 'unique (review_title)', "评审已经存在!"),
    # ]
