# -*- coding: utf-8 -*-
from odoo import models, fields


class Xlccfuserpminspector(models.Model):
    _name = 'xlcrm.user.ccfpminspector'
    pm = fields.Char(string='pm')
    inspector = fields.Char(string='pm总监')
    init_time = fields.Datetime(string='创建时间', default=lambda self: fields.Datetime.utc_now(self))

    init_users = fields.Many2one('xlcrm.users', store=True, string='创建人员', readonly=True)
    update_time = fields.Datetime(string='更新时间')
    update_user = fields.Char(string='更新人')

    # _sql_constraints = [
    #     ('name_uniq', 'unique (name)', "用户组已经存在!"),
    # ]
