# -*- coding: utf-8 -*-
from odoo import models, fields
from odoo import api, fields, models

class Xlreviewcommit(models.Model):
    _name = 'xlcrm.review.commit'
    review_id = fields.Many2one('xlcrm.project.review', store=True, string='评审对象', ondelete='restrict')
    status_id = fields.Integer(string='评审状态', default = 0)
    review_comment = fields.Char(string='评审意见', default = '')
    review_result_id = fields.Integer(string='评审结果', default = 0)
    star_level =  fields.Integer(string='评审星级', default = 0)
    user_id = fields.Many2one('xlcrm.users', store=True, string='评审人', readonly=True)
    date_commit = fields.Datetime(string='提交时间', default=lambda self: fields.Datetime.utc_now(self))
    record_status = fields.Integer(string='记录状态', Default=1)
    project_id = fields.Many2one('xlcrm.project', related='review_id.project_id', string='项目名称', store=False)
    project_status_id = fields.Many2one(related='project_id.status_id', string='项目状态', store=False)
    customer_id = fields.Many2one(related='project_id.customer_id', string='客户名称', store=False)
    review_title = fields.Char(related='review_id.review_title', string='评审标题', store=False)
    review_create_user_name = fields.Char(related='review_id.create_user_name', string='评审发起', store=False)
    review_create_user_nick_name = fields.Char(related='review_id.create_user_nick_name', string='评审发起人昵称', store=False)
    from_stage_id = fields.Many2one(related='review_id.from_stage_id', string='评审阶段(从）', store=False)
    to_stage_id = fields.Many2one(related='review_id.to_stage_id', string='评审阶段（到）', store=False)
    review_date = fields.Datetime(related='review_id.date_begin', string='评审时间', store=False)
    user_name = fields.Char(related='user_id.username', string='提交人', store=False)
    user_nick_name = fields.Char(related='user_id.nickname', string='提交人昵称', store=False)
    create_date_time = fields.Datetime(string='创建时间', default=lambda self: fields.Datetime.utc_now(self))

    create_user_id = fields.Many2one('xlcrm.users', store=True, string='创建人员', readonly=True, ondelete='restrict')
    write_user_id = fields.Many2one('xlcrm.users', store=True, string='修改人员', readonly=True)
    create_user_name = fields.Char(related='create_user_id.username', string='创建人', store=False)
    write_user_name = fields.Char(related='write_user_id.username', string='修改人', store=False)