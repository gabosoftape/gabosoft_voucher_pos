# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:LINTO CT(<https://www.cybrosys.com>)

#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###################################################################################
import string
import random
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class GiftVoucherPos(models.Model):
    _name = 'gift.voucher.pos'

    name = fields.Char(string="Nombre Promocion", required=True)
    voucher_type = fields.Selection(
        selection=[
            ('product', 'Product'),
            ('category', 'POS Category'),
            ('all', 'All Products'),
        ], string="Applicable on ", default='product'
    )
    product_id = fields.Many2one('product.product', string="Producto")
    product_categ = fields.Many2one('pos.category', string="Categoria Producto")
    min_value = fields.Integer(string="Valor Minimo Promocion", required=True)
    max_value = fields.Integer(string="Valor Maximo Promocion", required=True)
    expiry_date = fields.Date(string="Fecha Limite", required=True, help='Fecha de expiracion Promocion.')


class GiftCouponPos(models.Model):
    _name = 'gift.coupon.pos'

    def get_code(self):
        size = 7
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choice(chars) for _ in range(size))

    _sql_constraints = [
        ('name_uniq', 'unique (code)', "Code already exists !"),
    ]

    name = fields.Char(string="Nombre", required=True)
    code = fields.Char(string="Codigo", default=get_code)
    voucher = fields.Many2one('gift.voucher.pos', string="Promocion", required=True)
    start_date = fields.Date(string="Fecha de Inicio")
    end_date = fields.Date(string="Fecha Fin")
    partner_id = fields.Many2one('res.partner', string="Limitar a un solo socio", help='Limitar a un solo socio.')
    limit = fields.Integer(string="Total disponible para cada usuario", default=1, help='Total disponible para cada usuario.')
    total_avail = fields.Integer(string="Total Available", default=1)

    voucher_val = fields.Float(string="Valor Promocion", help='El importe de la promoción..')
    type = fields.Selection([
        ('fixed', 'Cantidad Fija'),
        ('percentage', 'Porcentaje'),
        ], store=True, default='fixed')

    @api.onchange('voucher_val')
    def check_val(self):
        if self.voucher_val > self.voucher.max_value or self.voucher_val < self.voucher.min_value:
            raise UserError(_("Por favor, compruebe el valor del vale."))


class CouponPartnerPos(models.Model):
    _name = 'partner.coupon.pos'

    partner_id = fields.Many2one('res.partner', string="Cliente")
    coupon_pos = fields.Char(string="Cupon")
    number_pos = fields.Integer(string="Numero de veces Usado.")

    def update_history(self, vals):
        if vals:
            h_obj = self.env['partner.coupon.pos']
            history = h_obj.search([('coupon_pos', '=', vals['coupon_pos']),('partner_id', '=', vals['partner_id'])], limit=1)
            coupon = self.env['gift.coupon.pos'].search([('code', '=', vals['coupon_pos'])], limit=1)
            if history:
                history.number_pos += 1
                coupon.total_avail -= 1
            else:
                coupon.total_avail -= 1
                rec = {
                    'partner_id': vals['partner_id'],
                    'number_pos': 1,
                    'coupon_pos': vals['coupon_pos']
                }
                h_obj.create(rec)
            return True


class PartnerExtendedPos(models.Model):
    _inherit = 'res.partner'

    applied_coupon_pos = fields.One2many('partner.coupon.pos', 'partner_id', string="Cupones aplicados desde POS.")
