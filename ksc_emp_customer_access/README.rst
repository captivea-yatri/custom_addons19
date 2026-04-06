# Manage Customer Access By Captivea

## Version
Odoo 19.0

## Dependencies
1. base
2. mail
3. project_todo
4. access_rights_management

## Description
The goal of this module is to enhance the management of access rights for team operations.
Within this system, users can submit access requests for specific contacts. Upon approval from their manager, users are
granted read and write access to all projects & tasks also read access for sales orders associated with that customer.

## Features
Here are the main features of this module:
- **Access Request:**
  Users can create access requests from the "Access Request" menu or by using the smart button labeled "Access Request"
  on contact records
- **Check Access for Employee:**
  There is a scheduled action that runs monthly to check for any access requests older than one year. If such requests
  are found, their state is changed to "Renewal," and an activity is created for the manager. This allows the manager to
  review the request and reject it if the user is no longer working on the customer's project. Consequently, access to
  this customer is revoked, improving overall access management.
- **Auto-create and Approved Request for Manager:**
  When a user is assigned as a manager for another user, the system reviews all requests approved for the child user.
  It then creates and approves requests for the same customer on behalf of the child user, allowing the manager to
  better oversee and manage both projects and the child user’s activities.

## Author & Maintainer
CAPTIVEA INDIA
