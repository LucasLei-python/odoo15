# -*- coding: utf-8 -*-

from odoo import api, fields, models


class partialRejectSec(models.Model):
    _name = 'xlcrm.account.partial.sec'
    review_id = fields.Many2one('xlcrm.account', string='表单ID')
    p_id = fields.Many2one('xlcrm.account.partial',string='主表ID')
    station_no = fields.Integer(string='站别')

    remark = fields.Char(string='驳回理由')
    init_time = fields.Datetime(string='创建时间', default=lambda self: fields.Datetime.utc_now(self))
    init_user = fields.Many2one('xlcrm.users', store=True, string='创建者')
    sign_over = fields.Char(compute='_compute_sign', store=False, string='是否签核完成')
    to_brand = fields.Char(string='驳回去处品牌')
    sign_brand = fields.Char(string='已经审核过品牌')

    # _sql_constraints = [
    #     ('review_title_uniq', 'unique (review_title)', "评审已经存在!"),
    # ]
    @api.depends('sign_brand')
    def _compute_sign(self):
        for item in self:
            to_brand = item.to_brand if item.to_brand else ''
            sign_brand = item.sign_brand if item.sign_brand else ''
            to_brand = sorted(set(to_brand.split(',')))
            sign_brand = sorted(set(sign_brand.split(',')))
            item.sign_over = 'Y' if to_brand == sign_brand else 'N'
