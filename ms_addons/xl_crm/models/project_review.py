# -*- coding: utf-8 -*-
from odoo import models, fields
from odoo import api, fields, models

class Xlprojectreview(models.Model):
    _name = 'xlcrm.project.review'
    review_title = fields.Char(string='评审标题')
    status_id = fields.Integer(string='评审状态', default = 0)
    review_status_id = fields.Integer(string='评审结果', default=0)
    date_begin = fields.Datetime('开始时间')
    date_end = fields.Datetime('结束时间')
    desc = fields.Text('评审说明')
    review_target = fields.Text('评审目标')
    review_duration = fields.Integer('评审时长')
    record_status = fields.Integer(string='记录状态', Default=1)
    create_date_time = fields.Datetime(string='创建时间', default=lambda self: fields.Datetime.utc_now(self))

    project_id = fields.Many2one('xlcrm.project', store=True, string='项目', copy = True, ondelete='restrict')
    user_id = fields.Many2one('xlcrm.users', store=True, string='发起人', readonly=True, ondelete='restrict')
    from_stage_id = fields.Many2one('xlcrm.project.stage', store=True, string='From阶段', readonly=True, ondelete='restrict')
    to_stage_id = fields.Many2one('xlcrm.project.stage', store=True, string='TO阶段', readonly=True, ondelete='restrict')

    review_user_ids = fields.Many2many('xlcrm.users', 'users_review_rel', 'review_id',
                                   'users_id', string='参会者')

    review_commit_ids = fields.One2many('xlcrm.review.commit', 'review_id','Review Commit IDs')
    review_commits = fields.One2many(compute='_compute_review_commits', string="review commits", copy = False)
    review_document_ids = fields.One2many('xlcrm.documents', 'res_id', string='评审文档')
    # review_documents = fields.One2many(compute='_compute_review_documents', string='评审文档')
    create_user_id = fields.Many2one('xlcrm.users', store=True, string='创建人员', readonly=True, ondelete='restrict')
    write_user_id = fields.Many2one('xlcrm.users', store=True, string='修改人员', readonly=True)
    create_user_name = fields.Char(related='create_user_id.username', string='创建人', store=False)
    create_user_nick_name = fields.Char(related='create_user_id.nickname', string='创建人昵称', store=False)
    write_user_name = fields.Char(related='write_user_id.username', string='修改人', store=False)

    pass_count =  fields.Integer(compute='_compute_review_commits_pass', string="评审通过数", store=True)
    pass_count_lv = fields.Float(compute='_compute_review_commits_pass_lv', string="评审通过率", store=True)

    _sql_constraints = [
        ('review_title_uniq', 'unique (review_title)', "评审已经存在!"),
    ]

    @api.depends('review_commit_ids')
    def _compute_review_commits_pass(self):
        for review in self:
            review.pass_count = len(self.env['xlcrm.review.commit'].search([('review_result_id', '=', 1), ('review_id', '=', review.id)]).ids)

    @api.depends('pass_count')
    def _compute_review_commits_pass_lv(self):
        for review in self:
            all_pass_count = len(self.env['xlcrm.review.commit'].search([('review_result_id', '>', 0), ('review_id', '=', review.id)]).ids)
            if all_pass_count > 0:
                review.pass_count_lv = round(float(review.pass_count)/all_pass_count,2) * 100
            else:
                review.pass_count_lv = 0.0

    # @api.multi
    @api.depends('review_commit_ids')
    def _compute_review_commits(self):
        for review in self:
            if review.review_commit_ids:
                review.review_commits = self.env['xlcrm.review.commit'].sudo().search_read([('id', 'in', review.review_commit_ids.ids)],['id','review_comment'])
