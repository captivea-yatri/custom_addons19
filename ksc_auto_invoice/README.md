================================================
Odoo 19 KSC Auto Invoice
================================================

This Module Implements the functionality of creating invoice automatically through scheduled action,creating invoice automatically if advanced payment type product is in order lines and  also adds security deposit in order line of invoice if enabled


============
Odoo Version
============
Odoo 19.0


============
Dependencies
============
1) sale
2) sale_margin
1) sale_timesheet
2) account
2) mail
2) cap_account_intern_company_transection
2) timesheet_grid
2) project_forecast
2) sale_subscription


=====================
Detailed Information
=====================
Follow steps to avail functionality:
(1) Automatic Invoice if Invoicing Policy is Prepaid/fixed Price :
    - Go to Sale application and in quotations menu item, create new quotation
    - fill in all required fields and add the product in sale order line section, of which invoicing policy is "Prepaid/fixed Price"
    - make sure that "online payment" check box is cleared in "sales" section of "Other info" tab
    - save and confirm sale order
    - as you can see, invoice for same order is automatically created
(2) Automatic Invoice on scheduled action named "Automatically Invoice" if Invoicing Policy is Based on timesheet :
    - follow functionality (1) and during selecting product, select product with Invoicing Policy is "Based on timesheet"
    - in "Automated Invoice" section of "Other info" tab, you can see the drop down list with options "Not activated", "Activated last day of month" and "Activated at specific day"
    - if "Not activated" is selected, automatic invoicing feature will stay inactive
    - if "Activated last day of month" selected, invoice will be created automatically only for sale order line time sheet items which was created before last day of previous month
    - if "Activated at specific day" selected, you will have option for selection before which day, you want to create invoice automatically 
    - also below "Automatically Invoice" field, you have another field "Invoice Action", which will decide whether you want to create invoice in either "Draft" state,"Confirm" state or you want to confirm and send invoice to customer
    - below "Invoice Action" field, there is field name "Minimum amount to invoice", in which you can set the amount and during creating automatic invoice, it will only create invoice of which sale order amount is greater than set value in field
    - also there is a checkbox named "Invoice for Group Riss" added on project form in "Time Management" section of "Setting" tab
    - if check box selected, automatic invoice will be created on another scheduled action named "INVOICE RISS GROUP"
    
(3) Security Deposit Functionality:
    - Security Deposit refers to an amount of money paid by the customer in advance and held in reserve, in the exchange of the services that we are providing
    - Go on the companies and set the security deposit account on any one company of type current liabilities (Note:If no account is set on the security deposit than this functionality will not work for that company.)
    - security deposit line will be automatically added at the time of invoice creation in above mentioned step (1) and (2) with the round off “500” 
    - Security deposit will always in round of 500. If the invoice amount is 510 $ than the security deposit will be created of 1000 $
    - If the invoice amount is less than then 500$ than no security deposit will be created 
    - to disable the security deposit for that specific customer, fill the checkbox De-activate security deposit on companies form


===================
Author & Maintainer
===================

This module is maintained by the "Captivea India"
