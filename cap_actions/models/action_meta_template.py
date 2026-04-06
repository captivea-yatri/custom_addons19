from odoo import fields, models, api
from datetime import date, timedelta

class ActionMetaTemplate(models.Model):
    _name = 'action.meta.template'
    _description = 'Action Meta Template'
    
    description = fields.Html(string='Description')
    name = fields.Char(string='Name')
    
    eval_expresion = fields.Text(string='Python Code')

    def evaluate(self, company_id):
        """
              Evaluate the meta-template expression for the given company.

                Behaviour
                ---------
                - If `eval_expresion` is empty or False, returns False.
                - Otherwise evaluates the expression in a restricted context and
                  returns the result of that evaluation.

                Context available inside the expression
                --------------------------------------
                - company_id (int): the id of the company passed to evaluate().
                - self (record): the ActionMetaTemplate record on which evaluate() was called.
                - today (date): datetime.date.today() for convenience.

                Return value
                ------------
                - Expected: boolean (True means "allow action creation"; False means "do not create").
                - If the expression returns a non-boolean value it will be returned as-is
                  (caller should treat truthiness accordingly).
        """
        if self.eval_expresion != '' and self.eval_expresion!= False:
            return eval(self.eval_expresion, {'company_id':company_id, 'self':self, 'today':date.today()})
        return False
