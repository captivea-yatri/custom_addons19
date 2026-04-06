from odoo import fields, models, api
from datetime import date, timedelta

class CompanyReports(models.Model):
    _name = 'res.company.reports'
    _description = 'Company Reports'
    
    company_id = fields.Many2one('res.company', string='Company')
    
    quality_crm = fields.Float(string='CRM Quality')
    quality_operation = fields.Float(string='Operation Quality')
    quality_target = fields.Float(string='Target Quality')
    
    previous_quality_crm = fields.Float(string='Previous CRM Quality')
    previous_quality_operation = fields.Float(string='Previous Operation Quality')
    previous_quality_target = fields.Float(string='Previous Target Quality')
    
    variation_crm = fields.Float(string='CRM Quality Variation')
    variation_operation = fields.Float(string='Operation Quality Variation')
    variation_target = fields.Float(string='Target Quality Variation')
    
    performance_growth_sales = fields.Float(string='Growth Sales Performance')
    performance_profit = fields.Float(string='Profit Performance')
    performance_active_customer = fields.Float(string='Active Customer')

    performance_growth_sales_summary = fields.Char(string='Growth Sales Performance Summary')
    performance_profit_summary = fields.Char(string='Performance Profit Summary')

    previous_performance_growth_sales = fields.Float(string='Previous Growth Sales Performance')
    previous_performance_profit = fields.Float(string='Previous Profit Performance')
    previous_performance_active_customer = fields.Float(string='Previous Active Customer')
    
    variation_performance_growth_sales = fields.Float(string='Growth Sales Performance Variation')
    variation_performance_profit = fields.Float(string='Previous Profit Performance Variation')
    variation_performance_active_customer = fields.Float(string='Previous Active Customer Variation')

    yearly_performance_growth_sales = fields.Float(string='Yearly Growth Sales Performance')
    yearly_performance_profit = fields.Float(string='Yearly profit Performance')

    yearly_performance_growth_sales_summary = fields.Char(string='Yearly Growth Sales Performance Summary')
    yearly_performance_profit_summary = fields.Char(string='Yearly Performance Profit Summary')
    
    budget_marketing_allocation = fields.Float(string='Budget Marketing Allocation')
    budget_marketing_allocation_projection = fields.Float(string='Budget Marketing Allocation projection')
    budget_marketing_consumed = fields.Float(string='Budget Marketing Consumed')

    amount_in_late_more_than_15days = fields.Float(string='Amount in late more than 15 days')
    
    def generate_company_report(self):
        
        subsidiaries = self.env['res.company'].search([])
        
        # Loop through each subsidiary
        for subsidiary in subsidiaries:

            quality_operation = 0.0
            quality_target = 0.0
            quality_crm = 0.0
            
            previous_quality_crm = 0.0
            previous_quality_operation = 0.0
            previous_quality_target = 0.0
        
            variation_crm = 0.0
            variation_operation = 0.0
            variation_target = 0.0
            
            previous_performance_growth_sales = 0.0
            previous_performance_profit = 0.0
            previous_performance_active_customer = 0.0
            
            variation_performance_growth_sales = 0.0
            variation_performance_profit = 0.0
            variation_performance_active_customer = 0.0
            
            performance_growth_sales = 0.0
            performance_profit = 0.0
            performance_active_customer = 0.0

            performance_growth_sales_summary = ''
            performance_profit_summary = ''
            
            yearly_performance_growth_sales = 0.0
            yearly_performance_profit = 0.0

            yearly_performance_growth_sales_summary = ''
            yearly_performance_profit_summary = ''
            
            budget_marketing_consumed = 0.0

            amount_in_late_more_than_15days = 0.0
            
            quality_crm = 0.0
            quality_score = 0.0
            goal_nb = 0
            
            target_achieved = 0
            target_total = 0
            
            today = date.today() 
            last_day_previous_month = today.replace(day=1) - timedelta(days=1)
            first_day_previous_month = last_day_previous_month.replace(day=1)
            first_day_year = first_day_previous_month.replace(month=1)
            
            quality_crm_ontime = self.env['crm.lead'].search_count([('probability', '<', 100), ('company_id', '=', subsidiary.id), ('team_id.x_studio_type', '=','Closing'), ('x_activity_ontime', '=',True)])
            quality_crm_all = self.env['crm.lead'].search_count([('probability', '<', 100), ('company_id', '=', subsidiary.id), ('team_id.x_studio_type', '=','Closing')])
            if quality_crm_all > 0:
                quality_crm = quality_crm_ontime / quality_crm_all
            
            for goal in self.env['gamification.goal'].search([("x_studio_company", "=", subsidiary.id),("challenge_id.challenge_category", "=", "hr"), ("x_studio_archived", "=", False), ("end_date", "=", last_day_previous_month)]):
                quality_score += goal.global_quality_score
                goal_nb += 1
                
                if goal.state == 'reached':
                    target_achieved += 1
                
            if goal_nb > 0:
                quality_operation = (quality_score / goal_nb) / 100
                quality_target = target_achieved / goal_nb
            
            previous_report = self.env['res.company.reports'].search([('company_id', '=', subsidiary.id), ('create_date', '>=', first_day_previous_month), ('create_date', '<=', last_day_previous_month)], limit=1)
            
            income = self.env['budget.line'].search([('general_budget_id', '=', 'TOTAL Income'), ('company_id', '=', subsidiary.id), ('date_to', '=', last_day_previous_month)], limit=1)
            if income.id != False: 
                performance_growth_sales = income.percentage
                performance_growth_sales_summary = str(int(income.practical_amount)) + " / " + str(int(income.planned_amount))

            
            profit = self.env['budget.line'].search([('general_budget_id', '=', 'TOTAL Profit'), ('company_id', '=', subsidiary.id), ('date_to', '=', last_day_previous_month)], limit=1)
            if profit.id != False: 
                performance_profit = profit.percentage
                performance_profit_summary = str(int(profit.practical_amount)) + " / " + str(int(profit.planned_amount))

            performance_active_customer = self.env['res.partner'].search_count([('status', '=', 'customer'), ('x_studio_customer_of', '=', subsidiary.id), ('is_company', '=', True)])
            
            #Yearly growth Sales
            incomes = self.env['budget.line'].search([('general_budget_id', '=', 'TOTAL Income'), ('company_id', '=', subsidiary.id), ('date_to', '>', first_day_year), ('date_to', '<=', last_day_previous_month)])
            planned_amount = 0.0
            practical_amount = 0.0
            for inc in incomes: 
                planned_amount += inc.planned_amount
                practical_amount += inc.practical_amount
            if planned_amount > 0:
                yearly_performance_growth_sales  = practical_amount / planned_amount
                yearly_performance_growth_sales_summary = str(int(practical_amount)) + " / " + str(int(planned_amount))
            
            #Marketing budget
            budget_marketing_allocation = practical_amount*10/100
            
            today = date.today()
            last_day_previous_month = today.replace(day=1) - timedelta(days=1)
            budget_marketing_allocation_projection = budget_marketing_allocation * 12 / last_day_previous_month.month
            
            marketing_budget = self.env['budget.line'].search([('crossovered_budget_id', '=', 'Marketing Expense'), ('general_budget_id', '=', 'TOTAL Profit'), ('company_id', '=', subsidiary.id), ('date_to', '>', first_day_year)], limit=1)
            if marketing_budget.id != False:
                budget_marketing_consumed = -marketing_budget.practical_amount
                
             
            
            #Yearly Profit
            profits = self.env['budget.line'].search([('general_budget_id', '=', 'TOTAL Profit'), ('company_id', '=', subsidiary.id), ('date_to', '>', first_day_year), ('date_to', '<=', last_day_previous_month)])
            planned_amount = 0.0
            practical_amount = 0.0
            for prof in profits: 
                planned_amount += inc.planned_amount
                practical_amount += inc.practical_amount
            if planned_amount > 0:
                yearly_performance_profit  = practical_amount / planned_amount
                yearly_performance_profit_summary = str(int(practical_amount)) + " / " + str(int(planned_amount))
                
            
            #Previous Report
            if previous_report.id != False: 
                previous_quality_crm = previous_report.quality_crm
                previous_quality_operation = previous_report.quality_operation
                previous_quality_target = previous_report.quality_target
            
                variation_crm = (quality_crm - previous_quality_crm) * 100
                variation_operation = (quality_operation - previous_quality_operation) * 100
                variation_target = (quality_target - previous_quality_target) * 100
                
                previous_performance_growth_sales = previous_report.performance_growth_sales
                previous_performance_profit = previous_report.performance_profit
                previous_performance_active_customer = previous_report.performance_active_customer
                
                variation_performance_growth_sales = (performance_growth_sales - previous_performance_growth_sales) * 100
                variation_performance_profit = (performance_profit - previous_performance_profit) * 100
                variation_performance_active_customer = (performance_active_customer - previous_performance_active_customer)

            #Amount in late
            duedate_minus15 = date.today() - timedelta(days=15)
            invoices = self.env['account.move'].search([('company_id', '=', subsidiary.id), ('move_type', '=', 'out_invoice'), ('state', '=', 'posted'), ('invoice_date_due', '<=', duedate_minus15), ('payment_state', '!=', 'paid'), ('payment_state', '!=', 'reversed') ])
            amount_in_late_more_than_15days = 0
            for invoice in invoices:
                amount_in_late_more_than_15days += invoice.amount_residual
            
            #creation
            values = {
                    'company_id' : subsidiary.id,
                    'quality_crm' : quality_crm,
                    'quality_operation' : quality_operation,
                    'quality_target' : quality_target,
                    'previous_quality_crm': previous_quality_crm,
                    'previous_quality_operation': previous_quality_operation,
                    'previous_quality_target' : previous_quality_target,
                    'variation_crm' : variation_crm,
                    'variation_operation' : variation_operation,
                    'variation_target' : variation_target,
                    'performance_growth_sales' : performance_growth_sales,
                    'performance_profit' : performance_profit,
                    'performance_active_customer' : performance_active_customer,

                    'performance_growth_sales_summary' : performance_growth_sales_summary,
                    'performance_profit_summary' : performance_profit_summary,
                    
                    'previous_performance_growth_sales' : previous_performance_growth_sales,
                    'previous_performance_profit' : previous_performance_profit,
                    'previous_performance_active_customer' : previous_performance_active_customer,
                    
                    'variation_performance_growth_sales' : variation_performance_growth_sales,
                    'variation_performance_profit' : variation_performance_profit,
                    'variation_performance_active_customer' : variation_performance_active_customer,

                    'yearly_performance_growth_sales' : yearly_performance_growth_sales,
                    'yearly_performance_profit' : yearly_performance_profit,

                    'yearly_performance_growth_sales_summary' : yearly_performance_growth_sales_summary,
                    'yearly_performance_profit_summary' :  yearly_performance_profit_summary,
                    
                    'budget_marketing_consumed' : budget_marketing_consumed,
                    'budget_marketing_allocation_projection' : budget_marketing_allocation_projection,
                    'budget_marketing_allocation' : budget_marketing_allocation,

                    'amount_in_late_more_than_15days' : amount_in_late_more_than_15days,
                    
                
                }
            report = self.env['res.company.reports'].search([('company_id', '=', subsidiary.id), ('create_date', '>', last_day_previous_month)], limit=1)
            if report.id == False:
                self.env['res.company.reports'].create(values)
            else:
                report.update(values)
                
            

