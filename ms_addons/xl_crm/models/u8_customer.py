# -*- coding: utf-8 -*-

from ..public import synchronization_cus
import odoo
from odoo import models, fields, api, modules
import fcntl, datetime

from odoo import registry


class ToU8Customer(models.Model):
    _name = 'xlcrm.u8_customer'
    a_company = fields.Text('账套')
    code = fields.Char('客户编码')
    name = fields.Text('客户名称')
    abbrname = fields.Text('客户简称')
    sort_code = fields.Char('客户类型编码')
    payment = fields.Text('支付方式')
    ccussscode = fields.Text('结算方式')
    ccusmngtypecode = fields.Char('客户管理类型编码', default='999')
    account_remark = fields.Text('账期补充说明')
    ccdefine2 = fields.Text('客户资料是否齐全')
    ccusexch_name = fields.Text('币种')
    seed_date = fields.Text('发展日期')
    super_dept = fields.Text('分管部门')
    spec_operator = fields.Text('分管业务员')
    phone = fields.Text('客户联系电话')
    contact = fields.Text('客户联系人')
    mobile = fields.Text('客户联系移动电话')
    email = fields.Text('客户联系Email地址')
    # ccuscreditcompany = fields.Text('信用单位')
    credit_rank = fields.Text('信用等级')
    credit_amount = fields.Text('信用额度')
    credit = fields.Text('是否控制信用额度',default='1')
    creditdate = fields.Text('是否控制信用期限',default='1')
    ccussaprotocol = fields.Text('销售默认收付款协议')
    status = fields.Integer('同步状态', default=0)
    review_id = fields.Many2one('xlcrm.account', store=True, string='主单ID')
    remark = fields.Char('备注')
    category = fields.Char('类型')
    ccusmnemcode = fields.Char('助记码')
    # deliver_add = fields.One2many('xlcrm.u8_customer_deliver_add')
    # bank = fields.One2many('xlcrm.u8_customer_bank')

    # _sql_constraints = [
    #     ('review_title_uniq', 'unique (review_title)', "评审已经存在!"),
    # ]
    @api.model
    def task(self):
        cr, env = self.get_env()
        review_ids = []
        res = env['xlcrm.u8_customer'].sudo().search([('status', '=', 0)])
        for _res in res:
            if _res.review_id.status_id == 3:
                des = synchronization_cus(_res,env)
                if des.get("ok"):
                    _res.status = 1
                    _res.code = des.get('msg')
                    _res.remark = 'ok'
                    if _res.a_company != '999':
                        _res.review_id.ccuscode = des.get('msg')
                        review_ids.append(_res.review_id.id)
                else:
                    _res.remark = des.get("msg")
        cr.commit()
        from ..public import ccf
        ccf = ccf.CCF()
        for r_id in review_ids:
            ccf.insert_brandlimit_toU8(r_id, env)
        cr.close()

    @staticmethod
    def get_env():
        db = odoo.tools.config['db_name']
        cr = registry(db).cursor()
        env = api.Environment(cr, '', {})
        return cr, env

    @api.model
    def create(self, vals):
        file = self.__file_lock()  # 加文件锁
        cr, env = self.get_env()
        obj = env['xlcrm.u8_customer'].sudo().search_read(limit=1, order='code desc')
        if not vals['code']:
            vals['code'] = '3000001'
            if obj and int(obj[0]['code']) > 300001:
                vals['code'] = str(int(obj[0]['code']) + 1)

        cr.close()
        file.close()  # 关闭文件后锁自动释放
        return super(ToU8Customer, self).create(vals)

    def __file_lock(self, flag=fcntl.LOCK_EX):
        file_path = modules.module.get_module_resource('xl_crm', 'static/code.lock')
        file = open(file_path)
        fcntl.flock(file.fileno(), flag)
        return file


class ToU8CustomerDeliverAdd(models.Model):
    _name = 'xlcrm.u8_customer_deliver_add'
    review_id = fields.Many2one('xlcrm.account', store=True, string='主单ID')
    cus = fields.Many2one('xlcrm.u8_customer')
    caddcode = fields.Char('地址编码')
    cdeliveradd = fields.Char('收货地址')
    cenglishadd = fields.Char('英文地址')
    cenglishadd2 = fields.Char('省')
    cenglishadd3 = fields.Char('地级市')
    cenglishadd4 = fields.Char('区')
    cdeliverunit = fields.Char('收货单位')
    clinkperson = fields.Char('联系人')
    clinkname = fields.Char('')
    clinkphone = fields.Char('')
    clinkmobile = fields.Char('')
    clinkemail = fields.Char('')
    clinkzipcode = fields.Char('')
    bdefault = fields.Char('默认值')


class ToU8CustomerBank(models.Model):
    _name = 'xlcrm.u8_customer_bank'
    review_id = fields.Many2one('xlcrm.account', store=True, string='主单ID')
    cus = fields.Many2one('xlcrm.u8_customer')
    cbank = fields.Char('所属银行')
    cbranch = fields.Char('开户银行')
    caccountnum = fields.Char('银行账号')
    caccountname = fields.Char('账户名称')
    bdefault = fields.Char('默认值')


class ToU8CustomerAuthDimen(models.Model):
    _name = 'xlcrm.u8_customer_authdimen'
    review_id = fields.Many2one('xlcrm.account', store=True, string='主单ID')
    cus = fields.Many2one('xlcrm.u8_customer')
    cadcode = fields.Char('代码')
    cadname = fields.Char('名称')
