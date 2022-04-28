
""" Need to populate the scenarios table with default scenarios that will
be availabe to all users when they sign up"""


import pandas as pd
import datetime
from mapper import SCEN_DESCRIPTION
from sqlalchemy.orm import sessionmaker
from create_db import Scenarios, Users, Base
from sqlalchemy import create_engine
import os
import bcrypt

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..','..', '.env'))

class PopulateDefaultScenario:

    def __init__(self, conn_string, case_csv_file):

        case_df = pd.read_csv(case_csv_file)
        base_cases = list(case_df.columns)[2:]
        csv_created_date = datetime.datetime.utcnow()

        engine = create_engine(conn_string)
        Base.metadata.bind = engine 
        db_session = sessionmaker(bind=engine)

        session = db_session()

        #Got to create a dummy use for default scenarios
        default_scenario_user = "NREL (ReEDS India)" # Donot change this
        user = Users()
        user.username = default_scenario_user
        default_scenario_password = 'does not work!'
        user.password = bcrypt.hashpw(default_scenario_password.encode('utf-8'), bcrypt.gensalt())
        user.email = 'dummy.nrel@nrel.gov'
        session.add(user)
        session.commit()
        
        for case in base_cases:
            
            scenario = Scenarios()
            scenario.name = case
            scenario.author = default_scenario_user
            scenario.created = csv_created_date
            scenario.status = 'Ready to test!'
            scenario.description = SCEN_DESCRIPTION[case] if case in SCEN_DESCRIPTION else f"Runs a {case} scenario"
            scenario.scen_type = 'base'

            session.add(scenario)
        session.commit()

        user = Users()
        user.username = os.getenv('REEDS_SUPERUSER')
        user.password = bcrypt.hashpw(os.getenv('REEDS_SUPERUSER_PASSWORD').encode('utf-8'), bcrypt.gensalt())
        user.email = os.getenv('REEDS_SUPERUSER_EMAIL')
        user.role = 'admin'
        user.organization = 'NREL'
        user.country = 'USA'
        session.add(user)
        session.commit()

        # Let's create the super user
        session.close()


if __name__ == '__main__':
    
    sqlite_engine = 'sqlite:///test.db'
    postgres_engine = 'postgresql://postgres:kapil@localhost:5001/reeds'
    mysql_engine = 'mysql://root:kapil@localhost:3306/reeds'
    mysql_engine = 'mysql://admin:reedsindia@reeds-database.cqpo6huywjus.us-west-1.rds.amazonaws.com:3306/reeds'
    PopulateDefaultScenario(
        mysql_engine,
        os.path.join(os.path.dirname(__file__), '..', '..', 'A_Inputs', 'cases.csv')
    )



