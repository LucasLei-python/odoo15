# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ReportsPoSigners(models.Model):
    _name = 'report.po.signers'
    review_id = fields.Many2one('report.pobase', store=True, string='申请单据')
    station_no = fields.Integer(string='签核站别', default=1)
    station_desc = fields.Char(string='站别描述', default='草稿')
    signers = fields.Char(string='签核人')
    signed = fields.Char(string='已签核签核人')
    # brandname = fields.Char(string='签核品牌')
    # brandnamed = fields.Char(string='已签核品牌')
    # sign_over = fields.Char(compute='_compute_sign', store=False, string='是否签核完成')

    # _sql_constraints = [
    #     ('review_title_uniq', 'unique (review_title)', "评审已经存在!"),
    # ]

