# -*- coding: utf-8 -*-
import odoo
from odoo import models, fields, api, modules
import fcntl, datetime

from odoo import registry


class Rebase(models.Model):
    _name = 'repair.baseinfo'

    code = fields.Char(string='编号', readonly=True)
    # customer = fields.Many2one('xlcrm.customer', store=True,
    #                            string='创建者')
    customer = fields.Char(string='客户名称')
    leading_cadre = fields.Char(string='维修负责人')
    maintenance_model = fields.Char(string='维修型号')
    contacts = fields.Char(string='联系人')
    arrive_date = fields.Date(string='抵修日期')
    serial_number = fields.Char(string='序列号')
    tel = fields.Char(string='电话')
    invoice_type = fields.Char(string='发票类型')
    # sale_date = fields.Date(string='销售日期')
    sale_date = fields.Char(string='销售日期')
    sales_business = fields.Char(string='销售业务')
    our_product = fields.Char(string='是否本公司产品')
    address = fields.Char(string='地址')
    remark = fields.Char(string='备注')
    init_user = fields.Many2one('xlcrm.users', store=True,
                                string='创建者')
    create_username = fields.Char(related='init_user.nickname', store=False, string='创建者昵称')
    init_time = fields.Datetime(string='创建时间', default=lambda self: fields.Datetime.utc_now(self))
    update_user = fields.Many2one('xlcrm.users', store=True, string='更新者')
    update_time = fields.Datetime(string='更新时间', default=lambda self: fields.Datetime.utc_now(self))
    record_status = fields.Integer(string='提交状态', default=0)
    testing_engineer = fields.Char(string='维修工程师')
    customer_service = fields.Char(string='维修客服')
    status = fields.Integer(string='签核描述')
    station_no = fields.Integer(string='当前站别')
    signers = fields.Char(string='当前签核人')
    create_date = fields.Date(string='创单日期')
    # customer_name = fields.Char(related='customer.name', store=False, string='客户名称')
    engineer_name = fields.Char(compute='_compute_engineer', store=False, string='工程师姓名')
    customer_service_name = fields.Char(compute='_compute_customer', store=False, string='客服姓名')

    @api.depends('testing_engineer')
    def _compute_engineer(self):
        for item in self:
            testing_engineer = item.testing_engineer.split(',') if item.testing_engineer else []
            users = ''
            if testing_engineer:
                users = self.env['xlcrm.users'].sudo().search_read([('id', 'in', testing_engineer[-2::-1])],
                                                                   fields=['nickname'])
                users = ','.join(map(lambda x: x['nickname'], users))
            item.engineer_name = users

    @api.depends('customer_service')
    def _compute_customer(self):
        for item in self:
            customer_service = item.customer_service.split(',') if item.customer_service else []
            users = ''
            if customer_service:
                users = self.env['xlcrm.users'].sudo().search_read([('id', 'in', customer_service[-2::-1])],
                                                                   fields=['nickname'])
                users = ','.join(map(lambda x: x['nickname'], users))
            item.customer_service_name = users

    @api.model
    # def create(self,vals):
    #     """
    #     利用odoo ir.sequence 模型产生自增序列号，但是最后3位流水号不能自动重置
    #     :param vals:
    #     :return:
    #     """
    #     # if not vals.get('code'):
    #     #     vals['code'] = self.env['ir.sequence'].next_by_code('repair.baseinfo.code') or '/'
    #     # return super(Rebase,self).create(vals)
    def create(self, vals):
        file = self.__file_lock()  # 加文件锁
        code_prefix = 'WX' + datetime.date.today().strftime('%Y%m%d')

        db = odoo.tools.config['db_name']
        cr = registry(db).cursor()
        env = api.Environment(cr, '', {})
        obj = env['repair.baseinfo'].sudo().search_read([('code', '=like', code_prefix + '%')], limit=1,
                                                        order='code desc')
        vals['code'] = code_prefix + '001'
        if obj and obj[0]['code'].startswith(code_prefix):
            vals['code'] = code_prefix + str(int(obj[0]['code'][-3:]) + 1).zfill(3)  # 自动补0
        cr.close()
        file.close()  # 关闭文件后锁自动释放
        return super(Rebase, self).create(vals)

    def __file_lock(self, flag=fcntl.LOCK_EX):
        file_path = modules.module.get_module_resource('myrepair', 'static/code.lock')
        file = open(file_path)
        fcntl.flock(file.fileno(), flag)
        return file
