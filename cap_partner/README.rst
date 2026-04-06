# Cap Partner By Captivea

## Version
Odoo 19.0

## Dependencies
1. base
2. website
3. project
4. account
5. ksc_sale_project_extended

## Description
The Cap Partner module extends Odoo to provide enhanced management of partners (customers and companies) and projects,
offering specialized fields, automation, and reports. It is designed to help sales, project management,
and accounting teams efficiently track customer engagement, project statuses, and invoicing details,
while ensuring compliance with internal business rules.

## Key Features
Here are the main features of this module:
1. Customer Status Automation

- Daily automated updates of customer status based on projects, timesheets, and sales orders.

-Determines if a partner is an Active, Inactive, Old, or Not a Customer based on historical engagement.

-Automatically sets appropriate sales status such as Active Pay as you go or Active Payment in Advance.

-Supports parent-child partner relationships to handle corporate accounts with multiple subsidiaries.

2. Project Status Tracking

-Adds a Project Status field to projects and tasks.

-Defines various project stages, such as:

-Analysis

-Pre-Live Configuration

-Live

-Dead

-Duplicate

-Internal

-Internal P2 P3

-Analytic entries automatically inherit the project status at the time of logging, ensuring accurate reporting and analytics.

3. Enhanced Partner Data

-Additional fields on partner/company records:

-Maintenance Support Terms (HTML)

-Number of Days Authorized in Late

-Validates that late days cannot be negative.


4. Customer Seniority on Invoices

-Computes the number of days a customer has been active.

-Categorizes customers as New or Existing based on seniority (>365 days).

-Adjusts invoice data to include partner-specific bank accounts.

5. Sales Order Enhancements

-Tracks the Quotation Sent Date automatically when quotation is sent.

-Option to display Maintenance and Support Terms on sales orders.

-Sales order reports and portal views are customized to include maintenance terms when applicable.

-Automatically removes invoice narration for cleaner documentation.

-Invoice values inherit partner-specific bank accounts for easier payments.

6. CRM Integration

-Prevents internal company partners from being assigned to opportunities.

-Helps maintain clean CRM data and avoids misassignment of opportunities.

7. Security and Access Control

-New user groups for controlled actions:

-Can change customer status

-Authorize to unlock customer

-Specific model-level access rights:

-Mark customer lost

-Manage project statuses

8. Automation & Cron Jobs

-Daily cron jobs manage customer status automatically.

-Tracks engagement metrics using project activity and timesheets to maintain up-to-date customer classifications.


## Author & Maintainer
CAPTIVEA INDIA
