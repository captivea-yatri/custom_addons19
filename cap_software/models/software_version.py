from odoo import fields, models, api


class SoftwareVersion(models.Model):
    _name = 'software.version'
    _description = 'Software Version Information'

    name = fields.Char(string='Name', compute='compute_name', store=True)
    software_id = fields.Many2one('software.software', string='Software', required=True)
    version = fields.Integer(string='Version', required=True, default=False)

    @api.depends('software_id', 'version', 'software_id.name')
    def compute_name(self):
        """
        This method is used to create name based on software and version
        """
        for rec in self._origin:
            software = rec.software_id.name if rec.software_id.name else False
            version = rec.version if rec.version else 0
            rec.name = software + ' V' + str(version)
