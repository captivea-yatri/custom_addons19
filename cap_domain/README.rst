# Cap Domain By Captivea

## Version
Odoo 17.0

## Dependencies
1. timesheet_grid
2. planning
3. ksc_project_extended

## Description
This module enhances the management of projects, tasks, timesheets, and customer relationships by introducing Default Domains,
Project Domains, automated role management, and a customer follow-up tracking system. It ensures cleaner configuration, better resource visibility,
and improved customer engagement through structured follow-up scheduling.

## Features
Here are the main features of this module:
- **Default Domain:**
  The main configuration for managing projects, tasks, and timesheets.
- **Project Domain:**
  It is automatically created for an individual project based on the default domain for project-specific ideas.
- **Auto Set & Remove Users In Fields Business Analyst, Developer, & Configurators on Project:**
  We have roles field on the project: Business Analyst, Developer, and Configurator. Each task has a 'role ID' field
  where we can assign roles such as Project Manager, Business Analyst, Developer, Configurator or Architecture.
  Now, with the help of this functionality, when a user logs their timesheet, it checks which role (set on the task the
  user is logging time against) they belong to. If a user is not included in these roles for the project, The Schedular
  automatically added to the project. If a user has not logged timesheets in the last 30 days but is still assigned a
  role on the project, Schedular removed from the project's role field.
-**customer follow-up tracking system:**
  It allows setting a follow-up frequency (monthly/quarterly/semester/annually) and automatically computes the last and next follow-up dates based on customer interactions.
  A scheduled cron job marks customers whose follow-up is due and displays a red/green status indicator on the partner form.
  Only authorized roles (President/CEO/VP Sales) can modify the follow-up frequency.
  The feature helps teams maintain consistent communication and ensures no customer follow-ups are missed.

## Author & Maintainer
CAPTIVEA INDIA
