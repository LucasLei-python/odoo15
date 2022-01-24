# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

class Xldocuments(models.Model):
    _name = 'xlcrm.documents'

    @api.depends('res_model', 'res_id')
    def _compute_res_name(self):
        for attachment in self:
            if attachment.res_model and attachment.res_id:
                record = self.env[attachment.res_model].browse(attachment.res_id)
                attachment.res_name = record.display_name

    name = fields.Char('Document Name', required=True)
    res_model = fields.Char('Resource Model', readonly=True,
                            help="The database object this attachment will be attached to.")
    res_id = fields.Integer('Resource ID', readonly=True, help="The record id this is attached to.")
    res_related_model = fields.Char('Related Resource Model', readonly=True,
                            help="The database object this attachment will be attached to.")
    res_related_id = fields.Integer('Related Resource ID', readonly=True, help="The record id this is attached to.")
    res_name = fields.Char('Resource Name', compute='_compute_res_name', store=True)
    res_field = fields.Char('Resource Field', readonly=True)

    type = fields.Char(string='Type', required=True, default='binary')
    url = fields.Char('Url', index=True, size=1024)
    public = fields.Boolean('Is public document')

    datas_fname = fields.Char('File Name')
    db_datas = fields.Binary('Database Data')
    store_fname = fields.Char('Stored Filename')
    file_size = fields.Integer('File Size', readonly=True)
    checksum = fields.Char("Checksum/SHA1", size=40, index=True, readonly=True)
    mimetype = fields.Char('Mime Type', readonly=True)
    index_content = fields.Text('Indexed Content', readonly=True, prefetch=False)
    description = fields.Text('Description')
    create_date_time = fields.Datetime(string='创建时间', default=lambda self: fields.Datetime.utc_now(self))

    create_user_id = fields.Many2one('xlcrm.users', store=True, string='创建人员', readonly=True)
    write_user_id = fields.Many2one('xlcrm.users', store=True, string='修改人员', readonly=True)
    create_user_name = fields.Char(related='create_user_id.username', string='创建人', store=False)
    create_user_nick_name = fields.Char(related='create_user_id.nickname', string='创建人昵称', store=False)
    write_user_name = fields.Char(related='write_user_id.username', string='修改人', store=False)

