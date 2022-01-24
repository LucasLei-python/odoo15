# -*- coding: utf-8 -*-

from odoo import api, fields, models


class Xlreload(models.Model):
    _name = 'xlcrm.reload'
    version = fields.Char(string='版本')
    item = fields.Char(string='说明')
    users = fields.Many2one('xlcrm.users', store=True, string='用户')
    reload = fields.Boolean(string='是否加载', default=True)
    update_usernickname = fields.Char(related='update_user.nickname', store=False, string='更新者昵称')
    update_time = fields.Datetime('更新时间')
    update_user = fields.Many2one('xlcrm.users', store=True, string='更新者')
    # _sql_constraints = [
    #     ('review_title_uniq', 'unique (review_title)', "评审已经存在!"),
    # ]
