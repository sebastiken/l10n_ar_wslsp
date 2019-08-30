# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2017 E-MIPS (http://www.e-mips.com.ar)
#    Copyright (c) 2017 Eynes (http://www.eynes.com.ar)
#    All Rights Reserved. See AUTHORS for details.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import logging
import re

from openerp import _, api, exceptions, fields, models
from openerp.exceptions import except_orm
from  openerp.addons.l10n_ar_wslsp.wslsptools.wslsp_easywsy \
    import InvoiceNumberException

_logger = logging.getLogger(__name__)


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    breed_id = fields.Many2one('wslsp.breed.codes', 'Breed')
    ranch_type = fields.Selection(
        related='invoice_id.purchase_data_id.ranch_type', string='Ranch Type')

    def get_romaneo_summary_line(self):
        summary_line_obj = self.env['ranch.purchase.romaneo.summary.line']
        query = """
            SELECT romaneo_summary_line_id
            FROM purchase_romaneo_summary_line_invoice_rel
            WHERE invoice_id = %s
            LIMIT 1
        """
        self.env.cr.execute(query, (self.id,))
        try:
            res = self.env.cr.fetchone()[0]
            summary_line = summary_line_obj.browse(res)
        except (TypeError, IndexError):
            summary_line = summary_line_obj
        return summary_line

    def get_romaneo_final_line(self):
        final_line_obj = self.env['ranch.purchase.data.final.line']
        query = """
            SELECT romaneo_final_line_id
            FROM purchase_romaneo_final_line_invoice_rel
            WHERE invoice_id = %s
            LIMIT 1
        """
        self.env.cr.execute(query, (self.id,))
        try:
            res = self.env.cr.fetchone()[0]
            final_line = final_line_obj.browse(res)
        except (TypeError, IndexError):
            final_line = final_line_obj
        return final_line

    def _check_romaneo_final_line(self):
        self.ensure_one()
        final_line = self.get_romaneo_final_line()
        if not final_line:
            raise except_orm(_('WSLSP Error!'),
                    _("Line Invoice [%s] does not have a ranch purchase " \
                      "data associated") %(self.name))
        return final_line

    def _round_qty_and_adjust_price(self, price_unit, quantity):
        subtotal = price_unit * quantity
        rounded_qty = round(quantity, 0)
        adjusted_price_unit = subtotal / rounded_qty
        return adjusted_price_unit, rounded_qty


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    aut_lsp = fields.Boolean(
        'Autorize', default=False, help='Autorize liquidation to AFIP')
    purchase_data_type = fields.Selection(
        related='purchase_data_id.billing_type',
        string="Purchase Data Type", store=True)
    is_lsp = fields.Boolean('Is LSP')

    @api.multi
    def _check_ranch_purchase(self):
        if not self.purchase_data_id:
            raise except_orm(_('WSLSP Error!'),
                    _("Invoice does not have a ranch purchase data associated"))
        return self.purchase_data_id

    def _check_fiscal_values(self):
        self.ensure_one()
        if not self.is_lsp:
            res = super(AccountInvoice, self)._check_fiscal_values()
            return res

        denomination_id = self.denomination_id and \
            self.denomination_id.id or False

        if not denomination_id:
            raise except_orm(_('Error!'), _('Denomination not set in invoice'))

        if denomination_id not in self.pos_ar_id.denomination_ids.ids:
            raise except_orm(_('Error!'),
                _('Point of sale has not the same '
                  'denomination as the invoice.'))

        if self.fiscal_position.denomination_id.id != denomination_id:
            raise except_orm(_('Error'),
                _('The invoice denomination does not corresponds with '
                  'this fiscal position.'))
        return True

    def get_wslsp_config(self):

        config_obj = self.env['wslsp.config']
        config = config_obj.get_config(self.pos_ar_id)
        return config

    @api.multi
    def _get_wslsp_voucher_type(self):
        self.ensure_one()
        config = self.get_wslsp_config()
        purchase_data = self._check_ranch_purchase()
        billing_type = purchase_data.billing_type
        voucher_type = config.voucher_type_ids.filtered(
                lambda x: (x.is_direct and
                x.document_type == self.type and
                x.denomination_id.id == self.denomination_id.id))
        if not voucher_type:
            raise except_orm(_('WSLSP Error!'),
                    _('There is not configured voucher type with document[%s] '
                      'Is Direct[%s] Denomination[%s]') %
                    (self.type, True, self.denomination_id.name))
        if len(voucher_type) > 1:
            raise except_orm(_('WSLSP Error!'),
                _('There are duplicated voucher types'))
        return int(voucher_type.code)



    #TODO: Sacar cuando se haga el merge de la rama:
    #https://github.com/Maartincm/l10n-argentina/blob/8.0-wsfe-rebase
    @api.multi
    def split_number(self):
        try:
            pos, numb = self.internal_number.split('-')
        except (ValueError, AttributeError):
            raise except_orm(
                _("Error!"),
                _("Wrong Number format for invoice id: `%s`" % self.id))
        if not pos:
            raise except_orm(
                _("Error!"),
                _("Wrong POS for invoice id: `%s`" % self.id))
        if not numb:
            raise except_orm(
                _("Error!"),
                _("Wrong Number Sequence for invoice id: `%s`" % self.id))
        try:
            pos = int(pos)
        except ValueError:
            raise except_orm(
                _("Error!"),
                _("Wrong POS `%s` for invoice id: `%s`" % (pos, self.id)))
        try:
            numb = int(numb)
        except ValueError:
            raise except_orm(
                _("Error!"),
                _("Wrong Number Sequence `%s` for invoice id: `%s`" %
                  (numb, self.id)))
        return pos, numb

    #TODO: Sacar cuando se haga el merge de la rama:
    #https://github.com/Maartincm/l10n-argentina/blob/8.0-wsfe-rebase
    @api.multi
    def _get_pos(self):
        self.ensure_one()
        try:
            pos = self.split_number()[0]
        except Exception:
            if not self.pos_ar_id:
                err = _("Pos not found for invoice `%s` (id: %s)") % \
                    (self.internal_number, self.id)
                raise except_orm(_("Error!"), err)
            pos = int(self.pos_ar_id.name)
        return pos

    #TODO: Sacar cuando se haga el merge de la rama:
    #https://github.com/Maartincm/l10n-argentina/blob/8.0-wsfe-rebase
    @api.multi
    def complete_date_invoice(self):
        for inv in self:
            if not inv.date_invoice:
                inv.write({
                    'date_invoice': fields.Date.context_today(self),
                })
        return True

    @api.multi
    def get_next_wslsp_number(self, conf=False):
        self.ensure_one()
        inv = self
        if not conf:
            conf = self.get_wslsp_config()
        voucher_type = self._get_wslsp_voucher_type()
        pos_ar = self._get_pos()
        last = conf.get_last_voucher(pos_ar, voucher_type)
        return int(last + 1)

    @api.multi
    def get_next_liquidation_number(self):
        """
        Funcion para obtener el siguiente numero de comprobante
        correspondiente en el sistema
        """
        self.ensure_one()
        invoice = self
        cr = self.env.cr
        # Obtenemos el ultimo numero de comprobante
        # para ese pos y ese tipo de comprobante
        q = """
        SELECT MAX(TO_NUMBER(
            SUBSTRING(internal_number FROM '[0-9]{8}$'), '99999999')
            )
        FROM account_invoice
        WHERE internal_number ~ '^[0-9]{4}-[0-9]{8}$'
            AND pos_ar_id = %(pos_id)s
            AND denomination_id = %(denomination_id)s
            AND state in %(state)s
            AND type = %(type)s
            AND purchase_data_id IS NOT NULL
        """
        q_vals = {
            'pos_id': invoice.pos_ar_id.id,
            'denomination_id': invoice.denomination_id.id,
            'state': ('open', 'paid', 'cancel',),
            'type': invoice.type,
        }
        cr.execute(q, q_vals)
        last_number = cr.fetchone()
        self.env.invalidate_all()

        # Si no devuelve resultados, es porque es el primero
        if not last_number or not last_number[0]:
            next_number = 1
        else:
            next_number = last_number[0] + 1

        return int(next_number)

    @api.multi
    def get_last_liquidation_date(self):
        self.ensure_one()
        q = """
        SELECT MAX(date_invoice)
        FROM account_invoice
        WHERE internal_number ~ '^[0-9]{4}-[0-9]{8}$'
            AND pos_ar_id = %(pos_id)s
            AND state in %(state)s
            AND type = %(type)s
            AND purchase_data_id IS NOT NULL
        """
        q_vals = {
            'pos_id': self.pos_ar_id.id,
            'state': ('open', 'paid', 'cancel',),
            'type': self.type,
        }
        self.env.cr.execute(q, q_vals)
        last_date = self.env.cr.fetchone()
        if last_date and last_date[0]:
            last_date = last_date[0]
        else:
            last_date = False
        return last_date

    # Heredado para no cancelar si es una liquidacion del sector pecuario
    @api.multi
    def action_cancel(self):
