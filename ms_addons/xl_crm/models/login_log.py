# -*- coding: utf-8 -*-

from odoo import api, fields, models


class Xlloginlogs(models.Model):
    _name = 'xlcrm.loginlog'
    init_time = fields.Datetime(string='创建时间', default=lambda self: fields.Datetime.utc_now(self))
    init_user = fields.Many2one('xlcrm.users', store=True, string='创建者')
    init_usernickname = fields.Char(related='init_user.nickname', store=False, string='创建者昵称')
    path = fields.Char(string='路径')
    name = fields.Char(string='名称')
    login_type = fields.Char(string='PC端or移动端')
    # _sql_constraints = [
    #     ('review_title_uniq', 'unique (review_title)', "评审已经存在!"),
    # ]
