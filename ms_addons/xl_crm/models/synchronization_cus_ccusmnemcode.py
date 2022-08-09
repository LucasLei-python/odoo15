from odoo import models, fields, api, tools, registry
from ..public import synchronization_cus_mcode


class SynchronizeU8Cus(models.Model):
    _name = 'u8.cus.synchronize'
    a_company = fields.Text('账套')
    code = fields.Char('客户编码')
    name = fields.Text('客户名称')
    abbrname = fields.Text('客户简称')
    ccusdefine7 = fields.Char('英文全称')
    ccusdefine3 = fields.Char('英文简称')
    ccusmnemcode = fields.Char('助记码')
    save_time = fields.Datetime(string='写入时间')
    save_user = fields.Char('编辑者')
    approval_time = fields.Datetime('审核时间')
    approval_user = fields.Char('审核者')
    status = fields.Integer('同步状态', default=0)
    remark = fields.Char('同步原因')

    @api.model
    def synchronization(self):
        res = self.search([('status', '=', 3)])
        des = synchronization_cus_mcode(res)
        data = {
            'remark': des['msg']
        }
        if des['msg'] == "ok":
            data['status'] = 4
        res.write(data)
