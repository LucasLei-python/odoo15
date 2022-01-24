# -*- coding: utf-8 -*-

from odoo import api, fields, models


class XlaccountSigners(models.Model):
    _name = 'xlcrm.account.signers'
    review_id = fields.Many2one('xlcrm.account', store=True, string='申请单据')
    station_no = fields.Integer(string='签核站别', default=1)
    station_desc = fields.Char(string='站别描述', default='草稿')
    signers = fields.Char(string='签核人')
    signed = fields.Char(string='已签核签核人')
    brandname = fields.Char(string='签核品牌')
    brandnamed = fields.Char(string='已签核品牌')
    sign_over = fields.Char(compute='_compute_sign', store=False, string='是否签核完成')

    # _sql_constraints = [
    #     ('review_title_uniq', 'unique (review_title)', "评审已经存在!"),
    # ]
    @api.depends('signed')
    def _compute_sign(self):
        for item in self:
            signers = item.signers if item.signers else ''
            signed = item.signed if item.signed else ''
            brandname = item.brandname if item.brandname else ''
            brandnamed = item.brandnamed if item.brandnamed else ''
            signers = sorted(set(signers.split(',')))
            signed = sorted(set(signed.split(',')))
            brandname = sorted(set(brandname.split(',')))
            brandnamed = sorted(set(brandnamed.split(',')))
            item.sign_over = 'Y' if signers == signed and brandname == brandnamed else 'N'
