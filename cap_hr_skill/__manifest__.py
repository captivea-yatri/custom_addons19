# -*- coding: utf-8 -*-
{
    'name': "Cap Hr Skill",
    'summary': """Module helps to manage skill and skills point""",
    'description': """Using this module user can ask to review there skill and validate. 
    Once the skill will be validated, skill will be added automatic to employee. 
    ALl the point will get calculated automatic as functional knowledge and global knowledge.""",
    'author': "Captivea",
    'website': 'www.captivea.com',
    'category': 'hr',
    'version': '19.0.0.1.1',
    'license': 'LGPL-3',
    'depends': ['base','hr', 'hr_skills', 'mail', 'survey'], #need to check that can we need cap_domain module in dependancy??
    'data': [
        "security/ir.model.access.csv",
        "data/ir_config_parameter_data.xml",
        "views/hr_skill_inherit_view.xml",
        "views/domain_skill_view.xml",
        "views/employee_inherit_view.xml",
        "views/hr_skill_validator_view.xml",
        "views/skill_validation_request_view.xml",
        "views/res_config_setting_view.xml",
        "views/survey_retry.xml",
    ],
    'installable': True,
    'auto_install': False,
}
