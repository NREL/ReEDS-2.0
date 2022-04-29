# standard libraries
import logging
import logging.config
import json
import os
import asyncio
import threading
from http import HTTPStatus
import requests
from concurrent.futures import *


# Third-party libraries
from aiohttp_swagger3 import *
from aiohttp import web
import aiohttp_cors
import asyncio
import yaml
import schedule
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))


with open(os.path.join(os.path.dirname(__file__), 'logging.yaml'), 'r') as stream:
    config = yaml.safe_load(stream)
logging.config.dictConfig(config)


# Internal modules
from web.handler import Handler

logger = logging.getLogger(__name__)

def get_json_schema(host, port):

    base_path = os.path.join(os.path.dirname(__file__), 'model\\reeds.V1.json' )
    base_url = f"http://{host}:{port}" + '/docs/swagger.json'

    isvalid = False
    while not isvalid:
        response = requests.get(base_url)
        isvalid = response.status_code = HTTPStatus.OK
    
    with open(base_path,'w') as outfile:
        json.dump(response.json(), outfile, indent=4, sort_keys=True)
    
    logger.info(f"Exported {base_path} file successfully")


class REEDS:

    def __init__(self, host= '0.0.0.0', port= 5001, logging_yaml_file=None):

        # Check env variables
        
        self.host = host
        self.port = port
        self.loop = asyncio.get_event_loop() 
        self.pool = ThreadPoolExecutor(max_workers=10)

        self.handler = Handler(loop= self.loop, pool = self.pool)
        logger.info('Handler initialized successfully')

        self.app = web.Application()
        logger.info('Initialized PRECISE API successfully')

        self.swagger = SwaggerDocs(
            self.app,
            swagger_ui_settings= SwaggerUiSettings(path="/docs/"),
            title='REEDS',
            version = '1.0-alpha',
            description='This API enables REEDS UI',
        )

        #self.swagger.register_media_type_handler()
        self.add_routes()

        self.loop.run_in_executor(self.pool, get_json_schema, 'localhost', port)
        # self.t = threading.Thread(name='api_thread', target= get_json_schema, args=(host,port,))
        # self.t.start()

        self.run_app()

    
    async def get_app(self):
        return self.app
    
    def run_app(self):
        
        self.configure_cors_on_all_routes()

        self.app = self.loop.run_until_complete(self.get_app())

        self.app.on_cleanup.append(self.cleanup_background_tasks)

        try:
            web.run_app(self.app, host=self.host, port=self.port)
        except Exception as err:
            logging.error(f"Error starting webserver - {str(err)}")

    
    def add_routes(self):
        
        #self.swagger.register_media_type_handler("multipart/form-data", self.handler.post_precise)
        # web.post('/return_folder_paths', self.handler.return_folder_paths),
        self.swagger.add_routes([
            web.get('/api/health', self.handler.handle_health),
            web.post('/api/run_model', self.handler.run_reeds_model),
            web.get('/api/get_scenarios', self.handler.get_scenarios),
            web.post('/api/update_scenarios', self.handler.update_scenarios),
            web.post('/api/clone_scenarios', self.handler.clone_scenarios),
            web.post('/api/delete_scenarios', self.handler.delete_scenarios),
            web.get('/api/get_output_metadata', self.handler.get_ouput_metadata),
            web.post('/api/delete_output_metadata', self.handler.delete_output_metadata),
            web.get('/api/download_file/{token}', self.handler.get_file_to_download),
            web.get('/api/get_scenario_data/{name}', self.handler.get_scenario_data),
            web.get('/api/get_scenario_list', self.handler.get_list_of_scenarios),
            web.get('/api/get_reeds_report/{token}', self.handler.get_reeds_report ),
            web.post('/api/user-sign-up', self.handler.handle_signup),
            web.post('/api/user-login', self.handler.handle_sigin),
            web.get('/api/authenticated', self.handler.check_authentication),
            web.post('/api/update_password', self.handler.update_password),
            web.get('/api/profile/{token}', self.handler.get_profile_image),
            web.get('/api/profile_data', self.handler.get_profile_data),
            web.post('/api/update_profile_data', self.handler.update_profile_data),
            web.post('/api/report_bug', self.handler.handle_bug_report),
            web.get('/api/list_bugs', self.handler.get_bugs),
            web.post('/api/upload_label', self.handler.upload_user_label),
            web.get('/api/get_labels', self.handler.get_user_labels),
            web.post('/api/delete_label', self.handler.delete_label_for_user),
            web.post('/api/add_card_label', self.handler.handle_add_card_label),
            web.get('/api/get_scenario_labels_list', self.handler.get_scenario_labels_list),
            web.post('/api/remove_card_label', self.handler.handle_remove_card_label),
            web.post('/api/update_label_status', self.handler.update_label_status),
            web.get('/api/get_lable_statuses', self.handler.get_lable_statuses),
            web.post('/api/update_personnel_scen_state', self.handler.update_personnel_scen_state),
            web.get('/api/get_personnel_scen_state', self.handler.get_personnel_scen_state),
            web.post('/api/delete_personnel_scen_state', self.handler.delete_personnel_scenario_state),
            web.post('/api/update_default_scen_state', self.handler.update_default_scen_state),
            web.get('/api/get_default_scen_state', self.handler.get_default_scen_state),
            web.post('/api/update_output_card_state', self.handler.update_output_card_state),
            web.get('/api/get_output_card_state', self.handler.get_output_card_state),
            web.get('/api/get_technologies', self.handler.handle_get_technologies),
            web.get('/api/get_scenario_file_infos/{scenario}', self.handler.handle_get_scenario_file_infos),
            web.post('/api/get_download_token', self.handler.get_download_token),
            web.post('/api/validate_csv', self.handler.handle_csv_validation),
            web.post('/api/user/reset_password', self.handler.get_reset_token),
            web.post('/api/update_password_after_reset/{token}', self.handler.handle_password_reset),
            web.post('/api/user-sign-up-request',  self.handler.handle_user_signup_request),
            web.get('/api/get-users-request', self.handler.return_users_requests),
            web.get('/api/admin_authenticated', self.handler.handle_admin_check),
            web.post('/api/approve-request', self.handler.handle_user_request_approval),
            web.post('/api/delete-user-request', self.handler.delete_user_signup_request),
            web.post('/api/reject-user-request', self.handler.handle_user_request_rejection),
            web.get('/api/get-error-log-file/{token}', self.handler.get_error_log_file),
            web.get('/api/user-signup-token-validate/{token}', self.handler.validate_user_signup_token),
            web.get('/api/user-password-reset-token-validate/{token}', self.handler.validate_user_password_reset_token),
            web.post('/api/update-bug-status', self.handler.update_bug_status),
            web.post('/api/delete_bug', self.handler.handle_delete_bug),
        ])
    
    def configure_cors_on_all_routes(self):
        
        """ Configure CORS on all routes. """
        cors = aiohttp_cors.setup(self.app, defaults={
            # Allow all to read all CORS-enabled resources from *
            "*": aiohttp_cors.ResourceOptions(
                expose_headers="*",
                allow_headers="*",
                allow_methods="*"
            )
        })
        for route in list(self.app.router.routes()):
            cors.add(route)

        logger.info('Added cors on all routes')

    async def cleanup_background_tasks(self, *args, **kwargs):

        logger.info('Cleaning up background tasks')
        #self.t.join()
        self.handler.shutdown_event.set()
        self.handler.stop_scheduler_run.set()

if __name__ == '__main__':

    REEDS()