# Copyright (c) 2022, Alliance for Sustainable Energy, LLC
# and others ReEDS India developers


""" Need to populate the scenarios table with default scenarios that will
be availabe to all users when they sign up"""


# standard imports
import os
import shutil
import datetime
from pathlib import Path

# third-party imports
import pandas as pd
import bcrypt
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from dotenv import load_dotenv

# internal imports
from mapper import SCEN_DESCRIPTION
from create_db import Scenarios, Users, Base


load_dotenv()


class PopulateDefaultScenario:
    def __init__(self, conn_string, case_csv_file):

        case_df = pd.read_csv(case_csv_file)
        base_cases = list(case_df.columns)[2:]
        csv_created_date = datetime.datetime.utcnow()

        # Create folder if already does not exist
        folders_to_create = ["users_avatar", "users_cases", "users_output"]
        for folder in folders_to_create:
            folder_path = Path(__file__).parents[0] / ".." / folder
            Path.mkdir(folder_path, exist_ok=True)

        engine = create_engine(conn_string)
        Base.metadata.bind = engine
        db_session = sessionmaker(bind=engine)

        session = db_session()

        # Got to create a dummy use for default scenarios
        default_scenario_user = "NREL (ReEDS India)"  # Donot change this
        user = Users()
        user.username = default_scenario_user
        default_scenario_password = "does not work!"
        user.password = bcrypt.hashpw(
            default_scenario_password.encode("utf-8"), bcrypt.gensalt()
        )
        user.email = "dummy.nrel@nrel.gov"
        session.add(user)
        session.commit()

        for case in base_cases:

            scenario = Scenarios()
            scenario.name = case
            scenario.author = default_scenario_user
            scenario.created = csv_created_date
            scenario.status = "Ready to test!"
            scenario.description = (
                SCEN_DESCRIPTION[case]
                if case in SCEN_DESCRIPTION
                else f"Runs a {case} scenario"
            )
            scenario.scen_type = "base"

            session.add(scenario)
        session.commit()

        user = Users()
        user.username = os.getenv("REEDS_SUPERUSER")
        user.password = bcrypt.hashpw(
            os.getenv("REEDS_SUPERUSER_PASSWORD").encode("utf-8"),
            bcrypt.gensalt(),
        )
        user.email = os.getenv("REEDS_SUPERUSER_EMAIL")
        user.role = "admin"
        user.organization = "NREL"
        user.country = "USA"
        session.add(user)
        session.commit()

        # create a folder for user if already does not exist
        case_base_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "users_cases",
            os.getenv("REEDS_SUPERUSER"),
        )

        if not os.path.exists(case_base_path):
            os.mkdir(case_base_path)

        # Copy the base case.csv file if one already does not exist
        case_file_path = os.path.join(case_base_path, "cases.csv")
        if not os.path.exists(case_file_path):
            default_case_csv_path = os.path.join(
                os.path.dirname(__file__), "..", "..", "A_Inputs", "cases.csv"
            )
            shutil.copy(default_case_csv_path, case_file_path)

        # create a output folder for user if already does not exist
        output_base_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "users_output",
            os.getenv("REEDS_SUPERUSER"),
        )

        if not os.path.exists(output_base_path):
            os.mkdir(output_base_path)

        # Let's create the super user
        session.close()


if __name__ == "__main__":

    # sqlite_engine = "sqlite:///test.db"
    # postgres_engine = "postgresql://postgres:kapil@localhost:5001/reeds"
    # mysql_engine = "mysql://root:kapil@localhost:3306/reeds"

    db_connection_string = "mysql://root:password@localhost:3306/reeds"

    PopulateDefaultScenario(
        db_connection_string,
        os.path.join(
            os.path.dirname(__file__), "..", "..", "A_Inputs", "cases.csv"
        ),
    )
