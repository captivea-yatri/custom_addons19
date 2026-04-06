from odoo import models, fields, api
from datetime import timedelta


class Partner(models.Model):
    _inherit = 'res.partner'

    followup_frequency = fields.Selection([('monthly', 'Monthly'), ('quarterly', 'Quarterly'),
                                           ('semester', 'Semester'), ('annually', 'Annually')],
                                          string='Follow-up Frequency', default="quarterly")
    modules_used = fields.Many2many(comodel_name='default.domain', string='Modules Used')
    last_followup_date = fields.Date(string='Last Follow-up Date', compute = "_compute_followup_dates" ,store=True)
    next_followup_date = fields.Date(string='Next Follow-up Date', compute = "_compute_followup_dates" ,store=True)
    customer_followup_status = fields.Boolean(string='Follow-up Status')
    is_followup_true = fields.Boolean(string="Is Followup True", compute="_compute_is_followup")

    def _compute_is_followup(self):
        """Compute whether the partner has a follow-up frequency set.
        This field is used as a helper flag indicating that follow-up logic
        should apply to this record. It becomes True if any follow-up
        frequency option is selected."""
        for rec in self:
            rec.is_followup_true = bool(rec.followup_frequency)

    @api.depends('followup_frequency', 'message_ids', 'is_followup_true', 'status')
    def _compute_followup_dates(self):
        """
        Computes the partner’s last and next follow-up dates based on the most recent
        follow-up message or the customer_since_date. Uses the follow-up frequency to
        calculate the next due date (monthly, quarterly, semester, annually). If the
        partner is not a customer, all follow-up dates are cleared.
        """
        for rec in self:
            if rec.status in ['customer', 'old_customer']:
                last_followup = self.env['mail.message'].search(
                    [
                        ('model', '=', 'res.partner'),
                        ('res_id', '=', rec.id),
                        ('subtype_id', '=', 3),
                        ('mail_activity_type_id', '=', 107),
                    ],
                    limit=1,
                    order='date desc'
                )
                customer_since_date = rec.customer_since_date or False
                if last_followup:
                    rec.last_followup_date = last_followup.date.date()
                    rec.customer_followup_status = False
                    base_date = rec.last_followup_date
                else:
                    rec.last_followup_date = customer_since_date
                    base_date = customer_since_date

                if base_date:
                    if rec.followup_frequency == 'monthly':
                        rec.next_followup_date = base_date + timedelta(days=30)
                    elif rec.followup_frequency == 'quarterly':
                        rec.next_followup_date = base_date + timedelta(days=90)
                    elif rec.followup_frequency == 'semester':
                        rec.next_followup_date = base_date + timedelta(days=180)
                    elif rec.followup_frequency == 'annually':
                        rec.next_followup_date = base_date + timedelta(days=365)
                    else:
                        rec.next_followup_date = False
                else:
                    rec.next_followup_date = False
            else:
                rec.last_followup_date = False
                rec.next_followup_date = False

    def _check_followup_status(self):
        """Check whether customers are due for follow-up today.
        This method is designed for a cron job:
        - Searches all customers.
        - Compares today's date with next_followup_date.
        - Sets customer_followup_status = True if follow-up is due."""
        records = self.env['res.partner'].search([('status', '=', 'customer')])
        today = fields.Date.today()

        for rec in records:
            if rec.next_followup_date and rec.next_followup_date <= today:
                rec.customer_followup_status = True
            else:
                rec.customer_followup_status = False

    @api.model
    def _commercial_fields(self):
        """ Extend the commercial fields used on parent/child contacts.
        These fields will be shared between parent and child commercial partners."""
        return super(Partner, self)._commercial_fields() + \
            ['customer_followup_status','followup_frequency']
