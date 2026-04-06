from odoo import models, fields, api
from odoo.exceptions import UserError


class GamificationBadge(models.Model):
    _inherit = 'gamification.badge'

    quest_bonus = fields.Float(string='Quest Bonus')

    @api.constrains('quest_bonus')
    def quest_bonus_negative(self):
        """Prevent quest bonus from being negative."""
        if self.quest_bonus < 0:
            raise UserError("Invalid Value of Quest Bonus !")