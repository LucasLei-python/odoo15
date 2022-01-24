# -*- coding: utf-8 -*-
import odoo
import os
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta


class Xlusers(models.Model):
    _name = 'xlcrm.users'
    username = fields.Char(string='用户名', required=True, readonly=True, index=True)
    password = fields.Char(string='密码', required=True)
    mobile = fields.Char(string='手机号码')
    is_mobile = fields.Boolean(string='手机登录', default=True)
    email = fields.Char(string='邮箱')
    is_email = fields.Boolean(string='邮箱登录', default=True)
    nickname = fields.Char(string='昵称')
    head_pic = fields.Char(string='头像')
    sex = fields.Integer(string='性别', default=0)
    birthday = fields.Date(string='生日')
    level_icon = fields.Char(string='等级图标')
    user_level_id = fields.Many2one('xlcrm.user.level', store=True, string='用户等级', ondelete='restrict')
    user_address = fields.Char(string='用户地址')
    # user_address_id = fields.Many2one('xlcrm.user.address', store=True, string='地址', readonly=True)
    group_id = fields.Many2one('xlcrm.user.group', store=True, string='用户组', readonly=True, ondelete='restrict')
    department_id = fields.Many2one('sdo.department', store=True, string='部门', readonly=True, ondelete='restrict')
    last_login = fields.Date(string='上次登录')
    last_ip = fields.Char(string='上次IP')
    status = fields.Integer(string='用户状态', default=1)
    is_delete = fields.Boolean(string='是否删除', default=False)
    user_id_odoo = fields.Integer(string='用户ID（Odoo）')
    # parent_id = fields.Many2one('xlcrm.users', string='上级账号', index=True)
    # child_ids = fields.One2many('xlcrm.users', 'parent_id', string='下级账号')
    parent_ids = fields.Many2many('xlcrm.users', 'users_users_rel', 'child_user_id',
                                  'parent_user_id', string='上级账号')
    child_ids = fields.Many2many('xlcrm.users', 'users_users_rel', 'parent_user_id',
                                 'child_user_id', string='下级账号')
    child_ids_all = fields.One2many(string='所有下级', compute='_compute_all_child', store=False)
    create_date_time = fields.Datetime(string='创建时间', default=lambda self: fields.Datetime.utc_now(self))
    review_ids = fields.Many2many('xlcrm.project.review', 'users_review_rel', 'users_id',
                                  'review_id', string='参与评审')
    user_attend_project_ids = fields.Many2many('xlcrm.project', 'users_project_rel', 'users_id',
                                               'project_id', string='参与项目')
    avatar_id = fields.Integer(string='头像')
    avatar_url = fields.Char(string='头像URL', compute='_compute_avatar_url', store=False)

    create_user_id = fields.Many2one('xlcrm.users', store=True, string='创建人员', readonly=True)
    write_user_id = fields.Many2one('xlcrm.users', store=True, string='修改人员', readonly=True)
    create_user_name = fields.Char(related='create_user_id.username', string='创建人', store=False)
    write_user_name = fields.Char(related='write_user_id.username', string='修改人', store=False)
    user_group_name = fields.Char(related='group_id.name', string='用户角色', store=False)
    department_name = fields.Char(related='department_id.name', string='部门', store=False)
    parent_user_names = fields.Char(string='上级账号', compute='_compute_parent_names', store=False)
    parent_user_nicknames = fields.Char(string='上级账号昵称', compute='_compute_parent_nicknames', store=False)
    email_password = fields.Char(string='邮箱密码')
    wechat_id = fields.Char(string='微信ID')
    _sql_constraints = [
        ('username_uniq', 'unique (username)', "用户名已经存在!"),
    ]

    def _compute_parent_nicknames(self):
        for crm_user in self:
            lstParentNames = self.env['xlcrm.users'].sudo().search_read([('id', 'in', crm_user.parent_ids.ids)],
                                                                        [('nickname')], order='id desc')
            all_usernickname = ''
            for usr in lstParentNames:
                all_usernickname = all_usernickname + usr['nickname'] + '   '
            crm_user.parent_user_nicknames = all_usernickname

    def _compute_avatar_url(self):
        for crm_user in self:
            crm_user.avatar_url = odoo.tools.config['serve_url'] + '/crm/image/' + str(crm_user.avatar_id)

    def _compute_parent_names(self):
        for crm_user in self:
            lstParentNames = self.env['xlcrm.users'].sudo().search_read([('id', 'in', crm_user.parent_ids.ids)],
                                                                        [('username')], order='id desc')
            all_username = ''
            for usr in lstParentNames:
                all_username = all_username + usr['username'] + '   '
            crm_user.parent_user_names = all_username

    @api.depends('child_ids_all')
    def _compute_all_child(self):
        for crm_usr in self:
            allChilds = []
            if crm_usr.child_ids:
                self._get_all_child_recursion(crm_usr, allChilds)
                crm_usr.child_ids_all = allChilds

    def _get_all_child_recursion(self, item_child, allChilds):
        if item_child.child_ids:
            for crm_usr_child in item_child.child_ids:
                if crm_usr_child.id not in allChilds:
                    allChilds.append(crm_usr_child.id)
                    self._get_all_child_recursion(crm_usr_child, allChilds)

    @classmethod
    def authenticate(cls, db, login, password, user_agent_env):
        """Verifies and returns the user ID corresponding to the given
          ``login`` and ``password`` combination, or False if there was
          no matching user.
           :param str db: the database on which user is trying to authenticate
           :param str login: username
           :param str password: user password
           :param dict user_agent_env: environment dictionary describing any
               relevant environment attributes
        """
        uid = cls._login(db, login, password)
        if uid == SUPERUSER_ID:
            # Successfully logged in as admin!
            # Attempt to guess the web base url...
            if user_agent_env and user_agent_env.get('base_location'):
                try:
                    with cls.pool.cursor() as cr:
                        base = user_agent_env['base_location']
                        ICP = api.Environment(cr, uid, {})['ir.config_parameter']
                        if not ICP.get_param('web.base.url.freeze'):
                            ICP.set_param('web.base.url', base)
                except Exception:
                    _logger.exception("Failed to update web.base.url configuration parameter")
        return uid
