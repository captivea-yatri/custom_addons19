from odoo import models, api, _
from odoo.exceptions import ValidationError

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        lines._check_product_account_restriction()
        return lines

    def write(self, vals):
        res = super().write(vals)
        self._check_product_account_restriction()
        return res

    def _check_product_account_restriction(self):
        """
        Enforce product/account restrictions for vendor bills.
        Works for first line, subsequent lines, catalog lines, and ignores:
        - Payable lines
        - Tax lines
        """
        for line in self:
            move = line.move_id
            if not move or move.move_type != 'in_invoice' or not move.partner_id:
                continue

            restrictions = self.env['product.account.restriction'].search([
                ('partner_id', '=', move.partner_id.id),
                '|', ('company_id', '=', move.company_id.id), ('company_id', '=', False)
            ])

            if not restrictions:
                continue

            allowed_products = restrictions.mapped('allowed_product_ids').ids
            allowed_accounts = restrictions.mapped('allowed_account_ids').ids

            payable_account_id = move.partner_id.property_account_payable_id.id

            # ✅ Skip system, payable, and tax lines
            if (
                not line.product_id and
                (
                    line.account_id.id == payable_account_id
                    or line.tax_line_id  # <- Skip tax lines
                )
            ):
                continue

            # ✅ Check product restriction
            if allowed_products and line.product_id and line.product_id.id not in allowed_products:
                raise ValidationError(
                    _("For Vendor %s, you cannot add the product %s.")
                    % (move.partner_id.name, line.product_id.display_name)
                )

            # ✅ Check account restriction (skip payable/tax)
            if (
                allowed_accounts
                and line.account_id
                and line.account_id.id not in allowed_accounts
                and line.account_id.id != payable_account_id
                and not line.tax_line_id  # <- Skip tax account lines
            ):
                raise ValidationError(
                    _("For Vendor %s, you cannot add the account %s.")
                    % (move.partner_id.name, line.account_id.display_name)
                )
