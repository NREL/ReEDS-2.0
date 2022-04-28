
USER_RESET_EMAIL_SUBJECT = 'Your new ReEDS India password awaits!'
USER_SIGNUP_EMAIL_SUBJECT = 'Your link to ReEDS Inida Signup awaits!'
USER_SIGNUP_EMAIL_REJECT_SUBJECT = 'Unfortunately your request for ReEDS Inida Signuo is Rejected!'
USER_SIGNUP_REQUEST_SUBJECT = 'New request for user sign up awaits!'
USER_WELCOME_EMAIL_SUBJECT = 'Your new ReEDS India account awaits!'
REEDS_SIM_INITIATION_SUBJECT = f'Congratulations your simulation is starting!'
REEDS_SIM_INQUEUE_SUBJECT = f'Your Simulation is in Queue!'
REEDS_SIM_COMPLETE_SUBJECT = f'Your Simulation is Complete!'
REEDS_PASSWORD_CHANGE_SUBJECT = f'You password has been Changed!'

REL_URL_TO_SERVICE_DICT = {
    '/api/health': 'health', # Auth not needed
    '/api/run_model': 'simulation',
    '/api/get_scenarios': 'get_scenarios',
    '/api/update_scenarios': 'update_scenarios',
    '/api/clone_scenarios': 'clone_scenarios',
    '/api/delete_scenarios': 'delete_scenarios',
    '/api/get_output_metadata': 'get_output_metadata',
    '/api/delete_output_metadata': 'delete_output_metadata',
    '/api/get_scenario_list': 'get_scenario_list',
    '/api/user-sign-up': 'user_sign_up', # Auth not needed
    '/api/user-login': 'user_login', # Auth not needed
    '/api/authenticated': 'authenticated',
    '/api/update_password': 'update_password',
    '/api/profile_data': 'profile_data',
    '/api/update_profile_data': 'update_profile_data',
    '/api/report_bug': 'report_bug',
    '/api/list_bugs': 'list_bugs',
    '/api/upload_label': 'upload_label',
    '/api/get_labels': 'get_labels',
    '/api/delete_label': 'delete_label',
    '/api/add_card_label': 'add_card_label',
    '/api/get_scenario_labels_list': 'get_scenario_labels_list',
    '/api/remove_card_label': 'remove_card_label',
    '/api/update_label_status': 'update_label_status',
    '/api/get_lable_statuses': 'get_lable_statuses',
    '/api/update_personnel_scen_state': 'update_personnel_scen_state',
    '/api/delete_personnel_scen_state': 'delete_personnel_scen_state',
    '/api/update_default_scen_state': 'update_default_scen_state',
    '/api/get_default_scen_state': 'get_default_scen_state',
    '/api/update_output_card_state': 'update_output_card_state',
    '/api/get_download_token': 'get_download_token',
    '/api/validate_csv': 'validate_csv', # No auth required
    '/api/user/reset_password': 'user_reset_password', # No auth required
    '/api/user-sign-up-request': 'user_sign_up_request',
    '/api/get-users-request': 'get_users_request', 
    '/api/admin_authenticated': 'admin_authenticated',
    '/api/approve-request': 'approve_request',
    '/api/delete-user-request': 'delete_user_request',
    '/api/reject-user-request': 'reject_user_request'
}

DEFAULT_RATES_FOR_ALL_USERS = {
    'simulation': {'max_token': 20, 'rate_pm': 0.007},
    'get_scenarios': {'max_token': 200 , 'rate_pm': 60 },
    'update_scenarios': {'max_token': 200 , 'rate_pm': 60 },
    'clone_scenarios': {'max_token': 200 , 'rate_pm': 60 },
    'delete_scenarios': {'max_token': 200 , 'rate_pm': 60 },
    'get_output_metadata': {'max_token': 200 , 'rate_pm': 60 },
    'delete_output_metadata': {'max_token': 200 , 'rate_pm': 60 },
    'get_scenario_list': {'max_token': 200 , 'rate_pm': 60 },
    'authenticated': {'max_token': 500 , 'rate_pm': 60 },
    'update_password': {'max_token': 5 , 'rate_pm': 0.0035 },
    'profile_data': {'max_token': 200 , 'rate_pm': 60 },
    'update_profile_data': {'max_token': 10 , 'rate_pm': 0.007 },
    'report_bug': {'max_token': 20 , 'rate_pm': 0.014 },
    'list_bugs': {'max_token': 100 , 'rate_pm': 5 },
    'upload_label': {'max_token': 200 , 'rate_pm': 60 },
    'get_labels': {'max_token': 200 , 'rate_pm': 60 },
    'delete_label': {'max_token': 200 , 'rate_pm': 60 },
    'add_card_label': {'max_token': 200 , 'rate_pm': 60 },
    'get_scenario_labels_list': {'max_token': 200 , 'rate_pm': 60 },
    'remove_card_label': {'max_token': 200 , 'rate_pm': 60 },
    'update_label_status': {'max_token': 200 , 'rate_pm': 60 },
    'get_lable_statuses': {'max_token': 200 , 'rate_pm': 60 },
    'update_personnel_scen_state': {'max_token': 200 , 'rate_pm': 60 },
    'delete_personnel_scen_state': {'max_token': 200 , 'rate_pm': 60 },
    'update_default_scen_state': {'max_token': 200 , 'rate_pm': 60 },
    'get_default_scen_state': {'max_token': 200 , 'rate_pm': 60 },
    'update_output_card_state': {'max_token': 200 , 'rate_pm': 60 },
    'get_download_token': {'max_token': 200 , 'rate_pm': 60 },
    'user_sign_up_request': {'max_token': 5, 'rate_pm': 0.0035},
    'get_users_request': {'max_token': 200, 'rate_pm':60},
    'admin_authenticated': {'max_token': 200, 'rate_pm':60},
    'approve_request': {'max_token': 200, 'rate_pm':60},
    'delete-user-request': {'max_token': 200, 'rate_pm':60},
    'reject_user_request': {'max_token': 200, 'rate_pm':60}
}

OPEN_ROUTES = {
    'user_sign_up': {'max_token': 60 , 'rate_pm': 60 },
    'user_login': {'max_token': 2 , 'rate_pm': 1 },
    'validate_csv': {'max_token': 200 , 'rate_pm': 60 },
    'user_reset_password': {'max_token': 5, 'rate_pm': 0.0035}
}

