# -*- coding: utf-8 -*-

from odoo import api, fields, models,registry
import odoo
from ..public import send_email_ToU8_EF,send_email_ToCUS_Account,grab_consolidated,suit_consolidated


class Xlaccount(models.Model):
    _name = 'xlcrm.account'
    review_type = fields.Char(string='单据类别')
    status_id = fields.Integer(string="审核状态", default=1)
    stop_status = fields.Integer(string="暂不处理", default=0)
    # review_status_id = fields.Integer(string='审核结果', default=0)
    apply_user = fields.Char(string='申请人')
    department = fields.Char(string='申请部门')
    apply_date = fields.Date('申请日期')
    a_company = fields.Text('申请公司名称(集团内)')
    kc_company = fields.Text('客户下单公司名称(中文)')
    ccusabbname = fields.Text('客户下单公司简称')
    ccusabbname_en = fields.Text('客户下单公司英文简称')
    ccuscode = fields.Char('客户代码')
    ccusmnemcode = fields.Char('助记码')

    ke_company = fields.Text('客户下单公司名称(英文)')
    kw_address = fields.Text('客户办公地址')
    ke_address = fields.Char("客户英文地址")
    registered_address = fields.Text('客户注册地址')
    kf_address = fields.Text('客户工厂地址')
    krc_company = fields.Text('客户收货地址(中文)')
    kre_company = fields.Text('客户收货地址(英文)')
    kpc_company = fields.Text('客户付款公司名称(中文)')
    kpe_company = fields.Text('客户付款公司名称(英文)')
    de_address = fields.Text('交货地点')
    unit = fields.Char(string='信用额度')
    currency = fields.Char(string='交易币种', size=10)
    dap = fields.Char(string='是否款到发货', size=4)
    c_account = fields.Text('现有账期')
    a_account = fields.Text('申请账期')
    protocol_code = fields.Char('首付款协议码')
    protocol_detail = fields.Char('首付款协议码描述')
    reconciliation_date = fields.Char('对账日期')
    payment_date = fields.Char('付款日期')
    station_no = fields.Integer(string='当前站别')
    isback = fields.Integer(string='是否驳回', default=0)
    station_desc = fields.Char(string='当前站别描述')
    next_station_no = fields.Integer(string='下一站签核站别')
    signer = fields.Char(string='当前签核人')
    # signer_nickname = fields.Char(related='signer.nickname', store=False, string='当前签核人昵称')
    next_signer = fields.Many2one('xlcrm.users', store=True, string='下一站签核人')
    init_time = fields.Datetime(string='创建时间', default=lambda self: fields.Datetime.utc_now(self))
    init_user = fields.Many2one('xlcrm.users', store=True, string='创建者')
    init_usernickname = fields.Char(related='init_user.nickname', store=False, string='创建者昵称')
    update_usernickname = fields.Char(related='update_user.nickname', store=False, string='更新者昵称')
    update_time = fields.Datetime('更新时间')
    update_user = fields.Many2one('xlcrm.users', store=True, string='更新者')
    record_status = fields.Integer(string='记录状态')
    account_attend_user_ids = fields.Many2many('xlcrm.users', 'users_account_rel', 'account_id',
                                               'users_id', string='参会者')
    reviewers = fields.Char(string='签核人')
    kehu = fields.Char(string='新老客户')
    release_time = fields.Char(string='放帐时间(老客户)')
    payment_method = fields.Char(string='付款方式(老客户)')
    acceptance_days = fields.Char(string='承兑天数(老客户)')
    telegraphic_days = fields.Char(string='电汇+承兑天数(老客户)')
    release_time_apply = fields.Char(string='申请帐期')
    release_time_applyM = fields.Char(string='月结天数(申请帐期)')
    release_time_applyO = fields.Char(string='其他天数(申请帐期)')
    payment_method_apply = fields.Char(string='付款方式(申请帐期)')
    acceptance_days_apply = fields.Char(string='承兑天数(申请帐期)')
    telegraphic_days_apply = fields.Char(string='电汇+承兑天数(申请帐期)')
    others_apply = fields.Char(string='其他付款方式')
    u8_payment = fields.Char(string='U8支付方式')
    credit_limit = fields.Char(string='申请交期信用额度')
    credit_limit_now = fields.Char(string='现有交期信用额度')
    products = fields.Char(string='品牌')
    remark = fields.Char(string='备注')
    current_account_period = fields.Char(string='现有账期')
    main_id = fields.Integer(string='主单ID')
    cs = fields.Char(string='cs')
    affiliates = fields.Char(string='关联公司名称')
    # affiliates = fields.Many2many('xlcrm.account.affiliates', 'affiliates_account_rel', 'account_id',
    #                                            'affiliates_id', string='关联客户')
    overdue_arrears = fields.Char(string='本公司是否超期')
    re_overdue_arrears = fields.Char(string='关联公司是否超期')
    overdue_payment = fields.Char(string='本公司是否逾期')
    re_overdue_payment = fields.Char(string='关联公司是否逾期')
    payment = fields.Char(string='本公司逾期数据')
    overdue = fields.Char(string='本公司超期数据')
    re_payments = fields.Char(string='关联公司逾期数据')
    re_overdues = fields.Char(string='关联公司超期数据')
    end_recive_date = fields.Char(string='月结客户截止接收对账日期')
    end_date = fields.Char(string='客户确认对账截止日期')
    latest_receipt_date = fields.Char(string='客户最晚收票日期')
    receipt_confirmer = fields.Char(string='收货确认人')
    release_time_apply_new = fields.Char(string='放账时间申请')
    release_time_apply_remark = fields.Char(string='账期申请备注')
    account_type = fields.Char(string='客户账期类型')
    payment_method_apply_new = fields.Char(string='客户账期类型')
    wire_apply_per = fields.Integer(string='电汇百分比')
    wire_apply_type = fields.Char(string='')
    wire_apply_days = fields.Integer(string='天数')
    days_apply_type = fields.Char(string='')
    days_apply_days = fields.Integer(string='天数')

    # _sql_constraints = [
    #     ('review_title_uniq', 'unique (review_title)', "评审已经存在!"),
    # ]
    @api.model
    def task(self):
        send_email_ToU8_EF()

    @api.model
    def get_consolidated(self):
        try:
            cr, env = self.get_env()
            # grab_consolidated(env)
            suit_consolidated(env)
            cr.close()
        except Exception as e:
            print(e)

    @api.model
    def send_mail_list(self):
        try:
            cr, env = self.get_env()
            send_email_ToCUS_Account(env)
            cr.close()
        except Exception as e:
            print(e)

    @staticmethod
    def get_env():
        db = odoo.tools.config['db_name']
        cr = registry(db).cursor()
        env = api.Environment(cr, '', {})
        return cr, env
