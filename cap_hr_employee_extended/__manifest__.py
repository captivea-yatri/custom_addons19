# -*- coding: utf-8 -*-
{
    'name': "Hr Employee Extended",
    'summary': """Employee Extended module mainly used to manage all view for internal user""",
    'description': """""",
    'author': "Captivea",
    'website': 'www.captivea.com',
    'category': 'hr',
    'version': '19.0.0.1',
    'license': 'LGPL-3',
    'depends': ['base', 'documents_hr', 'hr_appraisal', 'cap_hr_skill', 'hr_attendance', 'hr_holidays',
                'hr_timesheet','hr'],
#check all the dependancy 
    'data': [
        "security/hr_employee_extended_group.xml",
        "security/ir.model.access.csv",
        "views/hr_employee_extended_view.xml",
        "views/hr_employee_extended_public_view.xml"
    ],
    'installable': True,
    'auto_install': False,
}
