-- Delete the configuration parameters in Neutralize mode

DELETE FROM ir_config_parameter WHERE key = 'cap_hr_skill.url';
