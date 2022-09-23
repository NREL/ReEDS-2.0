""" Need to run this script to make sure all the tables are created !"""

from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    String,
    DateTime,
    LargeBinary,
    Boolean,
    Float,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from sqlalchemy import UniqueConstraint
import datetime
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.types import BINARY


@compiles(BINARY, "sqlite")
def compile_binary_sqlite(type_, compiler, **kw):
    return "BLOB"


Base = declarative_base()


class Rules(Base):

    __tablename__ = "rules"
    id = Column("id", Integer, autoincrement=True, primary_key=True)
    client_key = Column("client_key", String(200), nullable=False)
    service_name = Column("service_name", String(200), nullable=False)
    max_token = Column("max_token", Float(), nullable=False)
    allowed_requests_per_minute = Column(
        "allowed_requests_per_minute", Float(), nullable=False
    )


class SimulationQueue(Base):

    __tablename__ = "simulation_queue"
    id = Column("id", Integer, autoincrement=True, primary_key=True)
    input = Column("input", LargeBinary, nullable=False)
    created_date = Column(
        "created_date", DateTime(timezone=False), nullable=False
    )
    uuid = Column("uuid", String(150), nullable=False)
    username = Column("username", String(150), nullable=False)


class RequestMetric(Base):
    __tablename__ = "request_metric"
    id = Column("id", Integer, autoincrement=True, primary_key=True)
    req_name = Column("req_name", String(100), nullable=True)
    req_date = Column("req_date", DateTime(timezone=False), nullable=True)
    req_time = Column("req_time", Integer, nullable=True)


class UserSignupToken(Base):

    __tablename__ = "user_signup_token"
    email = Column(
        "email",
        String(100),
        ForeignKey("user_signup_request.email"),
        primary_key=True,
    )
    token = Column("token", String(100), nullable=False)
    token_used = Column("token_used", Boolean, default=False)
    token_created_date = Column(
        "token_created_date",
        DateTime(timezone=False),
        default=datetime.datetime.utcnow(),
    )


class UserSignUpRequest(Base):
    __tablename__ = "user_signup_request"

    first_name = Column("first_name", String(100), nullable=False)
    last_name = Column("last_name", String(100), nullable=False)
    email = Column(
        "email", String(100), nullable=False, unique=True, primary_key=True
    )
    country = Column("country", String(100), nullable=False)
    organization = Column("organization", String(100), nullable=False)
    description = Column("description", LargeBinary, nullable=False)
    requested_date = Column(
        "requested_date",
        DateTime(timezone=False),
        default=datetime.datetime.utcnow(),
    )
    request_status = Column("request_status", String(100), default="PENDING")

    signup_token = relationship(UserSignupToken, cascade="all, delete-orphan")


class UserResetToken(Base):

    __tablename__ = "user_reset_password_tokens"
    username = Column(
        "username",
        String(100),
        ForeignKey("users.username"),
        nullable=False,
        primary_key=True,
    )
    token = Column("token", LargeBinary, nullable=False)
    token_used = Column("token_used", Boolean, default=False)
    token_created_date = Column(
        "token_created_date",
        DateTime(timezone=False),
        default=datetime.datetime.utcnow(),
    )


class OutputMetadata(Base):

    __tablename__ = "output_metadata"
    __table_args__ = (UniqueConstraint("name", "author"), {})

    # Here we define columns for table output_metadata
    id = Column("id", Integer, autoincrement=True, primary_key=True)
    name = Column("name", String(100), nullable=False)
    author = Column(
        "author", String(100), ForeignKey("users.username"), nullable=False
    )
    created = Column(
        "created", DateTime(timezone=False), default=datetime.datetime.utcnow
    )
    status = Column("status", String(250), nullable=False)
    uuid = Column("uuid", String(250), nullable=False)
    size = Column("size", String(100))
    description = Column("description", String(250))


class Scenarios(Base):

    __tablename__ = "scenarios"
    __table_args__ = (UniqueConstraint("name", "author"), {})

    id = Column("id", Integer, autoincrement=True, primary_key=True)
    name = Column("name", String(100), nullable=False)
    author = Column(
        "author", String(100), ForeignKey("users.username"), nullable=False
    )
    created = Column(
        "created", DateTime(timezone=False), default=datetime.datetime.utcnow
    )
    status = Column("status", String(250), nullable=False)
    description = Column("description", String(250))
    scen_type = Column("scen_type", String(100), nullable=False)


