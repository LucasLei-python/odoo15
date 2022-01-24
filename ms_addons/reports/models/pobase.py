# -*- coding: utf-8 -*-
import odoo
from odoo import api, fields, models, modules,registry
import fcntl, datetime


class Pobase(models.Model):
    _name = "report.pobase"
    account = fields.Char(string='下单套账')
    cvencode = fields.Integer(string='供应商编号')
    cvenname = fields.Char(string='供应商名称')
    cpoid = fields.Char(string='订单编号')
    ccontactcode = fields.Char(string="供方联系人编码")
    cvenperson = fields.Char(string="供方联系人")
    cdepcode = fields.Char(string="部门编码")
    cvenpuomprotocol = fields.Char(string='收付款协议编码')
    cpersoncode = fields.Char(string='业务员编码')
    nflat = fields.Float(string="汇率")
    idiscounttaxtype = fields.Char(string='扣税类别')
    cexch_name = fields.Char(string="币种")
    dpodate = fields.Date(string="订单日期")
    cmaker = fields.Char(string='制单人')
    cbustype = fields.Char(string='业务类型')
    cptcode = fields.Char(string='采购类型')
    itaxrate = fields.Float(string='表头税率')
    others = fields.Char(string="表体数据")
    record_status = fields.Integer(string='提交状态', default=0)
    po_attend_user_ids = fields.Many2many('xlcrm.users', 'users_po_rel', 'po_id',
                                               'user_id', string='参会者')
    station_no = fields.Integer(string='当前站别')
    station_desc = fields.Char(string='当前站别描述')
    signer = fields.Many2one('xlcrm.users', store=True, string='当前签核人')
    signer_nickname = fields.Char(related='signer.nickname', store=False, string='当前签核人昵称')
    init_time = fields.Datetime(string='创建时间', default=lambda self: fields.Datetime.utc_now(self))
    init_user = fields.Many2one('xlcrm.users', store=True, string='创建者')
    init_usernickname = fields.Char(related='init_user.nickname', store=False, string='创建者昵称')
    update_usernickname = fields.Char(related='update_user.nickname', store=False, string='更新者昵称')
    update_time = fields.Datetime('更新时间')
    update_user = fields.Many2one('xlcrm.users', store=True, string='更新者')
    reviewers = fields.Char(string='签核人')
    status_id = fields.Integer(string="审核状态", default=1)
    isback = fields.Integer(string='是否驳回', default=0)
    cname = fields.Char(string='账期')
    iscreatepo = fields.Boolean(string='是否在U8创建成功')

    @api.model
    def create(self, vals):
        file = self.__file_lock()  # 加文件锁
        code_prefix = '%s%s%s' % (
        'HK' if vals['account'] == '601' else 'AA', 'POGAP', datetime.date.today().strftime('%Y%m'))

        db = odoo.tools.config['db_name']
        cr = registry(db).cursor()
        env = api.Environment(cr, '', {})
        obj = env['report.pobase'].sudo().search_read([('cpoid', '=like', code_prefix + '%')], limit=1,
                                                       order='cpoid desc')
        vals['cpoid'] = code_prefix + '0001'
        if obj and obj[0]['cpoid'].startswith(code_prefix):
            vals['cpoid'] = code_prefix + str(int(obj[0]['cpoid'][-4:]) + 1).zfill(4)  # 自动补0
        cr.close()
        file.close()  # 关闭文件后锁自动释放
        return super(Pobase, self).create(vals)

    def __file_lock(self, flag=fcntl.LOCK_EX):
        file_path = modules.module.get_module_resource('repair', 'static/code.lock')
        file = open(file_path)
        fcntl.flock(file.fileno(), flag)
        return file
