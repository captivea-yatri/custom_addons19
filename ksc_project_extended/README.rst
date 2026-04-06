# Project Extended By Captivea

## Version
Odoo 18.0

## Dependencies
1. hr
2. sale_timesheet_enterprise
3. project_forecast
4. documents_project
5. base_automation
6. cap_partner

## Description
This module extends Odoo’s Project and Timesheet applications by adding automation, validations, UI improvements, task color indicators, and portal integration.
It enhances project management, customer invoice tracking, task creation behavior, and timesheet logging rules based on business constraints. We also handle
internal project quotas for the internal projects of Captivea LLC, Captivea France, Captivea Luxembourg, and Captivea France North.

## Features
Here are the main features of this module:
- **use_documents on Project:**
  Provide direct link with project related documents.
- **Options exclude from quality issue types on Project:**
  Checkbox for each quality issue type based on project if true: exclude from quality issue types for project.
- **number_of_days_authorized_to_backlog_timesheet on Company:**
  number_of_days_authorized_to_backlog_timesheet field on company with the help of this field we grant additional time
  to log timesheet for all the customers. If 5 days are set on company that means, if the customer is 5 days with late
  payment then also user can log timesheet for that customer's project.
- **Automatic send mail to salesperson:**
  An email is sent daily to the salesperson of a customer to follow up on pending payments. If the
  number_of_days_authorized_to_backlog_timesheet field in the company is set to 5 days, the email will be sent to the
  salesperson for five consecutive days for customers who are overdue on their payments.
- **Color Computation of Project, Task & Timesheet:**
  In the project, task, and timesheet, we have a field for color, which we set based on the follow-up status of the
  customer. This field manages the color computation for the project, task, and timesheet. Based on the color
  computation for the project and task, we manage timesheet logging.
- **On Hold Reason Field on Project:**
  If the 'on hold' reason is set for a project, the user will not be able to log timesheets for this project.
  Additionally, the 'on hold' reason is automatically set based on certain conditions: if all hours are consumed, the
  'on hold' reason for the project is automatically set to 'No Hours.' If the customer has not made the payment even
  after the due date has passed, the 'on hold' reason is automatically set to 'Late in Payment'.
- **Manage project and task's views:**
  In the Kanban view, display a message indicating whether the user can add a timesheet to the project or task.
  This should be determined based on the on-hold reason and the color computation logic.
- **Default Assignation on Task:**
  Checks if the project's PM is set, and if a task is created for this project, the task's assignee is automatically set
  to the project's PM. This scenario also applies when updating a task: if there are no assignees and the project has a
  PM set, the assignee is also set to the project's PM.
- **Authorized Invoicing Amount Field on Sale Order:**
  This field only works for products based on timesheets. If we sell a product that is based on timesheets and set an
  authorized invoicing amount on the sales order, then users will be able to log timesheets for which the total (unit
  amount * price per unit) is less than or equal to the authorized invoicing amount specified on the sales order. If an
  invoice is not created, users cannot log timesheets for this sales order line. When an invoice is created, the amount
  is refreshed.
- **x_studio_block_timesheet_log Field:**
  If x_studio_block_timesheet_log is True on a sale order, users will not be able to log timesheets for projects linked
  with that sale order.
- **Restrict Manual Timesheet on Project:**
  If restrict manual timesheet is True on a project, users will not be able to log timesheets directly for this project.
- **Cannot Reduce Past Month Timesheet:**
  User cannot reduce or delete past month timesheet if he cannot has group "Reduce Past Month Timesheet".
- **x_studio_autovalidate_timesheet on Employee:**
  If x_studio_autovalidate_timesheet is True on a employee, the timesheet Employee log is automatically validated.
- **Internal Project Quotas:**
  If the project's customer is Captivea LLC, Captivea France, Captivea Luxembourg, or Captivea France North, the user is
  only allowed to log timesheets up to the quota allocated to them in internal project quotas.

## Author & Maintainer
CAPTIVEA INDIA
