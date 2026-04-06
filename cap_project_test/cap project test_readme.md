================================================
Odoo 18 cap project test
================================================

Custom Module cap project test

============
Odoo Version
============
Odoo 18.0

============
Dependencies
============
Following Modules must be already installed.

1) cap_requirements
2) cap_project_feedback
3) cap_quality_issue_log


=====================
Detailed Information
=====================
Follow steps to avail functionality cap project test:
Note===> .
-   user can set phases of project in tab 'Phase' on project task
-   user or administrator can create template test which is template for customer's requirements
-   Task Test will also get created based on the Template test that is configured along with the tasks
-   all the execution test will get created from the Task Test
-   session test means there will be a session which will hold multiple execution test(test cases) that can be of same task or different task. We will need to create at least one session test from back-end to get menu visible on the portal to customer of that particular project.
-   there is “Initialize Test” button on session test to create execution test 
-   project => smart button=> there is smart button => session test, task test, execution test.
-   project=> button => create task from project requirement , then task and task test will creates,
-   project=> smart button => create session manually,
-   session test=> there is button initialize task => will create execution test and task validation status
-   Task Validation Status means what will be the status of the task with this session.

===================
Author & Maintainer
===================

This module is maintained by the "Captivea India"
