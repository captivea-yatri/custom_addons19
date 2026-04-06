================================================

Custom Module: cap_automatic_deferred_earning_account

============
Odoo Version
============
Odoo 19.0

============
Dependencies
============
Following Modules must be already installed.

=> 'product', 'account_asset', 'base', 'ksc_sale_project_extended','sale_project'


=====================
Configurations
=====================

On Company level: -
You need to define "Time Credit Configuration" on the company level.
Please configure, Revenue Enquiry User, User Closing Sale Order, Months after credit time expires and Time Credit Config.

In Deferred Revenue Account, assign the account of type current liabilities.
In Revenue Account, assign the account of type income.
Assign or Create Journal of miscellaneous type as Deferred Revenue Journal

On Product Level: -
You need to configure these following things: -
The product should be service type product and keep the Unit of measure in 'Hours' for better calculation.
Keep the Product Invoicing Policy to 'Prepaid/Fixed Price'.
Keep Product To Receive marked as True.
In the Accounting, "Income Account" should be any of the "Deferred Revenue Account", set on the Company level.
Also, set the Cost Price, Sales Price and Minimum Sales Price.



=====================
Functionalities
=====================
(1) creating time credit from sale order through server and schedule action automatically

Create a new SO with the Products consisting of hours. Confirm the sale order and create a new project or link an existing project.
After creating a new project, create and confirm the invoice.
You can either click on action menu(gear icon) and select the option "Create Time Credit" or this action is automatically managed by the scheduled action.(Create Time Credit for sale order with state is need to be created)

(2) posting time credit journal entries as per logged time sheet automatically
Once the project is created, review the project and you can do the task creation and in the task, you can do timesheet entry.
The Project tasks Smart button present in the Sale Order will redirect the user to create tasks and in tasks, user can do the timesheet entry.

(3) closing time credit manually through button and automatically through scheduled action
Once, all the time sheet entries are partially or fully entered, you can click on "Close Time Credit" button, or this action is automatically managed by the scheduled action(Time Credit Compute Credit Revenue Line(Add month line by project - Monthly on the 5th)).

(4) automatic reconciliation of time credit journal items with invoice
This feature will automatically reconcile the time credit journal items with invoice lines items. 
You can click "Time Credit Deferred Revenue" smart button >  In the time credit form view, you can see "Posted Credit Entries" > Open Any Journal Entry form view and click the "Reconciled Items" smart button > Here you will see the reconciliation of time credit journal items with invoice line items.

(5) time credit synchronization status management of partner / contact from accounting point of view
You can review how much time is consumed for a particular customer.
Got to the Customer for which we have related sale order and Project. > In the Accounting Tab/Page, you will see "Credit Time Status" group/section.
Here you can see, Credit Time Balance, Deferred Revenue Balance and Synchronization Status fields.

(6) supports multi-currency and multiple time credit for a sale order
You can select a Pricelist in Sale order in Different currency, but the time credit for the sale order will be created in company currency.

===================
Author & Maintainer
===================

This module is maintained by the "Captivea India"
