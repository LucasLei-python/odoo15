from odoo import models, fields, api, tools, registry
from ..public import update_brand_limit_to_u8


class Consolidated(models.Model):
    _name = 'consolidated'
    name = fields.Text('客户名称')


class ConsolidatedU8Cus(models.Model):
    _name = 'u8.cus.consolidated'
    code = fields.Char('客户编码')
    name = fields.Text('客户名称')
    ccusmnemcode = fields.Text('助记码')
    a_company = fields.Text('交易主体')
    a_companycode = fields.Text('交易主体')
    source = fields.Char('来源')
    result = fields.Char('匹配结果')
    brand_limit = fields.Integer('是否限制品牌', default=0)
    status = fields.Integer('同步状态', default=0)
    review_id = fields.Many2one('xlcrm.account')

    @api.model
    def syn_brand_limit(self):
        try:
            cr, env = self.get_env()
            res = self.sudo().search([("status", "=", 1)])
            for _res in res:
                brand = env["u8.cus.consolidated.brand"].sudo().search_read([("cus_con_id", "=", _res.id)])
                for _brand in brand:
                    _brand["material"] = env["u8.cus.consolidated.material"].sudo().search_read(
                        [("brand_con_id", "=", _brand["id"])])
                update_brand_limit_to_u8(_res, brand)
                # _res.status = 2
            cr.commit()
            cr.close()
        except Exception as e:
            print(e)

    @staticmethod
    def get_env():
        import odoo
        db = odoo.tools.config['db_name']
        cr = registry(db).cursor()
        env = api.Environment(cr, '', {})
        return cr, env


class ConsolidatedBrand(models.Model):
    _name = 'u8.cus.consolidated.brand'
    cus_con_id = fields.Many2one('u8.cus.consolidated')
    brand_name = fields.Char('品牌')
    pm = fields.Char('对应PM')
    init_user = fields.Many2one('xlcrm.users')
    init_nickname = fields.Char(related='init_user.nickname', store=False)
    init_time = fields.Datetime("保存时间", default=lambda self: fields.Datetime.utc_now(self))


class ConsolidatedMaterial(models.Model):
    _name = 'u8.cus.consolidated.material'
    brand_con_id = fields.Many2one('u8.cus.consolidated.brand')
    material_limit = fields.Char('限制料号')
