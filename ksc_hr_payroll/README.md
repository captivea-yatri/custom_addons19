====================================
Odoo 18 Payroll Accounting Extended
====================================

This Module extends the functionality of odoo's Payroll module and allows user to generate draft journal item for payment of employee's salaries and also pay it.
it also allows above mentioned functionality for batch of employees with same salary structure to pay their salaries in batch


============
Odoo Version
============
Odoo 18.0


============
Dependencies
============
Following Modules must be already installed to have Cap Marketing CRM Automation functionality
1) hr
2) hr_payroll
3) hr_payroll_account
4) l10n_in_hr_payroll



=====================
Detailed Information
=====================
Follow steps to avail functionality:
(1)Go to apps and install Payroll Accounting Extended
(2)Create user and employee from user form and fill necessary details for employee
(3)on employee form, on "HR Settings" tab, in "status" area, you have option to select partner for employee, select partner for employee and save Employee form
(4)on employee form, in header, click on 'contract'smart button and create contract for employee by filling necessary details 
(5)during filling out details on contract form, make sure below things:
    - proper salary structure type is been configured 
    - proper wage and wage type is specified in salary information tab
    - proper contract type,start date and end date is specified
(6)Go to Payroll app, on top menu bar click on payslips>all payslips and click on New button to create new payslip for above configured employee
(7)fill out necessary details that is period for which salary is to be paid, related contract, batch if it belongs to any and structure 
(8)after filling all details, click on "Compute Sheet" button to make odoo calculate salary as per specified salary structure
(9)you can see all computation on "Salary Computation" tab of employee payslips form and also "Create Draft Entry" button is visible
(10)click on "Create Draft Entry" for creating draft journal item, and you can see that draft entry is automatically populated in Accounting Entry field of other info tab of Employee payslips form
(11)click on Accounting Entry field link and post the journal item to proceed for payment
(12)once journal item is posted, you can do payment for salary by clicking on Pay button 
(13)to create salary payment to batch of employees, on payroll dashboard, click on Payslips>Batches and create new batch by clicking on New button
(14)click on generate payslips button to select employees for which we wanted to create payslips
(15)on generate payslips wizard which opens after clicking on generate payslips button, select salary structure type of which you wanted to generate batch payment, and you can see that all employees with selected salary structure is automatically populated in employee lines, click on generate to create payslips
(16)on batches form, create and post entries button is now visible and all payslips is been created which can be accessed with smart button in header
(17)click on create and post entries button, and journal item is automatically created and posted for all payslips
(18)click on register payment button to register payment and payment will be done for batch of employees


===================
Author & Maintainer
===================

This module is maintained by the "Captivea India"
