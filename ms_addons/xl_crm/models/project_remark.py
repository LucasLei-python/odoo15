# -*- coding: utf-8 -*-
from odoo import models, fields


class Xlprojectremark(models.Model):
    _name = 'xlcrm.project.remark'
    project_id = fields.Many2one('xlcrm.project',string='项目ID')
    content = fields.Char(string='内容')

    init_time = fields.Datetime(string='创建时间', default=lambda self: fields.Datetime.utc_now(self))

    init_user = fields.Many2one('xlcrm.users', store=True, string='创建人员', readonly=True)
    init_user_name = fields.Char(related='init_user.nickname', string='创建人昵称', store=False)
    update_user = fields.Many2one('xlcrm.users', store=True, string='修改人员', readonly=True)
    update_user_name = fields.Char(related='update_user.nickname', string='修改人昵称', store=False)
    update_time = fields.Datetime(string='修改时间')

    # _sql_constraints = [
    #     ('name_uniq', 'unique (name)', "项目类型已经存在!"),
    # ]