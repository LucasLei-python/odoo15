# -*- coding: utf-8 -*-
import odoo
import os
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

class Xlcustomer(models.Model):
    _name = 'xlcrm.customer'
    name = fields.Char(string='客户名称', required=True,readonly=True, index=True)
    customer_no = fields.Char(string='客户编号')
    customer_no_third = fields.Char(string='参考编号')
    short_name = fields.Char(string='客户简称')
    owner = fields.Char(string='联系人')
    mobile = fields.Char(string='手机号码')
    is_mobile = fields.Boolean(string='手机验证',default=True)
    email = fields.Char(string='邮箱')
    is_email = fields.Boolean(string='邮箱验证',default=True)
    is_focused = fields.Boolean(string='是否关注', default=False)
    address = fields.Char(string='公司地址')
    phone = fields.Char(string='公司电话')
    website = fields.Char(string='公司网址')
    birthday = fields.Date(string='注册日期')
    capital = fields.Float(string='注册资金')
    capital_currency = fields.Char(string='注册资金币种类型')
    customer_pic = fields.Char(string='客户头像')
    hot = fields.Integer(string='热度', compute='_compute_hot')
    products = fields.Char(string='主营产品')
    desc = fields.Char(string='客户描述', default='')
    create_date_time = fields.Datetime(string='创建时间', default= lambda self: fields.Datetime.utc_now(self))
    level_id = fields.Many2one('xlcrm.customer.level', store=True, string='客户等级', readonly=True, ondelete='restrict', default=1)
    category_id = fields.Many2one('xlcrm.customer.category', store=True, string='客户类别', readonly=True, ondelete='restrict', default=1)
    industry_id = fields.Many2one('xlcrm.customer.industry', store=True, string='所属行业', readonly=True, ondelete='restrict', default=1)
    status_id = fields.Many2one('xlcrm.customer.status', store=True, string='客户状态', readonly=True, ondelete='restrict', default=1)
    scope_id = fields.Many2one('xlcrm.customer.scope', store=True, string='客户规模', readonly=True, ondelete='restrict', default=1)
    revenue_id = fields.Many2one('xlcrm.customer.revenue', store=True, string='年营业额', readonly=True, ondelete='restrict', default=1)
    currency_type_id = fields.Many2one('xlcrm.currency.type', store=True, string='币种', readonly=True, ondelete='restrict', default=1)
    avatar_id = fields.Integer(string='头像')
    avatar_url = fields.Char(string='头像URL', compute='_compute_avatar_url', store=False)
    record_status = fields.Integer(string='记录状态', Default=1)
    email_notification = fields.Char(string='邮件知会人')
    projects = fields.One2many('xlcrm.project', 'customer_id', string='项目')
    project_ids = fields.One2many(compute='_compute_project_ids', store=False, string='项目ID')
    review_ids = fields.One2many(compute='_compute_review_ids', store=False, string='评审ID')

    visit_ids = fields.One2many(compute='_compute_visit_ids', store=False, string='拜访ID')
    create_user_id = fields.Many2one('xlcrm.users', store=True, string='创建人员', readonly=True, ondelete='restrict')
    write_user_id = fields.Many2one('xlcrm.users', store=True, string='修改人员', readonly=True)
    create_user_name = fields.Char(related='create_user_id.username', string='创建人', store=False)
    create_user_nick_name = fields.Char(related='create_user_id.nickname', string='创建人昵称', store=False)
    write_user_name = fields.Char(related='write_user_id.username', string='修改人', store=False)

    scope_id_name = fields.Char(related='scope_id.name', store=False, string='客户规模')
    revenue_id_name = fields.Char(related='revenue_id.name', store=False, string='年营业额')
    currency_type_id_name = fields.Char(related='currency_type_id.name', store=False, string='币种')
    create_user_old = fields.Many2one('xlcrm.users', store=True, string='原创建人', readonly=True)
    # customer_tag_id = fields.Many2many('xlcrm.customer.tag', store=True, string='客户标签')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "客户名称已经存在!"),
        ('no_uniq', 'unique (customer_no)', "客户编号已经存在!"),
    ]


    @api.model
    def get_customer_max_number(self):
        max_num_row = self.env['xlcrm.customer'].sudo().search_read([],[('id')],order='id desc',limit=1)
        max_num = "000000"
        if max_num_row:
            max_num = max_num_row[0]["id"] + 1
        return max_num

    # @api.multi
    @api.depends('projects')
    def _compute_project_ids(self):
        for customer in self:
            customer.project_ids = self.env['xlcrm.project'].search([('customer_id', '=', customer.id)]).ids

    # @api.multi
    @api.depends('project_ids')
    def _compute_review_ids(self):
        for customer in self:
            customer.review_ids = self.env['xlcrm.project.review'].search([('project_id', 'in', customer.project_ids.ids)]).ids

    # @api.multi
    def _compute_visit_ids(self):
        for customer in self:
            customer.visit_ids = self.env['xlcrm.visit'].search([('customer_id', '=', customer.id)]).ids

    def _compute_avatar_url(self):
        for crm_customer in self:
            crm_customer.avatar_url = odoo.tools.config['serve_url'] + '/crm/image/' + str(crm_customer.avatar_id)

    def _compute_hot(self):
        for crm_customer in self:
            crm_customer.hot = 10 + len(crm_customer.project_ids) + len(crm_customer.review_ids) + len(crm_customer.visit_ids)