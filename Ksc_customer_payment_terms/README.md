================================================
Odoo 17 Customer Payment Terms
================================================

This Module Implements Advanced Features for Customer Payment Terms


============
Odoo Version
============
Odoo 17.0


============
Dependencies
============
1) account
2) payment
3) sale


=====================
Detailed Information
=====================
Follow steps to avail functionality:
(1) go to accounting>configuration>payment terms and set up any 2 nos of payment term 
(2) go to form view of any payment term and you can see two check boxes that are "Default" and "Default After First Payment"
(3) rule is set so that you can set these check box active in only one payment term
(4) while creating new company, on company form view, in sales section of sale & purchase tab, payment term in which you have checked "Default" check box will be automatically populated
(5) once invoice of first sale order of this new customer gets paid,while creating second sale order of this company, payment term in which you have checked "Default After First Payment" check box will be automatically populated 
(6) this module basically sets different payment terms for new customer and trusted customers

===================
Author & Maintainer
===================

This module is maintained by the "Captivea India"