class Bugs(Base):

    __tablename__ = "bugs"

    uuid = Column("uuid", String(100), primary_key=True)
    created = Column(
        "created", DateTime(timezone=False), default=datetime.datetime.utcnow
    )
    title = Column("title", String(100), nullable=False)
    body = Column("body", String(250), nullable=False)
    status = Column("status", String(100), nullable=False)


class ScenarioLabels(Base):

    __tablename__ = "scenario_labels"
    __table_args__ = (UniqueConstraint("user", "label", "scenario"), {})

    id = Column("id", Integer, autoincrement=True, primary_key=True)
    user = Column(
        "user", String(100), ForeignKey("users.username"), nullable=False
    )
    scenario = Column("scenario", String(100), nullable=False)
    label = Column("label", String(100), nullable=False)
    created = Column(
        "created", DateTime(timezone=False), default=datetime.datetime.utcnow
    )


class Labels(Base):

    __tablename__ = "labels"
    __table_args__ = (UniqueConstraint("user", "name"), {})

    id = Column("id", Integer, autoincrement=True, primary_key=True)
    user = Column(
        "user", String(100), ForeignKey("users.username"), nullable=False
    )
    created = Column(
        "created", DateTime(timezone=False), default=datetime.datetime.utcnow
    )
    name = Column("name", String(100), nullable=False)
    description = Column("description", String(250))
    is_enabled = Column("is_enabled", String(100), nullable=False)


class PersonnelScenarioState(Base):

    __tablename__ = "personnel_scenario_state"
    user = Column(
        "user", String(100), ForeignKey("users.username"), primary_key=True
    )
    personnel_scen_order = Column(
        "personnel_scen_order", LargeBinary, nullable=False
    )


class DefaultScenarioState(Base):
    __tablename__ = "default_scenario_state"
    user = Column(
        "user", String(100), ForeignKey("users.username"), primary_key=True
    )
    default_scen_order = Column(
        "default_scen_order", LargeBinary, nullable=False
    )


class OutputCardState(Base):
    __tablename__ = "output_card_state"
    user = Column(
        "user", String(100), ForeignKey("users.username"), primary_key=True
    )
    output_card_order = Column("output_card_order", LargeBinary, nullable=False)


class Users(Base):

    __tablename__ = "users"
    username = Column("username", String(100), nullable=False, primary_key=True)
    password = Column("password", String(250), nullable=False)
    email = Column("email", String(100), nullable=False, unique=True)
    country = Column("country", String(100))
    organization = Column("organization", String(100))
    image_name = Column("image_name", String(100))
    role = Column("role", String(100), default="regular")

    output_card_state = relationship(
        OutputCardState, cascade="all, delete-orphan"
    )
    default_scenario_state = relationship(
        DefaultScenarioState, cascade="all, delete-orphan"
    )
    personnel_scenario_state = relationship(
        PersonnelScenarioState, cascade="all, delete-orphan"
    )
    scenario_labels = relationship(ScenarioLabels, cascade="all, delete-orphan")
    labels = relationship(Labels, cascade="all, delete-orphan")
    scenarios = relationship(Scenarios, cascade="all, delete-orphan")
    output_metadata = relationship(OutputMetadata, cascade="all, delete-orphan")
    reset_token = relationship(UserResetToken, cascade="all, delete-orphan")


if __name__ == "__main__":

    # sqlite_engine = 'sqlite:///test.db'
    # postgres_engine = 'postgresql://postgres:kapil@localhost:5001/reeds'
    # mysql_engine = 'mysql://root:kapil@localhost:3306/reeds'

    # db_connection_string = "postgresql://reeds_india_prod:EHTZzQ+MMx88eVUDU@aurora-postgres-low-prod.cluster-ccklrxkcenui.us-west-2.rds.amazonaws.  com:5432/reeds_india_prod"
    # db_connection_string = "mysql://admin:reedsindia@reeds-database.cqpo6huywjus.us-west-1.rds.amazonaws.com:3306/reeds"

    engine = create_engine(db_connection_string, echo=True)
    Base.metadata.create_all(engine)
