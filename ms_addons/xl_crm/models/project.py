# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
# from datetime import datetime, timedelta
# import datetime
class Xlproject(models.Model):
    _name = 'xlcrm.project'
    name = fields.Char(string='项目名称', required=True, readonly=True, index=True)
    project_no = fields.Char(string='项目编号', required=True)
    customer_price = fields.Float(string='客户报价', default =0)
    customer_price_currency = fields.Char(string='客户报价币种',default='元')
    cpu = fields.Char(string='CPU', default='')
    os = fields.Char(string='OS', default='')
    marketing = fields.Char(string='市场目标', default='')
    sdkversion = fields.Char(string='sdk version', default='')
    volume = fields.Float(string='用量', default=0)
    date_from = fields.Datetime(string='From', default= lambda self: fields.Datetime.utc_now(self))
    date_to = fields.Datetime(string='To', default= lambda self: fields.Datetime.utc_now(self))
    application = fields.Char(string='应用', default ='')
    desc = fields.Char(string='项目描述', default ='')
    dl_reason = fields.Char(string='失败描述', default='')
    is_focused = fields.Boolean(string='是否关注', default=False)
    create_date_time = fields.Datetime(string='创建时间', default= lambda self: fields.Datetime.utc_now(self))

    stage_id = fields.Many2one('xlcrm.project.stage', store=True, string='项目阶段', readonly=True, ondelete='restrict',index=True)
    category_id = fields.Many2one('xlcrm.project.category', store=True, string='项目类型', readonly=True, ondelete='restrict')
    status_id = fields.Many2one('xlcrm.project.status', store=True, string='项目状态', readonly=True, ondelete='restrict')
    record_status = fields.Integer(string='记录状态', Default=1)
    customer_id = fields.Many2one('xlcrm.customer', store=True, string='所属客户', readonly=True, ondelete='restrict')
    reviews = fields.One2many('xlcrm.project.review', 'project_id', string='项目评审')
    review_ids = fields.One2many(compute='_compute_review_ids', store=False, string='评审ID')
    project_document_ids = fields.One2many('xlcrm.documents', 'res_id', string='项目文档')
    stage_change_list = fields.One2many('sdo.project.stage.change', 'project_id', string='状态变更')
    stage_change_list_ids = fields.One2many(compute='_compute_stage_change_list_ids', store=False, string='状态变更ID')

    project_attend_user_ids = fields.Many2many('xlcrm.users', 'users_project_rel', 'project_id',
                                   'users_id', string='参会者')

    operation_date_time = fields.Datetime(string='创建时间', default=lambda self: fields.Datetime.utc_now(self))
    create_user_id = fields.Many2one('xlcrm.users', store=True, string='创建人员', readonly=True, ondelete='restrict')
    write_user_id = fields.Many2one('xlcrm.users', store=True, string='修改人员', readonly=True)
    create_user_name = fields.Char(related='create_user_id.username', string='创建人', store=False)
    create_user_nick_name = fields.Char(related='create_user_id.nickname', string='创建人', store=False)
    write_user_name = fields.Char(related='write_user_id.username', string='修改人', store=False)
    stage_id_name = fields.Char(related='stage_id.name', string='阶段名称', store=False)
    brand_name = fields.Char(string='品牌')
    date_do = fields.Datetime(string='DO日期', default=lambda self: fields.Datetime.utc_now(self))
    review_count = fields.Integer(compute='_compute_review_count', store=False, string='评审数量')
    socket = fields.Char(string='socket')
    reviewers = fields.Char(string='审核人')
    cus_city = fields.Char(string='客户所在城市')
    model_type_id = fields.Many2one('xlcrm.project.model', store=True, string='芯片或模型类别', readonly=True, ondelete='restrict')
    model_type = fields.Char(related='model_type_id.name', string='芯片或模型类别m', store=False)
    cus_product_type_id = fields.Many2one('xlcrm.project.cs.product', store=True, string='客户产品类型', readonly=True, ondelete='restrict')
    cus_product_type = fields.Char(related='cus_product_type_id.name', string='客户产品类型m', store=False)
    module = fields.Char(string='module')
    total_life_cycle = fields.Float('生命周期总量')
    total_life_price = fields.Float('生命周期总额')
    _sql_constraints = [
        ('name_uniq', 'unique (name)', "项目名称已经存在!"),
        ('no_uniq', 'unique (project_no)', "项目编号已经存在!"),
    ]


    @api.model
    def get_project_max_number(self):
        max_num_row = self.env['xlcrm.project'].sudo().search_read([], [('id')], order='id desc', limit=1)
        max_num = "000000"
        if max_num_row:
            max_num = max_num_row[0]["id"]
        return max_num

    # @api.multi
    @api.depends('reviews')
    def _compute_review_ids(self):
        for project in self:
            project.review_ids = self.env['xlcrm.project.review'].search([('project_id', '=', project.id)]).ids
            project.review_count = len(project.review_ids)

    @api.depends('review_ids')
    def _compute_review_count(self):
        for project in self:
            project.review_count = len(project.review_ids)

    # @api.multi
    @api.depends('stage_change_list')
    def _compute_stage_change_list_ids(self):
        for project in self:
            project.stage_change_list_ids = self.env['sdo.project.stage.change'].search([('project_id', '=', project.id)]).ids
