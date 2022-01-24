# -*- coding: utf-8 -*-
from odoo import models, fields


class Sdostagechange(models.Model):
    _name = 'sdo.project.stage.change'
    project_id = fields.Many2one('xlcrm.project', store=True, string='项目', readonly=True)
    operation_user_id = fields.Many2one('xlcrm.users', store=True, string='操作ID', readonly=True)
    from_stage_id = fields.Many2one('xlcrm.project.stage', store=True, string='From阶段', readonly=True)
    to_stage_id = fields.Many2one('xlcrm.project.stage', store=True, string='TO阶段', readonly=True)
    desc = fields.Text('备注')
    operation_date_time = fields.Datetime(string='操作时间', default=lambda self: fields.Datetime.utc_now(self))

    stage_id = fields.Many2one('xlcrm.project.stage', store=True, string='当前阶段', readonly=True)
    duration_effort = fields.Float(string='所用时间', Default=0)

    operation_user_name = fields.Char(related='operation_user_id.username', string='操作人员', store=False)
    project_name = fields.Char(related='project_id.name', string='项目名称', store=False)
    from_stage_name = fields.Char(related='from_stage_id.name', string='项目阶段（From）', store=False)
    to_stage_name = fields.Char(related='to_stage_id.name', string='项目阶段（To）', store=False)
    stage_name = fields.Char(related='stage_id.name', string='当前阶段', store=False)