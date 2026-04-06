from odoo import api, models, fields, _


class MailMessage(models.Model):
    _inherit = "mail.message"

    @api.model_create_multi
    def create(self, vals_list):
        """
        Sets description of task when message is created from email.
        We have to inherit this method to set description from body of
        email even when email from and the customer of the task are different.
        We have set the customer of the task as same as customer of the project.
        """
        res = super(MailMessage, self).create(vals_list)
        for rec in res:
            if rec.model == 'project.task':
                task_id = self.env[rec.model].browse(rec.res_id)
                if rec.body != task_id.description:
                    if rec.message_type == 'email' and rec.res_id == task_id.id and 'task created' in rec.subtype_id.name.lower():
                        self.env[rec.model].browse(rec.res_id).write({'description': rec.body})
        return res