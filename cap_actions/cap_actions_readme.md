# Cap Actions 

## Version
Odoo 19.0

## Dependencies
1. base  
2. hr  

## Description
This module allows you to define, generate, and track **organizational actions** with responsible users, substitutes, and sequential validators. It is designed to automate recurring tasks, ensure timely validation, and maintain scoring/probability for responsible users and validators.

## Features
- **Meta Templates for Rules:**  
  Define conditions that determine when an action should be created automatically (e.g., specific weekdays, date ranges, or custom expressions).  

- **Template Templates for Workflow:**  
  Set default substitutes and validators for each workflow to ensure proper sequencing and approvals.  

- **Action Templates:**  
  Assign responsible users, deadlines, frequency, score impact, and link templates for automated creation of actions.  

- **Automated Action Generation:**  
  Actions can be generated manually or via cron jobs, based on frequency and template rules.  

- **Sequential Validation:**  
  Actions are validated in order by assigned validators. Each validator can approve (OK) or reject (KO), triggering score/probability updates.  

- **Substitutes:**  
  Assign substitute users to automatically replace absent responsible users.  

- **Scoring & Probability Tracking:**  
  Validator performance affects probability calculations, improving accountability and workflow efficiency.  

  
### Workflow:
1. Cron or manual trigger creates the action if all conditions are met.  
2. Responsible user completes the task.  
3. Validators approve sequentially.  
4. Failed validations update probability and may revert action status.  

This ensures actions are completed on time, properly validated, and tracked for scoring.

## Author & Maintainer
CAPTIVEA INDIA
