from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = "sale.order"

    # new M2O field to link with crm.lead (different from default)
    new_lead_id = fields.Many2one(
        "crm.lead",
        string="Linked Lead (New)",
        help="Lead from which this quotation was created."
    )

    @api.model
    def create(self, vals):

        order = super().create(vals)

        # Check if created from Lead (context usually has active_model + active_id)
        if self.env.context.get("active_model") == "crm.lead":
            lead_id = self.env.context.get("active_id")
            if lead_id:
                lead = self.env["crm.lead"].browse(lead_id)
                order.new_lead_id = lead.id  # link to new M2O field

                # Add 'From Lead' tag (create if not found)
                tag = self.env["crm.tag"].search([("name", "=", "From Lead")], limit=1)
                if not tag:
                    tag = self.env["crm.tag"].create({"name": "From Lead"})
                order.tag_ids = [(4, tag.id)]  # add tag to many2many

        return order