#        for inv in self:
#            if inv.aut_lsp:
#                err = _("You cannot cancel an Electronic livestock sector " +
#                        "liquidation because it has been informed to AFIP.")
#                raise exceptions.ValidationError(err)
        return super(AccountInvoice, self).action_cancel()

    @api.multi
    def action_move_create(self):
        #Estamos en autoliquidacion?
        lsp_invoices = self.filtered(lambda x: x.is_lsp)
        lsp_invoices.button_compute(set_total=True)
        res = super(AccountInvoice, self).action_move_create()
        return res

    @api.multi
    def action_number(self):
        invoices = self.env['account.invoice']
        for inv in self:
            if not self.is_lsp:
                res = super(AccountInvoice, inv).action_number()
                continue
            inv._check_fiscal_values()
            # si el usuario no ingreso un numero,
            # busco el ultimo y lo incremento , si no hay ultimo va 1.
            # si el usuario hizo un ingreso dejo ese numero
            internal_number = inv.internal_number
            if not internal_number:
                next_number = inv.get_next_liquidation_number()
                pos_ar = inv.pos_ar_id
                internal_number = '%s-%08d' % (pos_ar.name, next_number)

            m = re.match('^[0-9]{4}-[0-9]{8}$', internal_number)
            if not m:
                raise except_orm(_('Error'),
                        _('The Invoice Number should be the format XXXX-XXXXXXXX'))

            aut_lsp = False
            conf = inv.get_wslsp_config()
            if conf and inv.pos_ar_id in conf.point_of_sale_ids:
                aut_lsp = True

            invoice_vals = {
                'aut_lsp' : aut_lsp,
                'internal_number' : internal_number
            }

            inv.write(invoice_vals)
        return True

    def _check_perceptions(self):

        for perception in self.perception_ids:
            if not perception.amount < 0.0 or not perception.base:
                raise except_orm(_('WSLSP Error!'),
                        _('Perceptions amount has to be negative '
                          'because it is a liquidation.'))

    @api.multi
    def _add_vat_retention(self, response):

        self.ensure_one()

        conf = self.get_wslsp_config()

        # Get new trisbutes from response
        tax_lines = self.tax_line.filtered(
            lambda x: x.tax_id.tax_group != 'vat')

        codes = [
            int(conf.get_tribute_code(tax)) for tax in tax_lines.tax_id
        ]

        if 'tributo' in response:
            tributes = filter(lambda x: x.codTributo not in codes, response.tributo)
            tax_l = []
            # Retencion IVA
            for tribute in tributes:
                tax = conf.tax_ids.filtered(lambda x: int(x.code) == tribute.codTributo)
                if not tax:
                    raise except_orm(_('WSLSP Config Error!'),
                        _('The wslsp does not have a configuration '
                          'for the tribute with code [%s]') % (tribute.codTributo))

                tax_id = tax.tax_id
                tax_l.append((0, 0, {
                    'name': tax_id.description or tax_id.name,
                    'tax_id': tax_id.id,
                    #'base': tribute.baseImponible,
                    'amount': round(-float(tribute.importe), 2),
                    #'base': tribute.baseImponible,
                    'tax_amount': round(-float(tribute.importe), 2),
                    'base_code_id': tax_id.base_code_id.id,
                    'tax_code_id': tax_id.tax_code_id.id,
                    'account_id': tax_id.account_collected_id.id,
                }))

            if not tax_l:
                return False

            # Add tributes to invoice and recompute
            self.write({'tax_line': tax_l})
            self.button_reset_taxes()

            # We have to recreate move_id
            # unlink origin move
            move_to_unlink = self.move_id
            self.move_id = False
            move_to_unlink.button_cancel()
            move_to_unlink.unlink()
            self.action_move_create()

            return True

    @api.model
    def synchronize_liquidation(self, ws, pos_ar, number):

        invoice_vals, response = ws.get_liquidation_by_number(pos_ar, number)
        dte = response.dte[0].nroDTE

        invoice_domain = [
            ('is_lsp', '=', True),
            ('state', '=', 'draft'),
            ('dte', '=', dte),
        ]

        if not ws.config.homologation:
            # When in homologation, receptor.cuit is always the afip cuit
            invoice_domain.append(
                ('partner_id.vat', '=', response.receptor.cuit))

        invoice = self.search(invoice_domain)

        if not invoice:
            raise except_orm(_("WSLSP Error"),
                             _("Synchronize process failed!"))

        invoice.action_move_create()

        # Create and attach pdf invoice from AFIP
        pdf_data = invoice_vals.pop('pdf', False)
        if pdf_data:
            attachment = invoice.attach_liquidation_report(pdf_data)
            self.send_autoliquidation_by_mail(attachment)

        # Add Vat Retention
        invoice._add_vat_retention(response)

        # Escribimos los campos necesarios de la factura
        invoice.write(invoice_vals)

        invoice_name = self.name_get()[0][1]
        if not self.reference:
            ref = invoice_name
        else:
            ref = '%s [%s]' % (invoice_name, self.reference)

        # Update move reference
        invoice._update_reference(ref)

        # Llamamos al workflow para que siga su curso
        invoice.signal_workflow('invoice_massive_open')

        return invoice

    def _prepare_ctx_send_mail(self, template_id):
        return {
            'default_model': 'account.invoice',
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
        }

    @api.multi
    def do_send_mail(self):
        self.write({'sent': True})
        template_id = self.env.ref(
                'l10n_ar_wslsp.mail_autoliquidation_template').id
        compose_form_id = self.env.ref('mail.email_compose_message_wizard_form').id

        ctx = dict(self.env.context)
        ctx.update(self._prepare_ctx_send_mail(template_id))

        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': str(ctx),
        }

    @api.multi
    def send_autoliquidation_by_mail(self, attachment):
        try:
            mail_obj = self.env['mail.mail']
            template = self.env.ref(
                'l10n_ar_wslsp.mail_autoliquidation_template')
            values = template.generate_email(template.id, self.id)
            values['recipient_ids'] = [
                (4, pid) for pid in values.get('partner_ids', list())
            ]
            values['attachment_ids'] = [(6, 0, attachment.ids)]
            mail = mail_obj.create(values)
            mail.send()
        except Exception as e:
            return True
        self.write({'sent': True})
        return True

    @api.multi
    def action_aut_cae(self):
        #res = super(AccountInvoice, self).action_aut_cae()

        for inv in self:
            if not inv.aut_lsp:
                res = super(AccountInvoice, inv).action_aut_cae()
                continue

            # In case of syncrhonization
            invoice_to_validate = None

            # Check if partner_id has same CUIT as company
            if self.company_id.vat == inv.partner_id.vat:
                raise except_orm(_('WSLSP Error!'),
                        _('VAT Number is same as your company '
                          'so it cannot be informed to AFIP.'
                          'Check Number of Point of Sale.'))

            self._sanitize_taxes(inv)
            inv._check_perceptions()

            new_cr = self.pool.cursor()
            uid = self.env.user.id
            ctx = self.env.context
            conf = inv.get_wslsp_config()
            ws = conf._get_wslsp_obj()
            try:
                invoice_vals, response = ws.generate_liquidation(inv)

                # Create and attach pdf invoice from AFIP
                pdf_data = invoice_vals.pop('pdf', False)
                if pdf_data:
                    attachment = inv.attach_liquidation_report(pdf_data)
                    self.send_autoliquidation_by_mail(attachment)
                inv.write(invoice_vals)

                # Add Vat Retention
                inv._add_vat_retention(response)
                self.env.cr.commit()

            except InvoiceNumberException, e:
                self.env.cr.rollback()
                number_to_synchro = e.number-1

                invoice_synchronized = self.synchronize_liquidation(
                    ws, inv.pos_ar_id.name, number_to_synchro)

                # If invoice synchronized is THIS invoice
                # re validate THIS inv
                if invoice_synchronized != inv:
                    invoice_to_validate = inv

                self.env.cr.commit()

            except except_orm as e:
                raise

            except Exception as e:
                raise except_orm(_('WSLSP Validation Error'),
                        _('Error received was: \n %s') % repr(e))
            finally:
                # Creamos el wslsp.request con otro cursor,
                # porque puede pasar que
                # tengamos una excepcion e igualmente,
                # tenemos que escribir la request
                # Sino al hacer el rollback se pierde hasta el wslsp.request
                self.env.cr.rollback()
                with api.Environment.manage():
                    new_env = api.Environment(new_cr, uid, ctx)
                    ws.log_request(new_env)
                    new_cr.commit()
                    new_cr.close()

            if invoice_to_validate:
                invoice_to_validate.signal_workflow('invoice_open')
        return True

    @api.multi
    def attach_liquidation_report(self, pdf):
        #Decode PDF from base64
        #file_pdf = b64decode(pdf)
        data_attach = {
			'name' : str(self.internal_number) + '.pdf',
			'datas' : pdf,
			'datas_fname' : str(self.internal_number) + '.pdf',
			'res_model' : 'account.invoice',
			'res_id' : self.id
		}
        #paso el regisruttro en el modelo attachment
        attachment = self.env['ir.attachment'].create(data_attach)
        return attachment
