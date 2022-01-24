# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

class Xlvisit(models.Model):
    _name = 'xlcrm.visit'
    title = fields.Char(string='拜访标题', required=True,readonly=True, index=True)
    target = fields.Char(string='拜访目的')
    visit_date = fields.Date(string='拜访日期')
    next_date = fields.Date(string='下次日期')
    opportunity = fields.Char(string='生意机会')
    with_man = fields.Char(string='陪同人员')
    content = fields.Text(string='拜访内容')
    is_notice = fields.Integer(string='是否提醒', default=0)
    notice_type = fields.Integer(string='提醒方式', default=0)
    create_date_time = fields.Datetime(string='创建时间', default=lambda self: fields.Datetime.utc_now(self))
    to_email = fields.Char(string='收件人邮箱')
    cc_email = fields.Char(string='抄送人邮箱')
    customer_id = fields.Many2one('xlcrm.customer', store=True, string='客户', readonly=True, ondelete='restrict')
    status_id = fields.Many2one('xlcrm.visit.status', store=True, string='拜访状态', readonly=True, ondelete='restrict')
    type_id = fields.Many2one('xlcrm.visit.type', store=True, string='拜访方式', readonly=True, ondelete='restrict')

    customer_name = fields.Char(related='customer_id.name', string='客户名称', store=False)
    scope_id_name = fields.Char(related='customer_id.scope_id_name', string='客户规模', store=False)
    customer_products = fields.Char(related='customer_id.products', string='主营产品', store=False)
    revenue_id_name = fields.Char(related='customer_id.revenue_id_name', string='年营业额', store=False)

    create_user_id = fields.Many2one('xlcrm.users', store=True, string='创建人', readonly=True)
    write_user_id = fields.Many2one('xlcrm.users', store=True, string='修改人', readonly=True)
    create_user_name = fields.Char(related='create_user_id.username', string='创建人用户名', store=False)
    create_user_nick_name = fields.Char(related='create_user_id.nickname', string='创建人昵称', store=False)
    create_user_email = fields.Char(related='create_user_id.email', string='创建人email', store=False)
    write_user_name = fields.Char(related='write_user_id.username', string='修改人用户名', store=False)
