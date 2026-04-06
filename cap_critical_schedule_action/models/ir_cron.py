# -*- coding: utf-8 -*-
import logging
import time
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class IrCron(models.Model):
    _inherit = "ir.cron"

    def _callback(self, cron_name, server_action_id):
        """
            Execute the cron's server action, log any failure, and notify configured users via email.
            Rolls back the transaction on error to keep environment clean.
        """
        self.ensure_one()
        try:
            # Reload registry if needed
            if self.pool != self.pool.check_signaling():
                self.env.reset()
                self = self.env[self._name]

            _logger.info('Job %r (%s) starting', cron_name, self.id)
            start_time = time.time()

            # Run the server action
            self.env['ir.actions.server'].browse(server_action_id).run()
            self.env.flush_all()

            end_time = time.time()
            _logger.info('Job %r (%s) done in %.3fs', cron_name, self.id,
                         end_time - start_time)

            if start_time and _logger.isEnabledFor(logging.DEBUG):
                _logger.debug(
                    'Job %r (%s) server action #%s with uid %s executed in %.3fs',
                    cron_name, self.id, server_action_id, self.env.uid, end_time - start_time
                )

            self.pool.signal_changes()

        except Exception as exception:
            # Log exception
            _logger.exception('Job %r (%s) server action #%s failed', cron_name, self.id, server_action_id)

            # Rollback to clean environment
            self.env.cr.rollback()

            # Get recipients from config parameter
            param_value = self.env['ir.config_parameter'].sudo().get_param(
                'cap_critical_schedule_action.cron_email_recipient_ids'
            )
            user_ids = [int(x) for x in param_value.strip('[]').split(',')] if param_value else []
            users = self.env['res.users'].browse(user_ids)

            # Avoid sending email for serialization errors
            if str(exception).strip() != 'could not serialize access due to concurrent update':
                if users:
                    # Send email after rollback
                    self._send_exception_email(users, cron_name, self.id, exception)

    def _send_exception_email(self, users, cron_name, job_id, exception):
        """
            Log the cron failure in 'cron.failure.history' and send an HTML email
            to the specified users ONLY if a new failure record is created.
        """
        # Check if the failure already exists
        existing_error = self.env['cron.failure.history'].sudo().search([
            ('action_name', '=', cron_name),
            ('is_solved', '=', False)
        ], limit=1)

        # If a record already exists, do nothing (skip email)
        if existing_error:
            _logger.info('Cron failure for %r already logged. No email sent.', cron_name)
            return

        # Otherwise, create a new failure log
        self.env['cron.failure.history'].sudo().create({
            'action_name': cron_name,
            'error_message': str(exception),
            'time_of_failure': fields.Datetime.now(),
        })

        # Prepare the email
        subject = _('Cron Job Failed: %s') % cron_name
        body = f"""
        <html>
        <head>
        ... (your existing HTML template) ...
        </head>
        <body>
            <div class="header">
                <h2>Cron Job Failure Notification</h2>
            </div>
            <div class="content">
                <p><span class="highlight">Hello,</span></p>
                <p>A cron job has failed. Please find the details below:</p>
                <div class="details">
                    <p><strong>Cron Job Name:</strong> {cron_name}</p>
                    <p><strong>Cron Job ID :</strong> {job_id}</p>
                    <p><strong>Error Message:</strong> {str(exception)}</p>
                </div>
                <p>Please check the logs for further details.</p>
            </div>
            <div class="footer">
                <p>This is an automated notification. Do not reply to this email.</p>
            </div>
        </body>
        </html>
        """

        # Send email
        mail_values = {
            'subject': subject,
            'body_html': body,
            'email_to': ', '.join(u.email for u in users if u.email),
            'auto_delete': False,
        }
        mail = self.env['mail.mail'].sudo().create(mail_values)
        mail.sudo().send(force_send=True)

        self.env.cr.commit()

