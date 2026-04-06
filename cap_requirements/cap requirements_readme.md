================================================
Odoo 18 cap requirements
================================================

Custom Module cap requirements

============
Odoo Version
============
Odoo 18.0

============
Dependencies
============
Following Modules must be already installed.

1) cap_domain
2) planning
3) sale_timesheet

=====================
Detailed Information
=====================
Here are the main features of this module:
- the template requirement which is standard data, The requirements of the clients that is further created into the project requirements. 
 Project >> Requirement Admin >> Template Requirement
- the project requirement is created based on the template requirement related to the domain.
Project >> Requirement Admin >> Project Requirement
- Project requirements refer to the specific  objectives, functionalities, and features that project must meet or possess to be considered as successful or completed
- There is smart button on the project to access project requirement, "Requirement for Workshop" and "Requirement for Analysis" from which we can access the project requirement. 
- To calculate the time required automatically from template requirement data, a button on project “Calculate advised estimated time” is available.
- There is a button “Create Task From Project Requirement” as soon as we click that button we will have a wizard where user needs to select a phase. Based on the Phase that is selected, system will search for all the project requirement  belongs with the same phase and will create task by extracting the detail from the project requirement related to that project.
- Meta template requirement is configuration that will be done once by administrator to have estimated time calculation dynamically. This calculation will have effect on project requirement and with that on project domain. 
Project >> Requirement Admin >> Meta Template Requirement
Project >> Requirement Admin >> Meta Project Requirement
- When on any requirement we need calculation dynamically, we will need to configure meta template requirement and meta project requirement


===================
Author & Maintainer
===================

This module is maintained by the "Captivea India"
