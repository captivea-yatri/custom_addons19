# -*- coding: utf-8 -*-

from odoo import models
from odoo.tools.misc import format_date, formatLang
import logging

_logger = logging.getLogger(__name__)


class report_print_check(models.Model):
    _inherit = 'account.payment'

    def _check_build_page_info(self, i, p):
        page = super(report_print_check, self)._check_build_page_info(i, p)
        page.update({
            'amount': formatLang(self.env, self.amount) if i == 0 else 'VOID',
            'amount_in_word': self.currency_id.amount_to_text(self.amount).ljust(75, '*'),
            'date_label': self.company_id.account_check_printing_date_label,
            'payment_date_canada': format_date(self.env, self.date, date_format='MM/dd/yyyy'),
        })
        return page
