# standard libraries
from lib2to3.pgen2 import token
import os
import json
import logging
import logging.config
from concurrent.futures import *
from uuid import uuid4
from multiprocessing import Event, Queue, Process, context
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import threading
import datetime
import math
import uuid
import sys
from aiohttp.web_request import Request
import psutil
import shutil
import jwt
import subprocess
from cerberus import Validator
import zipfile
from zipfile import ZipFile, PyZipFile 
import time
import sqlalchemy
import yaml
from sqlalchemy import create_engine
from web.create_db import Base
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
import schedule
import traceback

# Internal libraries
from aiohttp import web
from web.rate_limiter import rule_retriever, run_continuously, check_for_throttle
import aiohttp
from web.mapper import FILE_KEYS, FILE_LOCATION, SCEN_DESCRIPTION, DEFAULT_FILE_NAMES, DEFAULT_FILE_TO_CATEGORY, get_file_location, CSV_SCHEMA, CSV_FILE_HEADERS
from web.mail import (TestMail, AWS_SES_HTMLMail, UserPasswordResetHTMLMessage,
    UserSignUpInstructionsHTMLMessage, UserSignUpRejectionHTMLMessage,
    UserSignUpRequestNotificationHTMLMessage, UserWelcomeHTMLMessage, UserSimRunInitiationHTMLMessage,
    UserSimInQueueHTMLMessage, UserSimRunCompleteHTMLMessage, UserChangePasswordHTMLMessage)
from web.constants import (USER_RESET_EMAIL_SUBJECT, USER_SIGNUP_EMAIL_SUBJECT, 
    USER_SIGNUP_EMAIL_REJECT_SUBJECT, USER_SIGNUP_REQUEST_SUBJECT, USER_WELCOME_EMAIL_SUBJECT,
    REEDS_SIM_INITIATION_SUBJECT, REL_URL_TO_SERVICE_DICT, REEDS_SIM_INQUEUE_SUBJECT, REEDS_SIM_COMPLETE_SUBJECT,
    REEDS_PASSWORD_CHANGE_SUBJECT)
from web.notifier import notify

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from core.crypto import Hash
from core.dbhandler import DatabaseHandler
from runmodel import main
import pandas as pd

NUM_OF_PROCESS = os.getenv('NUM_OF_PROCESS')

# Third party libraries
logger = logging.getLogger(__name__)

JWT_KEY = os.getenv('JWT_KEY')
assert JWT_KEY != None

DB_CONN_STRING = os.getenv('DB_CONN_STRING')
assert DB_CONN_STRING != None
engine = create_engine(DB_CONN_STRING)
Base.metadata.bind = engine 
DB_SESSION = sessionmaker(bind=engine)

schedule.every(30).minutes.do(rule_retriever, sqlalchemy_session = DB_SESSION)
data_lock = threading.Lock()
db = DatabaseHandler()


# Let's create context manager for session
@contextmanager
def session_manager():
    """ Provides a transactional scopes around a series of operations """
    session = DB_SESSION()
    try:
        yield session
    except:
        session.rollback()
        raise
    finally:
        session.close()


def get_file_category(key, val):

    if val:
        if key in DEFAULT_FILE_TO_CATEGORY:
            if val in DEFAULT_FILE_TO_CATEGORY[key]:
                return DEFAULT_FILE_TO_CATEGORY[key][val]
            else:
                return 'Custom Upload'
        else:
            return 'Custom Upload'

    else:
        return 'Default'


# Decorator for measuring time it took to run the code 
def monitor_time(func):
    async def inner_wrapper(self, request):
        start_time = time.time()
        ret_val = await func(self, request)
        end_time = time.time()
        logger.info(f"Time spent processing request at url {request.url} is {round(end_time-start_time,3)} seconds")
        return ret_val
    return inner_wrapper

# Decorator for rate limiting the request
def rate_limit(func):
    async def inner_wrapper(self, request):

        is_admin = False

        if 'userData' in request:
            with session_manager() as session:
                is_admin = db.is_admin(session, request['userData']['username'])
                    
        throttle = check_for_throttle(request) if not is_admin else False
        if not throttle:
            logger.info(f"Request accepted for service {request.rel_url} for user {request['userData']['username'] if 'userData' in request else request.remote}")
            ret_val = await func(self, request)
            return ret_val
        else:
            logger.error(f"Request denied for service {request.rel_url} for user {request['userData']['username'] if 'userData' in request else request.remote}")
            return web.Response(text=json.dumps({
                    'message': 'Request denied! Please wait before sending more request!'
                }),status=429)
    return inner_wrapper

# Decorator for rate limiting the request
def authenticate(func):
    async def inner_wrapper(self, request):
        
        try:
            token = request.headers['Authorization'].split(" ")[1].encode('utf-8')
            decoded = jwt.decode(token, JWT_KEY, algorithms=['HS256'])
            request['userData'] = decoded
            ret_val = await func(self, request)
            return ret_val
        except Exception as e:
            logger.error(f"Unauthorized request to service {request.rel_url}, {str(e)}")
            return web.Response(text=json.dumps(f"Unauthorized"), status=401)
    return inner_wrapper

def run_simulation_using_queue(queue, db, instances_dict, thread_event):

    while True:

        # Remove this in the future
        time.sleep(3)

        if not queue.empty():
            sim_data = queue.get()
            
            # Generate a process
            p = Process(target=main, name=sim_data['uuid'], args=(sim_data['input'], notify, sim_data['uuid']))

            with data_lock:
                if sim_data['username'] not in instances_dict:
                    instances_dict[sim_data['username']] = {}

                instances_dict[sim_data['username']][sim_data['uuid']] = {
                    "process": p,
                    "name": sim_data['input']['run_name']
                }

            with session_manager() as session:
                db.update_output_metadata_status(session, 'RUNNING', sim_data['input']['run_name'], sim_data['username'])
                session.commit()
            
            # Start a process
            p.start()

            email_body = UserSimRunInitiationHTMLMessage().return_rendered_html({
                'uuid': sim_data['uuid'],
                'name': sim_data['input']['run_name'],
                'description':  sim_data['description'],
                'link_to_logs': f"{os.getenv('BASE_URL_FOR_SIMULATION_STATUS')}/{sim_data['uuid']}"
            })

            mail = AWS_SES_HTMLMail(os.getenv('AWS_REGION'), ec2_instance=True)
            #mail.send_email(os.getenv('REEDS_SENDER'), sim_data['usr_email'], email_body, REEDS_SIM_INITIATION_SUBJECT + f" : {sim_data['input']['run_name']}")

            # Join the process
            p.join()

            email_body = UserSimRunCompleteHTMLMessage().return_rendered_html({
                'uuid': sim_data['uuid'],
                'name': sim_data['input']['run_name'],
                'description':  sim_data['description']
            })

            mail = AWS_SES_HTMLMail(os.getenv('AWS_REGION'), ec2_instance=True)
            #mail.send_email(os.getenv('REEDS_SENDER'), sim_data['usr_email'], email_body, REEDS_SIM_COMPLETE_SUBJECT + f" : {sim_data['input']['run_name']}")

            with session_manager() as session:
                db.delete_simulation_queue(session, sim_data['username'], sim_data['uuid'])
                session.commit()


        if thread_event.is_set():
            break

