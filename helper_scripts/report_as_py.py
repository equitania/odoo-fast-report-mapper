# -*- coding: utf-8 -*-
# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

dependencies = [
    'eq_base', 'eq_fr_core', 'eq_res_partner',
    'account', 'eq_account'
    ]

report_name = {
        'ger': 'Rechnungen',
        'eng': 'Invoices'
    }

eq_print_report_button = True
report_tmpl_name = 'eq_fr_core_account_invoice'
report_model = 'account.invoice'

report_fields = {'account.invoice': ['id', 'number', 'date_invoice', 'origin', 'name', 'state', 'eq_head_text', 'partner_id',
                                     'partner_shipping_id', 'payment_term_id', 'incoterms_id', 'currency_id',
                                     'invoice_line_ids', 'comment', 'amount_total', 'amount_tax', 'amount_untaxed',
                                     'eq_use_page_break_after_header','eq_use_page_break_before_footer', 'user_id',
                                     'company_id', 'type'],
                 'account.invoice.line': ['id', 'sequence', 'product_id', 'delivery_date','discount',
                                          'price_subtotal','invoice_line_tax_ids', 'name','layout_category_id',
                                          'uom_id', 'quantity', 'price_unit', 'price_total', 'sale_line_ids', 'eq_move_ids',
                                          'display_type', 'eq_pos'],
                 'sale.order.line': ['id', 'order_id', 'move_ids'],
                 'sale.order': ['id', 'payment_acquirer_id'],
                 'payment.acquirer': ['id', 'name', 'done_msg'],
                 'res.currency': ['id', 'symbol'],
                 'res.partner': ['id', 'city', 'company_type', 'customer_number', 'eq_citypart', 'eq_firstname',
                                 'eq_foreign_ref', 'eq_foreign_ref_purchase', 'eq_house_no',
                                 'eq_name2', 'eq_name3', 'lang', 'name', 'parent_id', 'street', 'street2',
                                 'supplier_number', 'title', 'type','vat','zip', 'country_id', 'state_id'],
                 'res.partner.title': ['name', 'id',],
                 'res.company': ['id', 'bank_ids', 'city', 'company_registry', 'country_id', 'email', 'eq_ceo_01', 'eq_ceo_02',
                                 'eq_ceo_03', 'eq_ceo_title', 'eq_house_no', 'eq_fax', 'name', 'phone', 'state_id',
                                 'street', 'vat', 'website', 'zip'],
                 'res.partner.bank': ['id', 'acc_number', 'bank_bic', 'bank_name'],
                 'res.country': ['id', 'name'],
                 'res.country.state': ['id', 'name'],
                 'res.users': ['id', 'email', 'eq_firstname', 'eq_fax', 'lang', 'mobile', 'name', 'phone', 'display_name'],
                 'product.product': ['id', 'default_code', 'name', 'qty_available', 'lst_price'],
                 'uom.uom': ['id', 'name'],
                 'account.incoterms': ['id', 'name'],
                 'account.payment.term': ['id', 'note'],
                 'account.tax': ['id', 'description'],
                 'sale.layout_category': ['id', 'name', 'sequence'],
                 'stock.move': ['id', 'picking_id'],
                 'stock.picking': ['id', 'name', 'date_done'],
                 }

attachment = "(object.state in ('proforma','proforma2')) and " \
             "('Proforma-Rechnung-' + (object.number or '').replace('/','')+'.pdf') or " \
             "(object.state in ('draft')) and " \
             "('Entwurf-Rechnung.pdf') or " \
             "(object.state in ('cancel')) and " \
             "('Storno-Rechnung-' + (object.number or '').replace('/','')+'.pdf') or " \
             "(object.state in ('paid','open')) and " \
             "('Rechnung-' + (object.number or '').replace('/','')+'.pdf')"
print_report_name = "(object.state in ('proforma','proforma2')) and " \
                    "('Proforma-Rechnung-' + (object.number or '').replace('/','')) or " \
                    "(object.state in ('draft')) and " \
                    "('Entwurf-Rechnung') or " \
                    "(object.state in ('cancel')) and " \
                    "('Storno-Rechnung-' + (object.number or '').replace('/','')) or " \
                    "(object.state in ('paid','open')) and " \
                    "('Rechnung-' + (object.number or '').replace('/',''))"