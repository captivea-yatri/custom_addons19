================================================
Odoo 18 KSC Automatic Compensation
================================================

This Module Implements the functionality For a contact, whether vendor/customer we can auto compensate the invoice and bills by reconciling invoice and bill against each other


============
Odoo Version
============
Odoo 18.0


============
Dependencies
============
1) account


=====================
Detailed Information
=====================
Follow steps to avail functionality:
(1) Create a bill for the company by going into accounting > vendors > bills and confirm it
(2) create an invoice for the same customer that you created bill in previous step and confirm it also
(3) you can see 'compensate' button next to "reset to draft" button in button header section
(4) if you go back to bill that you have created, you can see "compensate" button over there too
(5) by clicking on "compensate" button of any of above record that is invoice or bill, wizard will pop up with list of invoice or bills that are available to compensate
(6) select required records from list by selecting checkbox and click on "Reconcile" button, and after that system will reconcile current record with the one you have selected in wizard and will show due amount below record if amount is not fully reconciled

===================
Author & Maintainer
===================

This module is maintained by the "Captivea India"
