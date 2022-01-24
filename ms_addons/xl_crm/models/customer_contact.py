# -*- coding: utf-8 -*-
import os
import odoo
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

class Xlcustomercontact(models.Model):
    _name = 'xlcrm.customer.contact'
    name = fields.Char(string='姓名', required=True,readonly=True, index=True)
    title = fields.Char(string='职位', default='')
    mobile = fields.Char(string='手机号码', default='')
    phone = fields.Char(string='固定电话', default='')
    qq = fields.Char(string='QQ号码', default='')
    wechat = fields.Char(string='微信号码', default='')
    dingding = fields.Char(string='钉钉号码', default='')
    email = fields.Char(string='邮箱', default='')
    address = fields.Char(string='公司地址', default='')
    gender = fields.Integer(string='性别', default=0)
    birthday = fields.Date(string='生日')
    avatar_id = fields.Integer(string='头像')
    avatar_url = fields.Char(string='头像URL', compute='_compute_avatar_url', store=False)
    is_default = fields.Boolean(string='默认联系人', default=False)
    create_date_time = fields.Datetime(string='创建时间', default=lambda self: fields.Datetime.utc_now(self))
    project_id =  fields.Many2one('xlcrm.project', store=True, string='所属项目', readonly=True)
    
    province_id = fields.Many2one('xlcrm.region', store=True, string='省', readonly=True)
    city_id = fields.Many2one('xlcrm.region', store=True, string='市', readonly=True)
    district_id = fields.Many2one('xlcrm.region', store=True, string='区/县', readonly=True)

    province_name = fields.Char(compute='_compute_province_name', string='省', store=False)
    city_name = fields.Char(compute='_compute_city_name', string='市', store=False)
    district_name = fields.Char(compute='_compute_district_name', string='区/县', store=False)

    customer_id = fields.Many2one('xlcrm.customer', store=True, string='所属客户', readonly=True)

    create_user_id = fields.Many2one('xlcrm.users', store=True, string='创建人员', readonly=True)
    write_user_id = fields.Many2one('xlcrm.users', store=True, string='修改人员', readonly=True)
    create_user_name = fields.Char(related='create_user_id.username', string='创建人', store=False)
    write_user_name = fields.Char(related='write_user_id.username', string='修改人', store=False)

    @api.depends('province_id')
    def _compute_province_name(self):
        for contact in self:
            contact.province_name = self.env['xlcrm.region'].search(
                [('region_id', '=', contact.province_id.id)]).region_name

    @api.depends('city_id')
    def _compute_city_name(self):
        for contact in self:
            contact.city_name = self.env['xlcrm.region'].search(
                [('region_id', '=', contact.city_id.id)]).region_name

    @api.depends('district_id')
    def _compute_district_name(self):
        for contact in self:
            contact.district_name = self.env['xlcrm.region'].search(
                [('region_id', '=', contact.district_id.id)]).region_name

    def _compute_avatar_url(self):
        for contact in self:
            contact.avatar_url = odoo.tools.config['serve_url'] + '/crm/image/' + str(contact.avatar_id)