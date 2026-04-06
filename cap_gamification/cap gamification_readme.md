================================================
Odoo 19 Cap Gamification
================================================

This Module Improves the feature of default odoo Gamification


============
Odoo Version
============
Odoo 19.0


============
Dependencies
============
Following Modules must be already installed.
1) gamification
2) project
3) hr



=====================
Detailed Information
=====================
Follow steps to avail functionality:
To explore this functionality, make sure that you are creating Goal challenges
(1) Go to Badges => added field quest_bonus, you can not add value less then zero , 
(2) Added field Quest Bonus on Goal gamification  => which get total_quest_bonus from badge 
(3) Added field Hours Of Internal P2 P3 => which store unit amount of timesheet
(6) Added field Current Value with Internal P2 P3 on Goal => which store  Hours Of Internal P2 P3 + Current Value
(7) Return the start and end date for a goal period based on today
(8) (start_date, end_date), dates in string format, False if the period is not defined or unknown
(9) Create goals that haven't been created yet (eg: if added users) Recompute the current value for each goal related

===================
Author & Maintainer
===================

This module is maintained by the "Captivea India"
