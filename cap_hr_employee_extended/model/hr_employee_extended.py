# -*- coding: utf-8 -*-

from odoo import fields, models, api
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError


class HrEmployeeExtended(models.Model):
    _inherit = 'hr.employee'

    odoo_experience_before_captivea = fields.Integer(string='Odoo experience before Captivea', groups='cap_hr_employee_extended.access_employee_group')
    experience_at_captivea = fields.Integer(string='Experience at Captivea', compute='_compute_experience_at_captivea')
    odoo_experience = fields.Integer(string='Total Odoo experience', compute='_compute_experience_at_captivea',store=True)
    x_studio_joining_date = fields.Date('Joining Date')
    real_employee = fields.Boolean(string='Real Employee',compute='_compute_real_employee', store=True)

    # override from base to solve the view warning on employee form
    barcode = fields.Char(string="Badge ID", help="ID used for employee identification.", groups="cap_hr_employee_extended.access_employee_group",
                          copy=False)

    @api.model
    def get_views(self, views, options=None):
        """
            Ensure that the `experience_at_captivea` and `odoo_experience` fields
            are always updated when employee views are loaded, preventing stale
            data in tree or form views.
               Logic:
                   - Compute experience for all employees (active and inactive) using
                     `_compute_experience_at_captivea`.
                   - Call the superclass `get_views` to return the standard view dictionary.
               """
        self.env['hr.employee'].search(['|',('active', '=', True),('active', '=', False)])._compute_experience_at_captivea()
        res = super().get_views(views, options)
        return res


    @api.depends('x_studio_joining_date')
    def _compute_experience_at_captivea(self):
        """
                Compute method for `experience_at_captivea` and `odoo_experience`.
                Logic:
                    For active employees:
                        - Compute months between joining date and today.
                        - Total Odoo experience = experience before Captivea + experience at Captivea.
                    For inactive employees (departed):
                        - Compute months between joining date and departure date.
                        - Total Odoo experience = experience before Captivea + experience at Captivea.
                """
        for employee in self:
            if employee.active:
                if employee.x_studio_joining_date:
                    joining_date = employee.x_studio_joining_date
                    # ✅ Corrected line below
                    difference = relativedelta(fields.Date.today(), joining_date)
                    employee.experience_at_captivea = difference.years * 12 + difference.months
                else:
                    employee.experience_at_captivea = 0
                employee.odoo_experience = employee.odoo_experience_before_captivea + employee.experience_at_captivea
            else:
                if employee.departure_date and employee.x_studio_joining_date:
                    joining_date = employee.x_studio_joining_date
                    departure_date = employee.departure_date
                    difference = relativedelta(departure_date, joining_date)
                    employee.experience_at_captivea = difference.years * 12 + difference.months
                else:
                    employee.experience_at_captivea = 0
                employee.odoo_experience = employee.odoo_experience_before_captivea + employee.experience_at_captivea

    @api.constrains('odoo_experience_before_captivea')
    def check_odoo_experience_before_captivea(self):
        """
        Prevent negative values for months of Odoo experience before Captivea.
        """
        if self.odoo_experience_before_captivea < 0:
            raise UserError("Invalid Value for Total Months of Experience Before Captivea!")

    @api.depends('user_id','company_id','user_id.company_id')
    def _compute_real_employee(self):
        """
                  Determines if the employee is a "real" employee of the current company.
              Logic:
                  - If `user_id` is assigned:
                      - Compare employee's `company_id` with the user's company.
                      - True if they match, False otherwise.
                  - If no `user_id` is assigned:
                      - Default to True (assume real employee).
              """
        for employee in self:
            if employee.user_id:
                if employee.company_id.id == employee.user_id.company_id.id:
                    employee.real_employee = True
                else:
                    employee.real_employee = False
            else:
                employee.real_employee = True