class Handler:

    def __init__(self, loop = None, pool=None):

        logger.info('Initializing handler for precise time series analysis API')

        self.stop_scheduler_run = run_continuously()
        schedule.run_all()
        self.instances_dict = dict()
        self.shutdown_event = Event()
        self.loop = loop
        self.pool = pool

        self.db = DatabaseHandler()
        self.hash = Hash(self.db)

        self.simulation_queue = Queue()

        with session_manager() as session:
            prev_sim_list = self.db.get_sim_queue(session)

        for sim in prev_sim_list:
            self.simulation_queue.put(
                {
                    'input': json.loads(sim.input.decode()),
                    'uuid': sim.uuid,
                    'username': sim.username
                }
            )
        

        sim_thread = threading.Thread(name='sim_running_thread', target=run_simulation_using_queue,
            args=(self.simulation_queue, self.db, self.instances_dict, self.shutdown_event))
        
        sim_thread.start()

        self.mail = AWS_SES_HTMLMail(os.getenv('AWS_REGION'), ec2_instance=True)

    def jwt_authenticate(self, request):
        try:
            token = request.headers['Authorization'].split(" ")[1].encode('utf-8')
            decoded = jwt.decode(token, JWT_KEY, algorithms=['HS256'])
            request['userData'] = decoded
            return (request, True)
        except Exception as e:
            return (request, False)

    @monitor_time
    async def get_bugs(self, request):

        # TODO: Authenticate this service
        with session_manager() as session:
            return web.Response(text=json.dumps(self.db.get_bugs(session)),status=200)

    @monitor_time
    async def delete_label_for_user(self, request):

        
        request, authenticated = self.jwt_authenticate(request)
        if authenticated:
            label_data = await request.json()
            
            with session_manager() as session:
                self.db.delete_label(session, request['userData']['username'] ,label_data['label'])
                session.commit()
            
            # Safe to create new session after expiring previous session
            with session_manager() as session:
                return web.Response(text=json.dumps(self.db.get_all_user_labels(session, request['userData']['username'])),status=200)

        else:
            return web.Response(text=json.dumps({
                    'message': 'Unauthorized'
                }),status=401)

    async def handle_health(self, request):

        return web.Response(text=json.dumps({
                    'message': 'UP and running!'
                }),status=200)

    
    @monitor_time
    @authenticate
    @rate_limit
    async def handle_get_scenario_file_infos(self, request):
            
        try:
            scenario_name = request.match_info['scenario']
            case_csv = os.path.join(os.path.dirname(__file__), '..', 'users_cases', request['userData']['username'], 'cases.csv')
            case_df = pd.read_csv(case_csv)
            case_dict = dict(zip(case_df['case'], case_df[scenario_name]))

            for key, val in case_dict.items():
                if pd.isna(val):
                    case_dict[key] = ''

            custom_input  = {
                                'TechCost_file': get_file_category('TechCost_file', case_dict['TechCost_file']),
                                'FuelLimit_file': get_file_category('FuelLimit_file', case_dict['FuelLimit_file']),
                                'MinLoad_file': get_file_category('MinLoad_file', case_dict['MinLoad_file'])
                            }
            
            ivt_base_dir = ivt_file = os.path.join(os.path.dirname(__file__), '..', '..', 'A_Inputs',  'inputs', 'generators')
            ivt_file = os.path.join(ivt_base_dir, case_dict['IVT_file']) if case_dict['IVT_file'].endswith('.csv') else os.path.join(ivt_base_dir, 'ivt.csv')
            ivt_df = pd.read_csv(ivt_file)
            onTechnologies = ivt_df['Unnamed: 0'].tolist()

            return web.Response(text=json.dumps({
                'custom_input_data': custom_input,
                'ontechnologies': onTechnologies
            }),status=200)

        except Exception as e:
            return web.Response(text=json.dumps(f"Error occured > {str(e)}"), status=500)


    @monitor_time
    @authenticate
    @rate_limit
    async def handle_remove_card_label(self, request):
        
        label_data = await request.json()
        
        if label_data['type'] == 'scenario':
            
            with session_manager() as session:
                self.db.delete_scenario_card_label(session, request['userData']['username'] , label_data['scen_name'] ,label_data['label'])
                session.commit()
            
            return web.Response(text=json.dumps({"message": "success"}),status=200)


    @monitor_time
    @authenticate
    @rate_limit
    async def get_scenario_labels_list(self, request):
        
        with session_manager() as session:
            return web.Response(text=json.dumps(self.db.get_scenario_tag_list(session,
                request['userData']['username'])),status=200)

    
    @monitor_time
    @authenticate
    @rate_limit
    async def upload_user_label(self, request):
    
        label_data = await request.json()
        
        with session_manager() as session:
            output, message = self.db.insert_label(
                session,
                request['userData']['username'],
                datetime.datetime.now(),
                label_data['name'],
                label_data['description']
            )
            session.commit()

        if output:
            
            with session_manager() as session:
                labels = self.db.get_all_user_labels(session, request['userData']['username'])
                return web.Response(text=json.dumps(labels),status=200)

        else:
            return web.Response(text=json.dumps({
                'message': message
            }),status=500)

        
    @monitor_time
    @authenticate
    @rate_limit
    async def get_user_labels(self, request): 
        
        with session_manager() as session:
            labels = self.db.get_all_user_labels(session, request['userData']['username'])
            return web.Response(text=json.dumps(labels),status=200)
    

    @monitor_time
    @authenticate
    @rate_limit
    async def handle_bug_report(self, request):

        try:
            # Trying to read multipart/form-data using the aiohttp post coroutine
            user_detail = await request.post()

            # Just a container to store the parsed data
            parsed_data = {}

            for key, value in user_detail.items():

                # check if the type is aiohttp.web_request.FileField
                if isinstance(value, aiohttp.web_request.FileField):

                    # get the filename and read file_content
                    filename = value.filename

                    # The read function gives binary encoded content which will decode using utf-8 and will write into a proper destination
                    filecontent = value.file.read()
                    # filecontent = filecontent.decode()

                    parsed_data[key] = {
                        'content': filecontent,
                        'filename': str(uuid4()) + '.' + filename.split('.')[-1]
                    }

                elif isinstance(value, str):

                    # we are going to assume all str can be jsonified
                    try:
                        parsed_data[key] = json.loads(value)
                    except Exception as e:
                        parsed_data[key] = value


            if 'attachement' in parsed_data:

                
                base_path = os.path.join(os.path.dirname(__file__), '..', 'bug_attachements')

                with open(os.path.join(base_path, f"{parsed_data['attachement']['filename']}"), "wb") as f:
                    f.write(parsed_data['attachement']['content'])

                attachement = parsed_data.pop('attachement')
                parsed_data['formdata']['image_name'] = attachement['filename']

            
            # Now create a github issue
            # subprocess.run(["gh", "issue", "create", "--title", parsed_data['formdata']['title'],
            # "--body", parsed_data['formdata']['body']], cwd="C:/Users/KDUWADI/Desktop/NREL_Projects/ReEDs/REEDS-2.0_UI", shell=True)

            # Insert bug into the database
            with session_manager() as session:
                
                if self.db.insert_bug(session, str(uuid.uuid4()),
                                        datetime.datetime.now(),
                                        parsed_data['formdata']['title'], 
                                        parsed_data['formdata']['body'], 
                                        'PENDING'):
                    
                    session.commit()

                    return web.Response(text=json.dumps({
                            'message': f'Success'
                        }),status=200)

                else:
                    return web.Response(text=json.dumps({
                            'message': f'Failed uploading bug'
                        }),status=500)

        except Exception as e:
            print(e)
            return web.Response(text=json.dumps({
                    'message': f'Failed to report a bug {e}'
                }),status=500)


    @monitor_time
    @authenticate
    @rate_limit
    async def update_profile_data(self, request):
        
        try:

            # Trying to read multipart/form-data using the aiohttp post coroutine
            user_detail = await request.post()

            # Just a container to store the parsed data
            parsed_data = {}

            for key, value in user_detail.items():

                # check if the type is aiohttp.web_request.FileField
                if isinstance(value, aiohttp.web_request.FileField):

                    # get the filename and read file_content
                    filename = value.filename

                    # The read function gives binary encoded content which will decode using utf-8 and will write into a proper destination
                    filecontent = value.file.read()
                    # filecontent = filecontent.decode()

                    parsed_data[key] = {
                        'content': filecontent,
                        'fileext': filename.split('.')[-1]}

                elif isinstance(value, str):

                    # we are going to assume all str can be jsonified
                    try:
                        parsed_data[key] = json.loads(value)
                    except Exception as e:
                        parsed_data[key] = value


            if 'avatar' in parsed_data:

                # Remove older profile image
                with session_manager() as session:
                    old_image_name = self.db.get_image_name(session, parsed_data['formdata']['username'])
                
                base_path = os.path.join(os.path.dirname(__file__), '..', 'users_avatar')
                os.remove(os.path.join(base_path, old_image_name))

                with open(os.path.join(base_path, f"{parsed_data['formdata']['username']}.{parsed_data['avatar']['fileext']}"), "wb") as f:
                    f.write(parsed_data['avatar']['content'])

                avatar = parsed_data.pop('avatar')
                parsed_data['formdata']['image_name'] = f"{parsed_data['formdata']['username']}.{avatar['fileext']}"
            
            #parsed_data['formdata']['password'], salt = self.hash.hash_string(parsed_data['formdata']['password'])
            with session_manager() as session:
                for key, value in parsed_data['formdata'].items():
                    if key not in ['username', 'password']:
                        if key =='org': 
                            key= 'organization'
                        self.db.update_user_info_by_username(session, parsed_data['formdata']['username'], key, value)
                session.commit()

            message = 'success'
            code = 200
            return web.Response(text=json.dumps({
                    'message':  message,
                }),status=code)

        
        except Exception as e:
            # import traceback
            # print(traceback.print_exc())
            return web.Response(text=json.dumps({
                    'message': 'Signing up failed'
                }),status=500)

    @monitor_time
    @authenticate
    @rate_limit
    async def get_profile_data(self, request):
        
        try:
            with session_manager() as session:
                user_detail = self.db.get_user_data(session, request['userData']['username'])
            if user_detail:
                return web.json_response(text=json.dumps(user_detail), status=200) 
            else:
                return web.json_response(text=json.dumps({"message": "Unsuccessful!"}), status=500) 
        except Exception as e:
            return web.json_response(text=json.dumps({"message": "Unsuccessful!"}), status=500) 
    

    @monitor_time
    async def get_profile_image(self, request):
        
        token = request.match_info['token']
        image_path = os.path.join(os.path.dirname(__file__), '..', 'users_avatar', 'default.png')
        try:
            decoded = jwt.decode(token, JWT_KEY, algorithms=['HS256'])
            with session_manager() as session:
                image_name = self.db.get_image_name(session, decoded['username'])
            if image_name:
                image_path = os.path.join(os.path.dirname(__file__), '..', 'users_avatar', image_name)
        except Exception as e:
            pass
        return web.FileResponse(
                image_path
                    )

    @monitor_time
    @authenticate
    @rate_limit
    async def update_password(self, request):
            
        try:
        
            user_detail = await request.json()
            
            with session_manager() as session:
                if self.hash.check_password(session, request['userData']['username'], user_detail['oldpassword']):

                    hash_key, salt = self.hash.hash_string(user_detail['password'])
                    self.db.update_password(session, hash_key, request['userData']['username'])
                    usr_email = self.db.get_email_from_username(session, request['userData']['username'])
                    session.commit()

                    
                    email_body = UserChangePasswordHTMLMessage().return_rendered_html({})
                    self.mail.send_email(os.getenv('REEDS_SENDER'), usr_email, email_body,  REEDS_PASSWORD_CHANGE_SUBJECT)
                
                    return web.json_response(text=json.dumps({'message': 'success'}), status=200)
                else:
                    return web.json_response(text=json.dumps({"message": "Unauthorized!"}), status=401) 
        except Exception as e:
            print(traceback.print_exc())

    # Check for JWT authentication
    @monitor_time
    @authenticate
    @rate_limit
    async def check_authentication(self, request):
        return web.json_response(text=json.dumps(request['userData']), status=200)
    
    # Handle user login
    @monitor_time
    @rate_limit
    async def handle_sigin(self, request):

        user_detail = await request.json()

        with session_manager() as session:
            message, jwt_token, code = self.hash.login(session, user_detail)

        return web.Response(
            text= json.dumps({
                'message': message,
                'token': jwt_token
            }), status=code
        )

    # Handles user sign up
    @monitor_time
    @rate_limit
    async def handle_signup(self, request):
        
        #TODO deal with large image size
        
        try:
            # Trying to read multipart/form-data using the aiohttp post coroutine
            user_detail = await request.post()
            
            # Just a container to store the parsed data
            parsed_data = {}

            for key, value in user_detail.items():

                # check if the type is aiohttp.web_request.FileField
                if isinstance(value, aiohttp.web_request.FileField):

                    # get the filename and read file_content
                    filename = value.filename

                    # The read function gives binary encoded content which will decode using utf-8 and will write into a proper destination
                    filecontent = value.file.read()
                    # filecontent = filecontent.decode()

                    parsed_data[key] = {
                        'content': filecontent,
                        'fileext': filename.split('.')[-1]}

                elif isinstance(value, str):

                    # we are going to assume all str can be jsonified
                    try:
                        parsed_data[key] = json.loads(value)
                    except Exception as e:
                        parsed_data[key] = value

            with session_manager() as session:
                token_is_valid = self.db.is_signup_token_valid(session, parsed_data['formdata']['stoken'])

            stoken = parsed_data['formdata'].pop('stoken')

            if token_is_valid:
                
                if 'avatar' in parsed_data:

                    base_path = os.path.join(os.path.dirname(__file__), '..', 'users_avatar')
                    with open(os.path.join(base_path, f"{parsed_data['formdata']['username']}.{parsed_data['avatar']['fileext']}"), "wb") as f:
                        f.write(parsed_data['avatar']['content'])

                    avatar = parsed_data.pop('avatar')
                    parsed_data['formdata']['image_name'] = f"{parsed_data['formdata']['username']}.{avatar['fileext']}"

                else:
                    parsed_data['formdata']['image_name'] = 'default.png'
                
                with session_manager() as session:
                    message, code = self.hash.signup(session, parsed_data['formdata'])
                    self.db.invalidate_signup_token(session, stoken)
                    self.db.add_default_limits(session, parsed_data['formdata']['username'] )
                    session.commit()
                message = 'success'
                code = 200


                # create a folder for user if already does not exist
                case_base_path = os.path.join(os.path.dirname(__file__), '..', 'users_cases', parsed_data['formdata']['username'])

                if not os.path.exists(case_base_path):
                    os.mkdir(case_base_path)

                # Copy the base case.csv file if one already does not exist
                case_file_path = os.path.join(case_base_path, 'cases.csv')
                if not os.path.exists(case_file_path):
                    default_case_csv_path = os.path.join(os.path.dirname(__file__), '..', '..', 'A_Inputs', 'cases.csv')
                    shutil.copy( default_case_csv_path, case_file_path)

                # create a output folder for user if already does not exist
                output_base_path = os.path.join(os.path.dirname(__file__), '..', 'users_output', parsed_data['formdata']['username'])

                if not os.path.exists(output_base_path):
                    os.mkdir(output_base_path)

                # send email template
                email_body = UserWelcomeHTMLMessage().return_rendered_html({})
                # print(email_body)

                # TODO: Activate this email during the testing
                self.mail.send_email(os.getenv('REEDS_SENDER'), parsed_data['formdata']['email'], email_body, USER_WELCOME_EMAIL_SUBJECT)

                return web.Response(text=json.dumps({
                        'message':  message,
                    }),status=code)
            else:
                return web.Response(text=json.dumps({"message":f"Unauthorized"}), status=401)
        except Exception as e:
            print(e)
            return web.Response(text=json.dumps({
                    'message': 'Signing up failed'
                }),status=500)
    
    @monitor_time
    @authenticate
    @rate_limit
    async def get_download_token(self, request):
            
        # Encode file_type, category, username and scen_name in the token and make it short lived
        # may be for 120 seconds
        data = await request.json()
        data['user'] = request['userData']['username']

        # Generate token
        token = self.hash.generate_token(data, 120)
        return web.Response(text=json.dumps({"token": token}), status=200)
    
    
    @monitor_time
    @rate_limit
    async def handle_csv_validation(self, request):

        try:
            # Using cerberus to validate the content of csv file
        
            # Trying to read multipart/form-data using the aiohttp post coroutine
            csv_detail = await request.post()

            # Just a container to store the parsed data
            parsed_data = {}

            for key, value in csv_detail.items():

                # check if the type is aiohttp.web_request.FileField
                if isinstance(value, aiohttp.web_request.FileField):

                    # get the filename and read file_content
                    filename = value.filename

                    # The read function gives binary encoded content which will decode using utf-8 and will write into a proper destination
                    filecontent = value.file.read()
                    # filecontent = filecontent.decode()

                    parsed_data[key] = {
                        'content': filecontent,
                        'filename': str(uuid4()) + '.' + filename.split('.')[-1]
                    }

            # Let's validate all the csvs
            errors = {}
            for key, subdict in parsed_data.items():
                
                print(key, subdict['filename'])
                if subdict['filename'].endswith('.csv'):
                    errors[key] = []
                 
                    with open(subdict['filename'], "wb") as f:
                        f.write(subdict['content'])

                    if key in CSV_FILE_HEADERS:
                        df = pd.read_csv(subdict['filename'], names=CSV_FILE_HEADERS[key])
                    else:
                        df = pd.read_csv(subdict['filename'])
                    csv_validator = Validator()
                    csv_validator.schema = CSV_SCHEMA[key]
                    csv_validator.require_all= True

                    df_dict = df.to_dict(orient='records')
                    for idx, record in enumerate(df_dict):
                        if not csv_validator.validate(record):
                            errors[key].append(f"Item {idx}: {csv_validator.errors}")
                    
                    if not errors[key]:
                        errors.pop(key)
                    os.remove(subdict['filename'])
                    print(errors)
            if not errors:
                errors = ''
            
            return web.Response(text=json.dumps({"errors": errors}), status=200)
        except Exception as e:

            return web.Response(text=json.dumps(f"Error occured > {str(e)}"), status=500)


    @monitor_time   
    async def get_file_to_download(self, request):

        try: 
            token = request.match_info['token']
            
            decoded = jwt.decode(token, JWT_KEY, algorithms=['HS256'])
            file_type, file_category, scen_name, user = decoded['file_type'], decoded['category'], decoded['scen_name'], decoded['user']
            file_name = get_file_location(file_type, file_category)
           
            if file_name is None:
                
                # This is custom upload so we need read users case.csv to find out 
                # which file this one belongs to 
                case_csv_file = os.path.join(os.path.dirname(__file__), '..', 'users_cases', user, 'cases.csv')
                case_df = pd.read_csv(case_csv_file)

                if scen_name in list(case_df.columns):
                    case_dict = dict(zip(case_df['case'], case_df[scen_name]))
                    file_name = case_dict[file_type]

                else:
                    print(f"No file exists for file type {file_type}, category {file_category}, scenario {scen_name} for user {request['userData']['username']}")
                    file_name = get_file_location(file_type, 'Default')

            file = os.path.join(os.path.dirname(__file__), '..', '..', 'A_Inputs', 'inputs', FILE_LOCATION[file_type], file_name)
            f = open(file, "rb")
            content = f.read()
            f.close()
            
            return web.Response(
                        body=content,
                        headers= {'Content-Type': 'application/octet-stream',
                            'Content-Disposition' : f"attachement; filename={file_name}"},
                        status=200
                    )


        except Exception as e:
            return web.Response(text=json.dumps(f"Error occured > {str(e)}"), status=500)
    
        
    # async def return_folder_paths(self, request):

    #     try:
    #         folder_data = await request.json()
    #         print(folder_data)
    #         if folder_data['folder_path'] == []:
    #             base_folder = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')
    #         else:
    #             if folder_data['folder']=='':
    #                 base_folder = "\\".join(folder_data['folder_path'])
    #             else:
    #                 base_folder = os.path.join("\\".join(folder_data['folder_path']),folder_data['folder'])
            
    #         base_folder = os.path.abspath(base_folder) if '..' in base_folder else base_folder
    #         folder_path = base_folder.split("\\")
    #         folders = os.listdir(base_folder)

    #         folders = [folder for folder in folders if os.path.isdir(os.path.join(base_folder, folder))]

    #         return web.Response(text=json.dumps({'folder_path': folder_path, 'folders': folders}),status=200)
    #     except Exception as e:
    #         return web.Response(text=json.dumps(f"Error occured > {str(e)}"), status=500)
    
    
    @monitor_time
    async def get_error_log_file(self, request):
        
        try:
            token = request.match_info['token']
            decoded = jwt.decode(token, JWT_KEY, algorithms=['HS256'])
            
            runname, username = decoded['run_name'], decoded['user']
            output_file_path = os.path.join(os.path.dirname(__file__), '..', 'users_output', username, runname, 'full_log.txt')


            if os.path.exists(output_file_path):

                with open(output_file_path, 'rb') as infile:
                    content = infile.read()
                
                return web.Response(
                            body=content,
                            headers= {'Content-Type': 'application/octet-stream',
                                'Content-Disposition' : f"attachement; filename=log.txt"},
                            status=200
                        )
            else:
                return web.Response(text=json.dumps(f"No log file found for the sim!"), status=500)
        except Exception as e:
            return web.Response(text=json.dumps(f"Error occured > {str(e)}"), status=500)

    
    
    @monitor_time
    async def get_reeds_report(self, request):

        def zipdir(path, ziph, include_only=None):
            # ziph is zipfile handle
            for root, dirs, files in os.walk(path):
                for file in files:
                    if not file.endswith('.zip'):
                        if include_only != None:
                            if include_only in file:
                                ziph.write(os.path.join(root, file), 
                                    os.path.relpath(os.path.join(root, file), 
                                                    os.path.join(path, '..')))
                        else:
                            ziph.write(os.path.join(root, file), 
                                    os.path.relpath(os.path.join(root, file), 
                                                    os.path.join(path, '..')))
        
        try:
            token = request.match_info['token']
            decoded = jwt.decode(token, JWT_KEY, algorithms=['HS256'])
            
            runname, username = decoded['run_name'], decoded['user']
            output_folder_path = os.path.join(os.path.dirname(__file__), '..', 'users_output', username, runname)
            output_file = None

            if os.path.exists(os.path.join(output_folder_path, 'exceloutput')):

                # Zip the content if not already
                file_exists = False
                for file in os.listdir(os.path.join(output_folder_path, 'exceloutput')):
                    if file.endswith('.xlsx'):
                        file_exists = True

                if file_exists:
                    if not os.path.exists(os.path.join(output_folder_path, 'exceloutput.zip')):

                        zipf = zipfile.ZipFile(os.path.join(output_folder_path, 'exceloutput.zip'), 'w', zipfile.ZIP_DEFLATED)
                        zipdir(os.path.join(output_folder_path, 'exceloutput'), zipf)
                        zipf.close()
                    
                    output_file = 'exceloutput.zip'

            # Check if error exists
            if output_file is None:
                error_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'D_Augur', 'ErrorFile')
                
                if not os.path.exists(os.path.join(error_dir, runname + '.zip')):
                    
                    errorFileExists = False
                    for file in os.listdir(error_dir):
                        if runname in file:
                            errorFileExists = True

                    if errorFileExists:
                        zipf = zipfile.ZipFile(os.path.join(error_dir, runname+'.zip'), 'w', zipfile.ZIP_DEFLATED)
                        zipdir(error_dir, zipf, include_only=runname)
                        zipf.close()
                        output_file = runname + '.zip'
                        output_folder_path = error_dir

                else:
                    output_file = runname + '.zip'
                    output_folder_path = error_dir


            if output_file:

                with open(os.path.join(output_folder_path, output_file), 'rb') as infile:
                    content = infile.read()
                
                if runname not in output_file:
                    output_file = runname + output_file
                return web.Response(
                            body=content,
                            headers= {'Content-Type': 'application/octet-stream',
                                'Content-Disposition' : f"attachement; filename={output_file}"},
                            status=200
                        )
            else:
                return web.Response(text=json.dumps(f"Either simulation is not complete or simulation ran into an error!"), status=500)
        except Exception as e:
            return web.Response(text=json.dumps(f"Error occured > {str(e)}"), status=500)

    
    # I left here
    @monitor_time
    @authenticate
    @rate_limit
    async def get_list_of_scenarios(self, request):
       
        try: 
            with session_manager() as session:
                base_scenarios = self.db.get_base_scenarios(session)
                personnel_scenarios = self.db.get_scenarios_by_user(session, request['userData']['username'])
            all_scenarios = base_scenarios + personnel_scenarios

            scen_list = [{"name": d['name'], "description": d['description']} for d in all_scenarios]
            return web.Response(text=json.dumps(scen_list),status=200)

        except Exception as e:
            return web.Response(text=json.dumps(f"Error occured > {str(e)}"), status=500)
       

    @monitor_time
    @authenticate
    @rate_limit
    async def handle_add_card_label(self, request):

        label = await request.json()
        if label['type'] == 'scenario':
            if label['label']:

                with session_manager() as session:
                    success, message = self.db.insert_scenario_label(
                        session,
                        request['userData']['username'],
                        label['scen_name'], 
                        label['label'],
                        datetime.datetime.now()
                        )
                    if success:
                        session.commit()
                if success:
                    return web.Response(text=json.dumps(f"{success}"), status=200)
                else:
                    return web.Response(text=json.dumps(f"{message}"), status=500)
            else:
                return web.Response(text=json.dumps(f"Label can not be empty"), status=500) 
      

    @monitor_time
    @authenticate
    async def get_scenario_data(self, request):

        try: 
            scenario_name = request.match_info['name']
            scenario_data = {} #[]

            case_csv_file = os.path.join(os.path.dirname(__file__), '..', 'users_cases', request['userData']['username'], 'cases.csv')
            case_df = pd.read_csv(case_csv_file)

            case_dict = dict(zip(case_df['case'], case_df[scenario_name]))
            row_desc = dict(zip(case_df['case'], case_df['Description']))

    
            scenario_data['scen_name'] = scenario_name

            with session_manager() as session:
                base_scenarios = self.db.get_base_scenarios(session)
                base_scenarios = [el['name'] for el in base_scenarios]

                username = request['userData']['username']
                if scenario_name in base_scenarios:
                    username = "NREL (ReEDS India)"

                # Get the description for the scenario name
                scenario_data['description'] = self.db.get_scenario_description(session, username, scenario_name)

            for key, val in case_dict.items():
                if not pd.isna(val):
                    scenario_data[key] = val

            # Let's parse the yearset values
            model_year_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'A_Inputs', 'inputs', 'sets')
            model_year_file = os.path.join(model_year_dir, scenario_data['yearset']) if 'yearset' in scenario_data else os.path.join(model_year_dir,'modeledyears_set.csv')

            model_year_df = pd.read_csv(model_year_file)
            scenario_data['yearset'] = ','.join(list(model_year_df.columns))
            return web.Response(text=json.dumps(scenario_data),status=200)

        except Exception as e:
            return web.Response(text=json.dumps(f"Error occured > {str(e)}"), status=500)

       
    
    @monitor_time
    @authenticate
    @rate_limit
    async def run_reeds_model(self, request):

        # request, authenticated = self.jwt_authenticate(request)

        # if authenticated:
        try:
            reeds_input = await request.json()
            reeds_uuid = str(uuid4())
            reeds_input['run_name'] = request['userData']['username'] + "_" + reeds_input['run_name']
            metadata = {
                    "name": reeds_input['run_name'],
                    "author": request['userData']['username'],
                    "created": datetime.datetime.now(),
                    "status": f"INQUEUE",
                    "size": None,
                    "uuid": reeds_uuid,
                    "description": ' + '.join([el for el in reeds_input['scenarios']])
                }

            # Append case file path and output folder path
            reeds_input['case_csv'] = os.path.join(os.path.dirname(__file__), '..', 'users_cases', request['userData']['username'], 'cases.csv')
            reeds_input['output_folder_path'] = os.path.join(os.path.dirname(__file__), '..', 'users_output', request['userData']['username'], reeds_input['run_name'])

            if request['userData']['username'] not in self.instances_dict:
                self.instances_dict[request['userData']['username']] = {}
            

            # Write into the database
            with session_manager() as session:
                self.db.insert_output_metadata(session, metadata)
                self.db.insert_simulation_queue(session, reeds_input, reeds_uuid, request['userData']['username'])
                session.commit()
            
            with session_manager() as session:
                output_metadata = self.db.get_output_metadata(session, request['userData']['username'])
                usr_email = self.db.get_email_from_username(session, request['userData']['username'])

            # Add to the Queue
            self.simulation_queue.put({
                    'input': reeds_input, 
                    'uuid': reeds_uuid, 
                    'username': request['userData']['username'],
                    'usr_email': usr_email,
                    'description': metadata['description']
                })

            # Let's send email
            email_body = UserSimInQueueHTMLMessage().return_rendered_html({
                'uuid': reeds_uuid,
                'name': metadata['name'],
                'description':  metadata['description'],
            })
           
            #self.mail.send_email(os.getenv('REEDS_SENDER'), usr_email, email_body,  REEDS_SIM_INQUEUE_SUBJECT + f" : {metadata['name']}")
            
            return web.Response(text=json.dumps(output_metadata),status=200)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return web.Response(text=json.dumps(f"Error occured > {str(e)}"), status=500)
        # else:
        #     return web.Response(text=json.dumps(f"Unauthorized"), status=401)

    @monitor_time
    @authenticate
    @rate_limit
    async def get_scenarios(self, request):

        try:

            with session_manager() as session:
                base_scenarios = self.db.get_base_scenarios(session)
                personnel_scenarios = self.db.get_scenarios_by_user(session, request['userData']['username'])
            
            print(personnel_scenarios)
            return web.Response(text=json.dumps({"base": base_scenarios, "personnel": personnel_scenarios}),status=200)
        
        
        except Exception as e:
            return web.Response(text=json.dumps(f"Error occured > {str(e)}"), status=500)
       
    
    @monitor_time
    @authenticate
    @rate_limit
    async def update_label_status(self, request):
        
        try:
            data = await request.json()
            with session_manager() as session:
                self.db.update_label_status(session, request['userData']['username'],data['enabled'], data['label'])
                session.commit()
            return web.Response(text=json.dumps({"message": "success"}),status=200)
        except Exception as e:
            return web.Response(text=json.dumps(f"Error occured > {str(e)}"), status=500)
      

    @monitor_time
    @authenticate
    @rate_limit
    async def get_lable_statuses(self, request):
        
        try:
            with session_manager() as session:
                status_dict = self.db.get_label_status_dict(session, request['userData']['username'])
            return web.Response(text=json.dumps(status_dict),status=200)
        except Exception as e:
            return web.Response(text=json.dumps(f"Error occured > {str(e)}"), status=500)
      

    @monitor_time
    @authenticate
    @rate_limit
    async def delete_personnel_scenario_state(self, request):
       
        try:
            with session_manager() as session:
                self.db.delete_personnel_scenario_state(session, request['userData']['username'])
                session.commit()
            return web.Response(text=json.dumps({"message": "success"}),status=200)
        except Exception as e:
            return web.Response(text=json.dumps(f"Error occured > {str(e)}"), status=500)
        


    @monitor_time
    @authenticate
    @rate_limit
    async def get_personnel_scen_state(self, request):
        
        try:
            with session_manager() as session:
                data = self.db.get_personnel_scen_state(session, request['userData']['username'])
            
            if data:
                return web.Response(text=json.dumps(data.decode()),status=200)
            else:
                return web.Response(text=json.dumps({"message": "no data"}),status=500)
        except Exception as e:
            return web.Response(text=json.dumps(f"Error occured > {str(e)}"), status=500)
      

    @monitor_time
    @authenticate
    @rate_limit
    async def get_default_scen_state(self, request):
        
        try:
            with session_manager() as session:
                data = self.db.get_default_scen_state(session, request['userData']['username'])
            
            if data:
                return web.Response(text=json.dumps(data.decode()),status=200)
            else:
                return web.Response(text=json.dumps({"message": "no data"}),status=500)
        except Exception as e:
            return web.Response(text=json.dumps(f"Error occured > {str(e)}"), status=500)
        

    @monitor_time
    async def handle_get_technologies(self, request):

        import numpy as np
        try:
            # Read IVT file and provide a list of technologies with description
            ivt_file = os.path.join(os.path.dirname(__file__), '..', '..', 'A_Inputs',  'inputs', 'generators', 'ivt.csv')
            df = pd.read_csv(ivt_file)

            technologies = []
            for i in range(len(df)):
                
                row_data = df.iloc[i]
                tech_name = row_data.pop('Unnamed: 0')
                year_turned_on = [key for key, val in row_data.items() if not np.isnan(val)]

                technologies.append({
                    'name': tech_name,
                    'display_name': tech_name if 'BATTERY' not in tech_name else "BATTERY ("+ tech_name.split('_')[1] + " hour)",
                    'description': f"CCGT: Combined Cycle Gas Turbine, LNG: Liquified Natural Gas, CT: Combustion Turbine, Turned on years: {year_turned_on}"
                })

            return web.Response(text=json.dumps(technologies),status=200)
        
        except Exception as e:
            return web.Response(text=json.dumps(f"Error occured > {str(e)}"), status=500)

    @monitor_time
    @authenticate
    @rate_limit
    async def get_output_card_state(self, request):
        
        try:
            with session_manager() as session:
                data = self.db.get_output_card_state(session, request['userData']['username'])
            if data:
                print(data.decode())
                return web.Response(text=json.dumps(data.decode()),status=200)
            else:
                return web.Response(text=json.dumps({"message": "no data"}),status=500)
        except Exception as e:
            return web.Response(text=json.dumps(f"Error occured > {str(e)}"), status=500)
    
    
    @monitor_time
    @authenticate
    @rate_limit
    async def update_personnel_scen_state(self, request):

        try:
            data = await request.json()
            binary_string = data['data'].encode('utf-8')
            with session_manager() as session:
                self.db.update_personnel_scen_state(session, request['userData']['username'], binary_string)
                session.commit()
            return web.Response(text=json.dumps({"status": "success"}),status=200)
        except Exception as e:
            return web.Response(text=json.dumps(f"Error occured > {str(e)}"), status=500)
        

    @monitor_time
    @authenticate
    @rate_limit
    async def update_default_scen_state(self, request):
       
        try:
            data = await request.json()
            binary_string = data['data'].encode('utf-8')
            with session_manager() as session:
                self.db.update_default_scen_state(session, request['userData']['username'], binary_string)
                session.commit()
            return web.Response(text=json.dumps({"status": "success"}),status=200)
        except Exception as e:
            return web.Response(text=json.dumps(f"Error occured > {str(e)}"), status=500)
     

    @monitor_time
    @authenticate
    @rate_limit
    async def update_output_card_state(self, request):

        try:
            data = await request.json()
            binary_string = data['data'].encode('utf-8')
            with session_manager() as session:
                self.db.update_output_card_state(session, request['userData']['username'], binary_string)
                session.commit()
            return web.Response(text=json.dumps({"status": "success"}),status=200)
        except Exception as e:
            return web.Response(text=json.dumps(f"Error occured > {str(e)}"), status=500)
        

    @monitor_time
    @authenticate
    @rate_limit
    async def clone_scenarios(self, request):
        
        try:
        
            # Trying to read json data
            data = await request.json()

            metadata = {    "name": data["name"] + '_copy',
                            "author": request['userData']['username'],
                            "created": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "status": "Ready to test",
                            "description": data["description"]
                        }
    
            # Let's read the case.csv file and update the content of that file

            case_csv_file = os.path.join(os.path.dirname(__file__), '..', 'users_cases', request['userData']['username'], 'cases.csv')
            case_df = pd.read_csv(case_csv_file)

            # check if name already exists or if the name is empty
            if data['name'] not in list(case_df.columns):
                return web.Response(text=json.dumps(f"{data['name']} does not exist, can not clone"), status=500)
            
            if not data['name']:
                return web.Response(text=json.dumps(f"Scenario name cannot be empty"), status=500)
                    
            
            # check if name already exists or if the name is empty
            if metadata['name'] in list(case_df.columns):
                return web.Response(text=json.dumps(f"{metadata['name']} already exists, please consider renaming ealier cloned copy and try again"), status=500)
            
            
            old_scenario_list = case_df[data['name']].tolist()
            case_rows = case_df['case'].to_list()
            new_scenario_list = []
            
            # Let's also update the file content
            for key, item in zip(case_rows, old_scenario_list):

                # Check if the key type belongs to FILE
                # Here we are assuming all the file_type keys are updated in mapper.py
                if isinstance(item, str):
                    if item.endswith('.csv') and key in FILE_KEYS:
                        
                        # Avoid copying default files
                        if item not in DEFAULT_FILE_TO_CATEGORY.get(key, {}):
                            # Let's create file_uuid
                            file_name = str(uuid4()) + '.csv'

                            # where to write the file
                            base_folder = os.path.join(os.path.dirname(__file__), '..', '..', 'A_Inputs', 'inputs')

                            shutil.copy(os.path.join(base_folder, FILE_LOCATION[key], item), os.path.join(base_folder, FILE_LOCATION[key], file_name))
                            item = file_name
                    

                new_scenario_list.append(item)

            # Now need to update the dataframe
            case_df[metadata['name']] = new_scenario_list

            # rewrite the case.csv file
            case_df.to_csv(case_csv_file, index=False)

            # Insert into the database
            
            with session_manager() as session:
                self.db.insert_scenario_metadata(session, metadata)
                session.commit()
            # Update the metadata and scenarios
            # self.update_scenarios_and_output()

            with session_manager() as session:
                scenarios_personnel = self.db.get_scenarios_by_user(session, request['userData']['username'])
            return web.Response(text=json.dumps(scenarios_personnel),status=200)

        except Exception as e:
            return web.Response(text=json.dumps(f"Error occured > {str(e)}"), status=500)
        

    @monitor_time
    @authenticate
    @rate_limit
    async def update_scenarios(self, request):
        
        
        try:
        
            # Trying to read multipart/form-data using the aiohttp post coroutine
            data = await request.post()

            # Just a container to store the parsed data
            parsed_data = {}
            
            for key, value in data.items():

                # check if the type is aiohttp.web_request.FileField
                if isinstance(value, aiohttp.web_request.FileField):

                    # get the filename and read file_content
                    filename = value.filename

                    # The read function gives binary encoded content which will decode using utf-8 and will write into a proper destination
                    filecontent = value.file.read()
                    filecontent = filecontent.decode()

                    parsed_data[key] = filecontent


                elif isinstance(value, str):

                    # we are going to assume all str can be jsonified
                    try:
                        parsed_data[key] = json.loads(value)
                    except Exception as e:
                        parsed_data[key] = value

            
            base_folder = os.path.join(os.path.dirname(__file__), '..', '..', 'A_Inputs', 'inputs')
            form_data = parsed_data.pop('formdata')
            file_allow = parsed_data.pop('file_allow')
            technologies = parsed_data.pop('technologies')
            update_action = parsed_data.pop('action', {'update': False})['update']

            metadata = {    "name": form_data.pop("scen_name"),
                            "author": request['userData']['username'],
                            "created": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "status": "Ready to test",
                            "description": form_data.pop("description")
                        }
    
            # Let's read the case.csv file and update the content of that file

            case_csv_file = os.path.join(os.path.dirname(__file__), '..', 'users_cases', request['userData']['username'], 'cases.csv')
            case_df = pd.read_csv(case_csv_file)

            if not metadata['name']:
                return web.Response(text=json.dumps(f"Scenario name cannot be empty"), status=500)

            case_rows = case_df['case'].to_list()
            if update_action:
                # Check if name does not exist for update case
                if metadata['name'] not in list(case_df.columns):
                    return web.Response(text=json.dumps(f"{metadata['name']} scenario does not exist"), status=500)

                case_row_dict = dict(zip(case_rows, case_df[metadata['name']].to_list()))
            else:
                # check if name already exists or if the name is empty
                if metadata['name'] in list(case_df.columns):
                    return web.Response(text=json.dumps(f"{metadata['name']} already exists, use different name"), status=500)
                
                # By default all values are nans 
                case_row_dict = dict(zip(case_rows, [None]*len(case_rows)))

            # If yearset is present you need to create the csv for this
            yearset = form_data.get("yearset")
            if yearset is not None:

                # if yearset already exists in case_dict remove that
                if str(case_row_dict.get('yearset', None)).endswith('.csv'):
                    prev_yearset_file = case_row_dict['yearset']
                    try:
                        os.remove(os.path.join(os.path.dirname(__file__), '..', '..', 'A_Inputs','inputs', 'sets', prev_yearset_file))
                    except FileNotFoundError as e:
                        print(f"Error removing file >> {str(e)}")

                yearset_file = str(uuid4()) + 'modeled_year.csv'
                with open(os.path.join(os.path.dirname(__file__), '..', '..', 'A_Inputs','inputs', 'sets', yearset_file), "w") as f:
                    f.write(yearset)
                form_data["yearset"] = yearset_file
            # Let's update the case dict from the input
            case_row_dict.update(form_data)

            # Let's also update the file content
            for key, content in parsed_data.items():

                # Check if the key type belongs to FILE
                # Here we are assuming all the file_type keys are updated in mapper.py
                if key in FILE_KEYS and file_allow[key] == 'Custom Upload':
                    
                    # If file aready exists delete old one
                    if str(case_row_dict.get(key, None)).endswith('.csv'):
                        prev_file = case_row_dict[key]
                        try:
                            os.remove(os.path.join(base_folder, FILE_LOCATION[key], prev_file))
                        except FileNotFoundError as e:
                            print(f"Error removing file >> {str(e)}, key {key}")
                    # Let's create file_uuid
                    file_name = str(uuid4()) + '.csv'

                    # where to write the file
                    content = content.replace('\r\n', '\n')

                    f = open(os.path.join(base_folder, FILE_LOCATION[key] ,file_name), 'w')
                    f.write(content)
                    f.close()

                    case_row_dict[key] = file_name

            # Convert file options to proper file names
            for key, val in file_allow.items():
                if val not in ['Default', 'Custom Upload']:
                    case_row_dict[key] = DEFAULT_FILE_NAMES[key][val]

            # Need to create ivt file if necessary
            ivt_file = os.path.join(os.path.dirname(__file__), '..', '..', 'A_Inputs',  'inputs', 'generators', 'ivt.csv')
            df = pd.read_csv(ivt_file, index_col=[0])
            default_techs = list(df.index)
            
            if set(default_techs) != set(technologies):
                
                # Remove the ones that are not present
                tech_to_remove = list(set(default_techs) - set(technologies))
                df = df.drop(tech_to_remove)

                # Then write it to the correct location
                new_ivt_file_name = str(uuid4()) + '_ivt.csv'

                # If IVT file aready exists then remove the older one
                if str(case_row_dict.get('IVT_file', None)).endswith('.csv'):
                    prev_file = case_row_dict['IVT_file']
                    try:
                        os.remove(os.path.join(os.path.dirname(__file__), '..', '..', 'A_Inputs',  'inputs', 'generators', prev_file))
                    except FileNotFoundError as e:
                        print(f"Error removing file >> {str(e)}, key {key}")

                case_row_dict['IVT_file'] = new_ivt_file_name
                df.to_csv(os.path.join(os.path.dirname(__file__), '..', '..', 'A_Inputs',  'inputs', 'generators', new_ivt_file_name))

            
            # Now need to update the dataframe
            new_values = list(case_row_dict.values())

            if update_action:
                try:
                    case_df = case_df.drop(metadata['name'], axis=1)
                except KeyError as e:
                    print(f"Error deleting columns> {metadata['name']}")
            case_df[metadata['name']] = new_values

            # rewrite the case.csv file
            case_df.to_csv(case_csv_file, index=False)

            
            if not update_action:
                # Insert into the database
                with session_manager() as session:
                    self.db.insert_scenario_metadata(session, metadata)
                    session.commit()
            else:
                # Update the record in database
                with session_manager() as session:
                    self.db.update_scenario_metadata(session, metadata)
                    session.commit()

            # Update the metadata and scenarios
            # self.update_scenarios_and_output()
            with session_manager() as session:
                scenarios_personnel = self.db.get_scenarios_by_user(session, request['userData']['username'])
            return web.Response(text=json.dumps(scenarios_personnel),status=200)

        except Exception as e:
            return web.Response(text=json.dumps(f"Error occured > {str(e)}"), status=500)
       

    @monitor_time
    @authenticate
    @rate_limit
    async def delete_scenarios(self, request):

        try:
            data = await request.json()
            with session_manager() as session:
                scenarios_personnel = self.db.get_scenarios_by_user(session, request['userData']['username'])
    
            if data in scenarios_personnel:
                
                # delete from case.csv file
                # Let's read the case.csv file and update the content of that file
                try:
                    case_csv_file = os.path.join(os.path.dirname(__file__), '..', 'users_cases', request['userData']['username'], 'cases.csv')
                    case_df = pd.read_csv(case_csv_file)
                    case_row_dict = dict(zip(case_df['case'], case_df[data['name']]))

                    # remove files if any
                    for key, val in case_row_dict.items():
                        if key in FILE_KEYS:
                            
                            if val and not pd.isna(val):
                                if val not in DEFAULT_FILE_TO_CATEGORY.get(key, {}):
                                    try:
                                        os.remove(os.path.join(os.path.dirname(__file__), '..', '..', 'A_Inputs', 'inputs', FILE_LOCATION[key], val))
                                    except FileNotFoundError as e:
                                        print(f"File not found for deleting! >> {str(e)}")

                # drop the column from dataframe and rewrite
                    case_df = case_df.drop(data['name'], 1)
                    case_df.to_csv(case_csv_file, index=False)
                except Exception as e:
                    print(e)

                # delete from the database
                with session_manager() as session:
                    self.db.delete_scenario(session, data)
                    session.commit()
                # self.update_scenarios_and_output()

                with session_manager() as session:
                    scenarios_personnel = self.db.get_scenarios_by_user(session, request['userData']['username'])

            return web.Response(text=json.dumps(scenarios_personnel),status=200)
        except Exception as e:
            return web.Response(text=json.dumps(f"Error occured > {str(e)}"), status=500)

       

    @monitor_time
    @authenticate
    @rate_limit
    async def get_ouput_metadata(self, request):

        try:
            # TODO : check the process is alive or not and update the status

            # Check whether the processes are alive or not
            remove_uuids = []
            for reed_uuid in self.instances_dict.get(request['userData']['username'], []):
                
                run_name = self.instances_dict[request['userData']['username']][reed_uuid]['name']
                output_folder = os.path.join(os.path.dirname(__file__), '..', 'users_output', request['userData']['username'], run_name, 'exceloutput')
                if not self.instances_dict[request['userData']['username']][reed_uuid]['process'].is_alive():

                    remove_uuids.append(reed_uuid)
                    # Update the status in the database

                    # Check if the output folder exists
                    status = "ERROR"
                    if os.path.exists(output_folder):
                        file_exist = False
                        for file in os.listdir(output_folder):
                            if file.endswith('.xslx'):
                                file_exist = True

                        if file_exist:
                            status = "COMPLETED"
                    with session_manager() as session:
                        self.db.update_output_metadata_status(session, status, run_name, request['userData']['username'])
                        session.commit()
                
                else:
                    # x = threading.Thread(target=self.compute_cpu_usage_and_update_output_metadata, args=(request['userData']['username'],self.instances_dict[request['userData']['username']][reed_uuid]['process'],run_name))
                    # x.start()
                    # Check for the error file
                    error_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'D_Augur', 'ErrorFile')
                    
                    error_file_exists = False
                    for file in error_dir:
                        if run_name in file:
                            error_file_exists = True
                    
                    if error_file_exists:
                        with session_manager() as session:
                            status = 'ERROR'
                            self.db.update_output_metadata_status(session, status, run_name, request['userData']['username'])

                # self.update_scenarios_and_output()

            for uuid_ in remove_uuids:
                self.instances_dict[request['userData']['username']].pop(uuid_)

            with session_manager() as session:
                output_metadata = self.db.get_output_metadata(session, request['userData']['username'])

            return web.Response(text=json.dumps(output_metadata),status=200)
        except Exception as e:
            return web.Response(text=json.dumps(f"Error occured > {str(e)}"), status=500)
        

    @monitor_time
    @authenticate
    @rate_limit
    async def delete_output_metadata(self, request):
        
        try:
            data = await request.json()

            if data['status'] == 'INQUEUE':
                with data_lock:
                    temp_queue = Queue()
                    for _ in range(self.simulation_queue.qsize()):
                        q_el = self.simulation_queue.get()
                        if q_el['uuid'] != data['uuid'] or q_el['username'] != request['userData']['username']:
                            temp_queue.put(q_el)
                    self.simulation_queue = temp_queue

            with session_manager() as session:
                output_metadata = self.db.get_output_metadata(session, request['userData']['username'])
                self.db.delete_simulation_queue(session, request['userData']['username'], data['uuid'])
                session.commit()

            if data in output_metadata:
                
                #  Kill the process if alive
                for uuid_ in self.instances_dict.get(request['userData']['username'], []):
                    if self.instances_dict[request['userData']['username']][uuid_]['name'] == data['name']:
                        if self.instances_dict[request['userData']['username']][uuid_]['process'].is_alive():
                            self.instances_dict[request['userData']['username']][uuid_]['process'].terminate()

                # delete the folder from E-Outputs folder
                try:
                    run_folder = os.path.join(os.path.dirname(__file__), '..', 'users_output', request['userData']['username'])
                
                    for folder in os.listdir(run_folder):
                        if data['name'] in folder:
                            shutil.rmtree(os.path.join(run_folder, folder))

                    
                    error_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'D_Augur', 'ErrorFile')
                    for file in error_dir:
                        if data['name'] in file:
                            os.remove(os.path.join(error_dir, file))

                    # Delete the html from F_Analysis if exists
                    # analysis_folder = os.path.join(os.path.dirname(__file__), '..', '..', 'F_Analysis')
                    # for file in os.listdir(analysis_folder):
                    #     if file.endswith('html') and f"ReEDS-India-results_{data['name']}" in file:
                    #         os.remove(file)


                except Exception as e:
                    print(str(e))
                    pass

                
                with session_manager() as session:
                    self.db.delete_output_metadata(session, data)
                    session.commit()
                    output_metadata = self.db.get_output_metadata(session,request['userData']['username'])

            return web.Response(text=json.dumps(output_metadata),status=200)
        except Exception as e:
            return web.Response(text=json.dumps(f"Error occured > {str(e)}"), status=500)


    @monitor_time
    @rate_limit
    async def get_reset_token(self, request):

        user_detail = await request.json()
        with session_manager() as session:
            user = self.db.is_useremail_exist(session, user_detail['email'])
            if user:
                token, hashed_token = self.hash.get_reset_token(user)

                if token != None:
                    reset_link = f"{os.getenv('BASE_URL_RESET_PASSWORD')}/{token}"

                    # Let's update the database
                    token = token.encode('utf-8')
                    self.db.insert_or_update_reset_token(session, hashed_token, user.username)
                    session.commit()

                    email_body = UserPasswordResetHTMLMessage().return_rendered_html({
                        'reset_link': reset_link
                    })
                    # print(email_body)

                    # TODO: Activate this email during the testing
                    self.mail.send_email(os.getenv('REEDS_SENDER'), user.email, email_body, USER_RESET_EMAIL_SUBJECT)
        return web.Response(text=json.dumps({
            'message':  "Email has been sent if it exists in our system!"
        }),status=200)

    @monitor_time
    async def handle_password_reset(self, request):

        try:
            token = request.match_info['token']
            decoded = jwt.decode(token, JWT_KEY, algorithms=['HS256'])
            with session_manager() as session:
                validate_token = self.db.check_reset_token(session, decoded['username'], token)
                if validate_token:
                    
                    user_detail = await request.json()
                    hash_pwd, salt = self.hash.hash_string(user_detail['password'])
                    self.db.update_user_info_by_username(session, decoded['username'], 'password', hash_pwd)
                    session.commit()
                    return web.Response(text=json.dumps({
                        'message':  "Password updated successfully!"
                    }),status=200)
                else:
                    return web.Response(text=json.dumps({
                    'message':  "Token is invalid, Unauthorized to reset password!"
                    }),status=401)

        except Exception as e:
            return web.Response(text=json.dumps({
            'message':  f"Error occurred during reset password! >> {str(e)}"
            }),status=500)
        
        # Need to validate the token
        # with session_manager() as session:
    
    @monitor_time
    @rate_limit
    async def handle_user_signup_request(self, request):

        try:
            user_detail = await request.json()
            with session_manager() as session:
                self.db.insert_user_signup_request(session, user_detail)
                session.commit()

            # Need to send email to reeds-team for notification purpose
            email_body = UserSignUpRequestNotificationHTMLMessage().return_rendered_html({
                'name': user_detail['first_name'] + ' ' + user_detail['last_name'],
                'email': user_detail['email'],
                'description': user_detail['description']
            })
            # print(email_body)

            # TODO: Activate this email during the testing
            self.mail.send_email(os.getenv('REEDS_SENDER'), os.getenv('REEDS_SENDER'), email_body, USER_SIGNUP_REQUEST_SUBJECT)

            return web.Response(text=json.dumps({
            'message':  f"Success submitting the request!"
            }),status=200) 
        
        except Exception as e:
            return web.Response(text=json.dumps({
            'message':  f"Error occurred during processing new user request! >> {str(e)}"
            }),status=500)

    
    # admin_authenticated
    @monitor_time
    @authenticate
    @rate_limit
    async def handle_admin_check(self, request):

        with session_manager() as session:
            is_admin = self.db.is_admin(session, request['userData']['username'])
        
        if is_admin:
            return web.Response(text=json.dumps({'message': 'authenticated'}),status=200)
        else:
            return web.Response(text=json.dumps(f"Unauthorized"), status=401)
       

    @monitor_time
    @authenticate
    @rate_limit
    async def return_users_requests(self, request):
            
        try:
            is_admin = False
            with session_manager() as session:
                if self.db.is_admin(session, request['userData']['username']):
                    is_admin = True
                    user_request_objects = self.db.get_users_request(session)
                    token_object = self.db.get_token_email_dict(session)
                    user_requests = [{ 'name': req_obj.first_name + ' ' + req_obj.last_name,
                            'email': req_obj.email,
                            'request_date': req_obj.requested_date.strftime('%Y-%m-%d %H:%M:%S'),
                            'country': req_obj.country,
                            'organization': req_obj.organization,
                            'status': req_obj.request_status,
                            'description': req_obj.description.decode(),
                            'token': token_object.get(req_obj.email, None)
                        } for req_obj in user_request_objects
                    ]
            
            if is_admin:
                return web.Response(text=json.dumps(user_requests),status=200)
            else:
                return web.Response(text=json.dumps(f"Unauthorized"), status=401)
        except Exception as e:
            return web.Response(text=json.dumps(f"Error occured > {str(e)}"), status=500)

      

    @monitor_time
    @authenticate
    @rate_limit
    async def delete_user_signup_request(self, request):
    
        try:
            is_admin = False
            with session_manager() as session:
                if self.db.is_admin(session, request['userData']['username']):
                    
                    is_admin = True
                    data = await request.json()
                    self.db.delete_user_signup_request(session, data['email'])
                    session.commit()

                    user_request_objects = self.db.get_users_request(session)
                    token_object = self.db.get_token_email_dict(session)
                    user_requests = [{ 'name': req_obj.first_name + ' ' + req_obj.last_name,
                            'email': req_obj.email,
                            'request_date': req_obj.requested_date.strftime('%Y-%m-%d %H:%M:%S'),
                            'country': req_obj.country,
                            'organization': req_obj.organization,
                            'status': req_obj.request_status,
                            'description': req_obj.description.decode(),
                            'token': token_object.get(req_obj.email, None)
                        } for req_obj in user_request_objects
                    ]
            
            if is_admin:
                return web.Response(text=json.dumps(user_requests),status=200)
            else:
                return web.Response(text=json.dumps(f"Unauthorized"), status=401)
        except Exception as e:
            return web.Response(text=json.dumps({"message":f"Error occured > {str(e)}"}), status=500)

       

    @monitor_time
    @authenticate
    @rate_limit
    async def handle_user_request_approval(self, request):
            
        try:
            is_admin = False
            with session_manager() as session:
                if self.db.is_admin(session, request['userData']['username']):
                    
                    is_admin = True
                    data = await request.json()

                    # Let's create a token and send email out to user
                    token = str(uuid.uuid4())
                    self.db.insert_signup_token(session, data['email'], token)
                    self.db.update_signup_request_status(session, data['email'], 'APPROVED')
                    session.commit()

                    signup_url = f"{os.getenv('BASE_URL_USER_SIGNUP')}/{token}"
                    email_body = UserSignUpInstructionsHTMLMessage().return_rendered_html({
                    'signup_link': signup_url
                    })
                    # print(email_body)

                    # TODO: Activate this email during the testing
                    self.mail.send_email(os.getenv('REEDS_SENDER'), data['email'], email_body, USER_SIGNUP_EMAIL_SUBJECT)

                    user_request_objects = self.db.get_users_request(session)
                    token_object = self.db.get_token_email_dict(session)
                    user_requests = [{ 'name': req_obj.first_name + ' ' + req_obj.last_name,
                            'email': req_obj.email,
                            'request_date': req_obj.requested_date.strftime('%Y-%m-%d %H:%M:%S'),
                            'country': req_obj.country,
                            'organization': req_obj.organization,
                            'status': req_obj.request_status,
                            'description': req_obj.description.decode(),
                            'token': token_object.get(req_obj.email, None)
                        } for req_obj in user_request_objects
                    ]
            
            if is_admin:
                return web.Response(text=json.dumps(user_requests),status=200)
            else:
                return web.Response(text=json.dumps(f"Unauthorized"), status=401)
        except Exception as e:
            return web.Response(text=json.dumps(f"Error occured > {str(e)}"), status=500)

     

    @monitor_time
    @authenticate
    @rate_limit
    async def handle_user_request_rejection(self, request):
          
        try:
            is_admin = False
            with session_manager() as session:
                if self.db.is_admin(session, request['userData']['username']):
                    
                    is_admin = True
                    data = await request.json()

                    self.db.delete_signup_token(session, data['email'])
                    self.db.update_signup_request_status(session, data['email'], 'REJECTED')
                    session.commit()

                    email_body = UserSignUpRejectionHTMLMessage().return_rendered_html({})
                    # print(email_body)

                    # TODO: Activate this email during the testing
                    self.mail.send_email(os.getenv('REEDS_SENDER'), data['email'], email_body, USER_SIGNUP_EMAIL_REJECT_SUBJECT)

                    user_request_objects = self.db.get_users_request(session)
                    token_object = self.db.get_token_email_dict(session)
                    user_requests = [{ 'name': req_obj.first_name + ' ' + req_obj.last_name,
                            'email': req_obj.email,
                            'request_date': req_obj.requested_date.strftime('%Y-%m-%d %H:%M:%S'),
                            'country': req_obj.country,
                            'organization': req_obj.organization,
                            'status': req_obj.request_status,
                            'description': req_obj.description.decode(),
                            'token': token_object.get(req_obj.email, None)
                        } for req_obj in user_request_objects
                    ]
            
            if is_admin:
                return web.Response(text=json.dumps(user_requests),status=200)
            else:
                return web.Response(text=json.dumps(f"Unauthorized"), status=401)
        except Exception as e:
            return web.Response(text=json.dumps(f"Error occured > {str(e)}"), status=500)

    @monitor_time
    async def validate_user_signup_token(self, request):

        token = request.match_info['token']
        
        with session_manager() as session:
            token_is_valid = self.db.is_signup_token_valid(session, token)

        status_code = 200 if token_is_valid else 401
        return web.Response(text=json.dumps(f"{token_is_valid}"), status=status_code)

    @monitor_time
    @authenticate
    async def validate_user_password_reset_token(self, request):

        token = request.match_info['token']
        decoded = jwt.decode(token, JWT_KEY, algorithms=['HS256'])
        with session_manager() as session:
            validate_token = self.db.check_reset_token(session, decoded['username'], token)

        status_code = 200 if validate_token else 401
        return web.Response(text=json.dumps(f"{validate_token}"), status=status_code)

    @monitor_time
    @authenticate
    @rate_limit
    async def update_bug_status(self, request):
        try:
            with session_manager() as session:
                if self.db.is_admin(session, request['userData']['username']):
                    data = await request.json()

                    # Let's create a token and send email out to user
                    self.db.update_bug_status(session, data['uuid'], data['status'])
                    session.commit()

                    return web.Response(text=json.dumps(f"success"),status=200)
            return web.Response(text=json.dumps(f"Unauthorized"), status=401)
        except Exception as e:
            return web.Response(text=json.dumps(f"Error occured > {str(e)}"), status=500)

    @monitor_time
    @authenticate
    @rate_limit
    async def handle_delete_bug(self, request):
        try:
            with session_manager() as session:
                if self.db.is_admin(session, request['userData']['username']):
                    data = await request.json()

                    # Let's create a token and send email out to user
                    self.db.delete_bug(session, data['uuid'])
                    session.commit()

                    return web.Response(text=json.dumps(f"success"),status=200)
            return web.Response(text=json.dumps(f"Unauthorized"), status=401)
        except Exception as e:
            return web.Response(text=json.dumps(f"Error occured > {str(e)}"), status=500)
