from odoo import models, fields, api


class HrExpense(models.Model):
    _inherit = "hr.expense"

    ana_account_partner_ids = fields.Many2many(comodel_name='res.partner', relation='partner_expense_rel',
                                               string='Partner', compute='_compute_custom_many2many', store=True)
    analytic_account_ids = fields.Many2many(comodel_name='account.analytic.account',
                                            relation='analytic_account_expense_rel',
                                            string='Analytic Account', compute='_compute_custom_many2many',
                                            store=True)

    @api.depends('analytic_distribution')
    def _compute_custom_many2many(self):
        """
        it sets the partner of analytic account which use in json filed analytic distribution only if partner's
        customer status is in_progress, old_customer or not_customer.
        also sets analytic accounts which use in json field analytic distribution.
        """
        for rec in self:
            if rec.analytic_distribution:

                analytic_account_ids = []
                for key in rec.analytic_distribution.keys():
                    analytic_account_ids.extend(map(int, key.split(',')))

                analytic_account_ids = self.env['account.analytic.account'].browse(analytic_account_ids)

                if rec.analytic_account_ids not in analytic_account_ids or analytic_account_ids == False:
                    rec.analytic_account_ids = False
                for analytic_account_id in analytic_account_ids:
                    rec.analytic_account_ids = [(4, analytic_account_id.id)]
                    if analytic_account_id.partner_id.status != 'customer' and analytic_account_id.partner_id.status != False:
                        rec.ana_account_partner_ids = [(4, analytic_account_id.partner_id.id)]
            else:
                rec.ana_account_partner_ids = False
                rec.analytic_account_ids = False

    def action_approve_duplicates(self):
        # if self.env.user.has_group('access_rights_management.role_operation') or self.env.user.has_group(
        #         'access_rights_management.role_operation_on_boarder') or self.env.user.has_group(
        #     'access_rights_management.role_team_manager') or self.env.user.has_group(
        #     'access_rights_management.role_team_director'):
        if self.env.user.has_group('base.group_user'):
            return super(HrExpense, self.sudo()).action_approve_duplicates()
        else:
            return super(HrExpense, self).action_approve_duplicates()
