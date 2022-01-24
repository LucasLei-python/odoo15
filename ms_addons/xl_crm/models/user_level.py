# -*- coding: utf-8 -*-
from odoo import models, fields

class Xluserlevel(models.Model):
    _name = 'xlcrm.user.level'
    name = fields.Char(string='等级名称', required=True)
    icon = fields.Char(string='等级头像')
    amount = fields.Float('等级数', required=True, default=0.0)
    discount = fields.Float('折扣', required=True, default=0.0)
    description = fields.Text('备注')
    create_date_time = fields.Datetime(string='创建时间', default=lambda self: fields.Datetime.utc_now(self))

    create_user_id = fields.Many2one('xlcrm.users', store=True, string='创建人员', readonly=True)
    write_user_id = fields.Many2one('xlcrm.users', store=True, string='修改人员', readonly=True)
    create_user_name = fields.Char(related='create_user_id.username', string='创建人', store=False)
    write_user_name = fields.Char(related='write_user_id.username', string='修改人', store=False)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "等级名称已经存在!"),
    ]