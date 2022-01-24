# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class Xlmenu(models.Model):
    _name = 'xlcrm.menu'
    parent_id = fields.Integer(string='上级菜单')
    name = fields.Char(string='菜单名称', required=True)
    title = fields.Char(string='标题')
    alias = fields.Char(string='别名')
    icon = fields.Char(string='图标')
    remark = fields.Char(string='备注')
    module = fields.Char(string='所属模块')
    type = fields.Integer(string='类型', default=0)
    url = fields.Char(strin='地址')
    params = fields.Char(string='参数')
    target = fields.Char(string='打开方式', default='_self')
    is_navi = fields.Integer(string='是否导航', default=1)
    sort = fields.Integer(string='排序')
    status = fields.Integer(string='状态', default=1)
    create_date_time = fields.Datetime(string='创建时间', default=lambda self: fields.Datetime.utc_now(self))
    children_total = fields.Integer(string='children total', compute='_compute_count', store=False)

    create_user_id = fields.Many2one('xlcrm.users', store=True, string='创建人员', readonly=True)
    write_user_id = fields.Many2one('xlcrm.users', store=True, string='修改人员', readonly=True)
    create_user_name = fields.Char(related='create_user_id.username', string='创建人', store=False)
    write_user_name = fields.Char(related='write_user_id.username', string='修改人', store=False)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "菜单名称已经存在!"),
    ]

    # @api.multi
    def _compute_count(self):
        domain = [('parent_id', 'in', self.ids)]
        self.children_total = self.env['xlcrm.menu'].search_count(domain)

