{
    'name': 'Employee Management KSC',
    'version': '1.0',
    'category': 'Human Resources',
    'summary': 'Manage employees, departments, shifts and leaves',
    'description': 'Module to manage employee, department, shifts, and leaves with hierarchical permissions.',
    'depends': ['base', 'hr'],
    'data': [
        'security/ir.model.access.csv',
        'views/employee_department_views.xml',
        'views/employee_shift_views.xml',
        'views/employee_views.xml',
        'views/employee_leave_views.xml',
    ],
    'installable': True,
    'application': True,
}
