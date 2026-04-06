# Sale Project Extended (By Captivea)

## Version
Odoo 19.0

## Dependencies
1. sale_timesheet
2. sale_project
3. crm
4. account_followup

## Description
This module extends Odoo’s Sales, Project, and CRM applications with enhancements designed for service-based businesses and companies selling prepaid hours. It simplifies project creation from sale orders, improves tracking of consumed and remaining hours, and automates yearly price increases for recurring service contracts.

It also adds controls to maintain data accuracy, such as enforcing minimum sale prices, restricting product description edits, and displaying consumed hours directly on sale order lines.
On the CRM side, the module automatically classifies new leads as opportunities, updates the expected revenue based on sale orders, and records the win date when an opportunity reaches 100% probability.

Overall, this module provides better visibility, automation, and consistency across Sales, Project, and CRM processes.


###### Features

### 🔹 Sales Enhancements

**Create or Link Projects from Sale Orders**
Easily create a project or link an existing one directly from the sale order.

**Minimum Sales Price Validation**
Ensures the sale order line price cannot be lower than the product’s minimum allowed sale price.

**Restrict Product Description Editing**
Products can be marked to prevent users from modifying their descriptions on sale order lines.

**Consumed Hours on Sale Order Lines**
Displays how many hours have been consumed for prepaid service products.

**Remaining Hours Tracking**
Automatically calculates total remaining hours for prepaid service lines.

**Automatic Activities for Low Hours**
Creates reminders for the salesperson when prepaid hours reach 20% or are fully consumed.

**Yearly Price Increase Automation**
Based on the company’s yearly increase rate:
    Automatically increases the price of delivered-timesheet services.
    Updates last and next update dates.
    Can be disabled per order.

### 🔹 CRM Enhancements

**Expected Revenue Update from Sale Order**
Opportunity expected revenue syncs automatically with the sale order's untaxed amount.

**Auto-Computed Win Date**
When an opportunity reaches 100% probability, the win date is set automatically.

**Automatic Lead → Opportunity Conversion**
Every new CRM lead becomes an opportunity by default.

### 🔹 Additional Controls

**Company-Based Increase Rate Defaults**
New sale orders automatically use the company’s yearly increase rate unless manually changed.

