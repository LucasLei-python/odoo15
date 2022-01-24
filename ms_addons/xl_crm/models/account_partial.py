# -*- coding: utf-8 -*-

from odoo import api, fields, models


class partialReject(models.Model):
    _name = 'xlcrm.account.partial'
    review_id = fields.Many2one('xlcrm.account', string='单据ID')
    from_station = fields.Integer(string='驳回来源站别')
    to_station = fields.Char(string='驳回去处站别')
    sign_station = fields.Char(string='已经审核过站别')
    from_id = fields.Integer(string='上次驳回单id')
    remark = fields.Char(string='驳回理由')
    init_time = fields.Datetime(string='创建时间', default=lambda self: fields.Datetime.utc_now(self))
    init_user = fields.Many2one('xlcrm.users', store=True, string='创建者')
    sign_over = fields.Char(compute='_compute_sign', store=False, string='是否签核完成')
    # to_brand = fields.Char(string='驳回去处品牌')
    # sign_brand = fields.Char(string='已经审核过品牌')

    # _sql_constraints = [
    #     ('review_title_uniq', 'unique (review_title)', "评审已经存在!"),
    # ]
    @api.depends('sign_station')
    def _compute_sign(self):
        for item in self:
            to_station = item.to_station if item.to_station else ''
            sign_station = item.sign_station if item.sign_station else ''
            to_station = sorted(set(to_station.split(',')))
            sign_station = sorted(set(sign_station.split(',')))
            item.sign_over = 'Y' if to_station == sign_station else 'N'
