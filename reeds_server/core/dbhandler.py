# Class to handle database related tasks


from web.create_db import (OutputMetadata, Scenarios, Bugs, ScenarioLabels, Labels, 
    PersonnelScenarioState, DefaultScenarioState, OutputCardState, Rules,
    Users, UserResetToken, UserSignUpRequest, UserSignupToken, SimulationQueue)
from sqlalchemy import and_
import datetime
import bcrypt
import json
from web.constants import DEFAULT_RATES_FOR_ALL_USERS

class DatabaseHandler:
    
    def is_user_exist(self, session, user):

        """ Checks whether user exists or not !"""
        user_1 = session.query(Users).filter(Users.username == user['username']).first()
        user_2 = session.query(Users).filter(Users.email == user['email']).first()
        return user_1 or user_2

    def is_useremail_exist(self, session, email):
        """ Check whetehr the user email exists or not"""
        user1 = session.query(Users).filter(Users.email == email).first()
        return user1

    def delete_label(self, session, user, label_name):

        """ Delete the label from labels table for particulat user """
        session.query(Labels).filter(and_(Labels.user == user, 
                    Labels.name == label_name)
                    ).delete(synchronize_session=False)

        """ Make sure to delete the scenario labels as well for the user """
        session.query(ScenarioLabels).filter(and_(ScenarioLabels.user == user, 
                    ScenarioLabels.label == label_name)
                    ).delete(synchronize_session=False)

    def delete_scenario_card_label(self, session, user, scenario, label):
        
        session.query(ScenarioLabels).filter(and_(
            ScenarioLabels.user == user,
            ScenarioLabels.scenario == scenario,
            ScenarioLabels.label == label
        )).delete(synchronize_session=False)

    def delete_personnel_scenario_state(self, session, user):
        session.query(PersonnelScenarioState).filter(PersonnelScenarioState.user == user).delete(synchronize_session=False)

    def get_bugs(self, session, max_bugs=20):
        
        """ Gives list of bugs"""
        bugs = session.query(Bugs).limit(max_bugs).all()
        # Just incase if you want to print actual sql query under the hood
        # bugs.statement.compile(engine)
        return [[bug.uuid, bug.created.strftime("%Y-%m-%d %H:%M:%S"), bug.title, bug.body, bug.status] for bug in bugs]

    def __convert_to_list_of_dict(self, list_of_list, keys, remove_keys = []):

        list_of_dict = []
        for arr in list_of_list:
            if len(arr) == len(keys):
                arr_dict = dict(zip(keys, arr))
                for k in remove_keys:
                    arr_dict.pop(k)

                list_of_dict.append(arr_dict)
        return list_of_dict

    def get_scenario_description(self, session, username, scenario_name):
        
        scenario = session.query(Scenarios).filter(and_(Scenarios.author == username, Scenarios.name == scenario_name)).first()
        return scenario.description if scenario else None    

    def get_scenarios_by_user(self, session, username):
        """ Gives a list of personel scenarios by username """
        # Get personnel scenarios filtered by username 
        personnel_scenarios_ = session.query(Scenarios).filter(Scenarios.author == username).all()
        # self.cursor.execute("SELECT * FROM scenarios where author = ?", [username])
        # personnel_scenarios = self.cursor.fetchall()
        personnel_scenarios = []
        for pscenario in personnel_scenarios_:
            personnel_scenarios.append([pscenario.name, pscenario.author, pscenario.created.strftime("%Y-%m-%d %H:%M:%S"), pscenario.status, \
                pscenario.description, pscenario.scen_type])
        
        # Convert to a list of dict
        keys = ['name', 'author', 'created', 'status', 'description', 'type']
        return self.__convert_to_list_of_dict(personnel_scenarios, keys, remove_keys=['type'])


    def get_base_scenarios(self, session):

        """ Gives a list of default base scenarios"""
        # Get personnel scenarios filtered by username 
        base_scenarios_ = session.query(Scenarios).filter(Scenarios.author == 'NREL (ReEDS India)').all()
        # self.cursor.execute("SELECT * FROM scenarios where author = ?", ['NREL (ReEDS India)'])
        # base_scenarios = self.cursor.fetchall()
        
        # Convert to a list of dict
        keys = ['name', 'author', 'created', 'status', 'description', 'type']
        base_scenarios = []
        for bscenario in base_scenarios_:
            if bscenario.name != 'Default Value':
                base_scenarios.append([bscenario.name, bscenario.author, bscenario.created.strftime("%Y-%m-%d %H:%M:%S"), bscenario.status, \
                    bscenario.description, bscenario.scen_type])
        
        return self.__convert_to_list_of_dict(base_scenarios, keys, remove_keys=['type'])

    def check_label_exists(self, session, user, name):

        labels = session.query(Labels).filter(and_(Labels.user == user, Labels.name == name)).all()
        return True if len(labels) !=0 else False

    def update_personnel_scen_state(self, session, user, data):
        """ Updates personnel scenario state order """
        scen_state = session.query(PersonnelScenarioState).filter(PersonnelScenarioState.user == user).first()
        if scen_state:
            session.query(PersonnelScenarioState).filter(PersonnelScenarioState.user == user).update({PersonnelScenarioState.personnel_scen_order: data}, synchronize_session=False)
        else:
            scen_state = PersonnelScenarioState()
            scen_state.user = user
            scen_state.personnel_scen_order = data
            session.add(scen_state)

    def update_default_scen_state(self, session, user, data):
        
        """ Updates personnel default state order """
        scen_state = session.query(DefaultScenarioState).filter(DefaultScenarioState.user == user).first()
        if scen_state:
            session.query(DefaultScenarioState).filter(DefaultScenarioState.user == user).update({DefaultScenarioState.default_scen_order: data}, synchronize_session=False)
        else:
            scen_state = DefaultScenarioState()
            scen_state.user = user
            scen_state.default_scen_order = data
            session.add(scen_state)

    def update_output_card_state(self, session, user, data):
        
        """ Updates output data state order """
        scen_state = session.query(OutputCardState).filter(OutputCardState.user == user).first()
        if scen_state:
            session.query(OutputCardState).filter(OutputCardState.user == user).update({OutputCardState.output_card_order: data}, synchronize_session=False)
        else:
            scen_state = OutputCardState()
            scen_state.user = user
            scen_state.output_card_order = data
            session.add(scen_state)


    def get_personnel_scen_state(self, session, username):
        """ Get's personnel scenario state """
        personnel_scenario = session.query(PersonnelScenarioState).filter(PersonnelScenarioState.user == username).first()
        return personnel_scenario.personnel_scen_order if personnel_scenario else False


    def get_default_scen_state(self, session, username):
        """ Get's default scenario state """
        default_scenario = session.query(DefaultScenarioState).filter(DefaultScenarioState.user == username).first()
        return default_scenario.default_scen_order if default_scenario else False

    def get_output_card_state(self, session, username):

        output_scenario = session.query(OutputCardState).filter(OutputCardState.user == username).first()
        return output_scenario.output_card_order if output_scenario else False

    def update_label_status(self, session, username, enabled, label):
        session.query(Labels).filter(and_(Labels.user == username, Labels.name == label)).update({Labels.is_enabled: enabled}, synchronize_session=False)

    def get_label_status_dict(self, session, username):

        labels = session.query(Labels).filter(Labels.user == username).all()
        return {label.name: label.is_enabled for label in labels}

    def insert_label(self, session, user, created, name, description, enabled='no'):
        """ Inserts label """
        # Check if the name is not empty
        if name:
            
            # Check whether the label exists already for this user
            if not self.check_label_exists(session, user, name):

                # Insert the label
                label = Labels()
                label.user = user
                label.created = created
                label.name = name
                label.description = description
                label.is_enabled = enabled
                session.add(label)

                return (True, 'success')
            else:
                return (False, "Duplicate label can not exist!")
        else:
            return (False, "Name can not be empty")

    def get_all_user_labels(self, session,  username): 
        
        """ Get all user labels """
        labels = session.query(Labels).filter(Labels.user == username).all()
        return [{"name": label.name, "created": label.created.strftime("%Y-%m-%d %H:%M:%S"), "description": label.description} for label in labels]

    def check_scenario_label_exists(self, session,  user, scen_name, label):

        scen_label = session.query(ScenarioLabels).filter(and_(ScenarioLabels.user == user, ScenarioLabels.scenario == scen_name, ScenarioLabels.label == label)).first()
        return True if scen_label else False

    def get_scenario_tag_list(self, session, username):

        scenario_labels = session.query(ScenarioLabels).filter(ScenarioLabels.user == username).all()

        label_data_dict = {}
        for scenario in scenario_labels:
            if  scenario.scenario not in label_data_dict:
                label_data_dict[scenario.scenario] = []
            label_data_dict[scenario.scenario].append(scenario.label)
        
        return label_data_dict

    def insert_or_update_reset_token(self, session, token, username):

        reset_token = session.query(UserResetToken).filter(UserResetToken.username == username).first()
        if reset_token:
            session.query(UserResetToken).filter(UserResetToken.username==username).update(
                { UserResetToken.token : token,
                  UserResetToken.token_created_date: datetime.datetime.utcnow()
                }, 
            synchronize_session=False)

        else:
            reset_token = UserResetToken()
            reset_token.username = username
            reset_token.token = token
            session.add(reset_token)

    def insert_scenario_label(self, session, username, scenario, label, created):

        # Check if label exists
        user_labels = self.get_all_user_labels(session, username)
        labels = [d['name'] for d in user_labels]
        if label in labels:
            # Check if the label exists
            if not self.check_scenario_label_exists(session, username, scenario, label):

                scen_label = ScenarioLabels()
                scen_label.user = username
                scen_label.scenario = scenario
                scen_label.label = label
                scen_label.created = created
                session.add(scen_label)

                return (True, '')
            else:
                return (False, f"{label} label already exists for this {scenario}")
        else:
            return (False, "Label does not exist, first create the label")
        


    def get_output_metadata(self, session, username):

        """ Retrieves the output metadata """
        out_data = session.query(OutputMetadata).filter(OutputMetadata.author == username).all()
        
        keys = ['name', 'author', 'created', 'status', 'size', 'description', 'uuid']
        output_metadata = []
        for d in out_data:
            output_metadata.append([d.name, d.author, d.created.strftime("%Y-%m-%d %H:%M:%S"), d.status, d.size, d.description, d.uuid])

        return self.__convert_to_list_of_dict(output_metadata, keys)


    def update_user_info_by_username(self, session,  username, key, value):
        session.query(Users).filter(Users.username==username).update({eval(f'Users.{key}') : value}, synchronize_session=False)

    def update_password(self, session, password, username):
        session.query(Users).filter(Users.username == username).update({Users.password: password}, synchronize_session=False)
        
    def get_hpwd(self, session, username):
        user = session.query(Users).filter(Users.username == username).first()
        return user.password if user else None
        
    def get_user_data(self, session, username):

        user = session.query(Users).filter(Users.username==username).first()
        return {'username': user.username, 'email': user.email, 'country': user.country, 'organization': user.organization} if user else None
       

    def get_image_name(self, session, username):
        user = session.query(Users).filter(Users.username == username).first()
        return user.image_name if user else None


    def insert_user(self, session, user):
        
        """ Inserts user into the database !"""
        user_ = Users()
        user_.username = user['username']
        user_.password = user['password']
        user_.email = user['email']
        user_.country = user['country']
        user_.organization = user['organization']
        user_.image_name = user['image_name']
        session.add(user_)
        return True

    def insert_bug(self, session,  uuid, created, title, body, status):

        bug = Bugs()
        bug.uuid = uuid
        bug.created = created
        bug.title = title
        bug.body = body
        bug.status = status

        session.add(bug)

        return True
    
    def insert_scenario_metadata(self, session, metadata):

        """ Inserts scenario metadata """
        scen_data = Scenarios()
        scen_data.name = metadata['name']
        scen_data.author = metadata['author']
        scen_data.created = metadata['created']
        scen_data.status = metadata['status']
        scen_data.description = metadata['description']
        scen_data.scen_type = 'personnel'
        session.add(scen_data)

    def update_scenario_metadata(self, session, metadata):

        """ Updates scenario metadata """

        session.query(Scenarios).filter(Scenarios.name == metadata['name']).update({
                Scenarios.created : metadata['created'],
                Scenarios.status : metadata['status'],
                Scenarios.description: metadata['description']
            },
            synchronize_session= False
        )


    def insert_output_metadata(self, session, metadata):

        out_data = OutputMetadata()
        out_data.name = metadata['name']
        out_data.author = metadata['author']
        out_data.created = metadata['created']
        out_data.status = metadata['status']
        out_data.size = metadata['size']
        out_data.uuid = metadata['uuid']
        out_data.description = metadata['description']
        session.add(out_data)

    def update_output_metadata(self, session, metadata):

        session.query(OutputMetadata).filter(OutputMetadata.name == metadata['name']).update({
                OutputMetadata.created : metadata['created'],
                OutputMetadata.status : metadata['status'],
                OutputMetadata.description: metadata['description']
            },
            synchronize_session= False
        )

    def update_output_metadata_status(self, session, status, run_name, username):

        session.query(OutputMetadata).filter(and_(
            OutputMetadata.name == run_name,
            OutputMetadata.author == username
            )).update({
                OutputMetadata.status : status,
            },
            synchronize_session= False
        )

    def delete_scenario(self, session, data):

        """ Deletes the scenario along with associated labels """

        session.query(Scenarios).filter(and_(
            Scenarios.name == data['name'],
            Scenarios.author == data['author'],
            Scenarios.status == data['status']
            )).delete(synchronize_session= False)

        session.query(ScenarioLabels).filter(and_(
            ScenarioLabels.user == data['author'],
            ScenarioLabels.label == data['name']
        )).delete(synchronize_session= False)

    def delete_output_metadata(self, session, data):
        """ Delete output metadata """
        session.query(OutputMetadata).filter(and_(
            OutputMetadata.name == data['name'],
            OutputMetadata.author == data['author'],
            OutputMetadata.status == data['status']
            )).delete(synchronize_session= False)

    def check_reset_token(self, session, username, token):

        rtoken = session.query(UserResetToken).filter(UserResetToken.username == username).first()
        if rtoken:
            if bcrypt.checkpw(token.encode('utf-8'), rtoken.token) and not rtoken.token_used:
                session.query(UserResetToken).filter(UserResetToken.username == username).update({UserResetToken.token_used: True}, synchronize_session=False)
                return True
        return False

    def insert_user_signup_request(self, session, user_info):

        user_request = UserSignUpRequest()
        user_request.first_name = user_info['first_name']
        user_request.last_name = user_info['last_name']
        user_request.email = user_info['email']
        user_request.country = user_info['country']
        user_request.organization = user_info['org']
        user_request.description = user_info['description'].encode('utf-8')
        session.add(user_request)

    def is_admin(self, session, username):

        user = session.query(Users).filter(Users.username==username).first()
        if user and user.role == 'admin':
            return True
        return False

    def get_users_request(self, session):
        return session.query(UserSignUpRequest).all()

    def get_token_email_dict(self, session):

        user_request_tokens = session.query(UserSignupToken).all()
        token_dict = {}
        if user_request_tokens:
            for ur in user_request_tokens:
                token_dict[ur.email] = ur.token
        return token_dict
    
    def insert_signup_token(self, session, email, token):

        signup_token = UserSignupToken()
        signup_token.email = email
        signup_token.token = token
        session.add(signup_token)

    def update_signup_request_status(self, session, email, status):
        session.query(UserSignUpRequest).filter(UserSignUpRequest.email == email).update({UserSignUpRequest.request_status: status}, synchronize_session=False)

    def delete_user_signup_request(self, session, email):

        """ Delete the user signup request """
        session.query(UserSignupToken).filter(UserSignupToken.email == email).delete(synchronize_session=False)
        session.query(UserSignUpRequest).filter(UserSignUpRequest.email == email).delete(synchronize_session=False)
        
    def is_signup_token_valid(self, session, token):
        """ Check if the signup token if valid"""
        is_valid = False
        stoken = session.query(UserSignupToken).filter(UserSignupToken.token == token).first()
        if stoken and not stoken.token_used:
            is_valid = True
        return is_valid

    def invalidate_signup_token(self, session, token):
        session.query(UserSignupToken).filter(UserSignupToken.token == token).update({UserSignupToken.token_used: True},synchronize_session=False)
    
    def delete_signup_token(self, session, email):

        """ Delete the user signup token """
        session.query(UserSignupToken).filter(UserSignupToken.email == email).delete(synchronize_session=False)

    def get_email_from_username(self, session, username):
        """ Get email for given user """

        usr = session.query(Users).filter(Users.username == username).first()
        return usr.email if usr else None

    def insert_simulation_queue(self, session, input, uuid, username):
        """ Insert simulation queue in database """

        sq = SimulationQueue()
        sq.input = json.dumps(input).encode('utf-8')
        sq.uuid = uuid
        sq.username = username
        sq.created_date = datetime.datetime.now()

        session.add(sq)

    def delete_simulation_queue(self, session, username, uuid):

        """ Delete the simulation from queue"""
        session.query(SimulationQueue).filter( and_(
            SimulationQueue.username == username,
            SimulationQueue.uuid == uuid
        )).delete(synchronize_session=False)

    def get_sim_queue(self, session):

        return session.query(SimulationQueue).order_by(SimulationQueue.created_date).all()

    def add_default_limits(self, session, username):

        for service, limit_dict in DEFAULT_RATES_FOR_ALL_USERS.items():
            rule = Rules()
            rule.client_key = username
            rule.service_name = service
            rule.max_token = limit_dict['max_token']
            rule.allowed_requests_per_minute = limit_dict['rate_pm']
            session.add(rule)
        
