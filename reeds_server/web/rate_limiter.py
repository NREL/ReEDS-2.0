"""
All features to implement Rate limiter
"""

import threading
import schedule
import time
import redis
import sqlalchemy
from web.create_db import Rules
import time
import os
import json
from web.constants import REL_URL_TO_SERVICE_DICT, OPEN_ROUTES


# if os.getenv("DEPLOY_MODE") != "local":
#     REDIS_DB = redis.Redis(
#         host=os.getenv("REDIS_HOST"),
#         port=int(os.getenv("REDIS_PORT")),
#         # password=os.getenv("REDIS_PASSWORD"),
#         charset="utf-8",
#         decode_responses=True,
#         ssl=False,
#     )
# else:
#     REDIS_DB = redis.Redis(
#         host=os.getenv("REDIS_HOST"),
#         port=int(os.getenv("REDIS_PORT")),
#         charset="utf-8",
#         decode_responses=True,
#     )

REDIS_DB = None

CLIENT_BUCKET_STORE = {}

# Implementing rules retriever
# Background process that retrieves rules from database every given seconds


def run_continuously(interval=1):

    cease_continous_run = threading.Event()

    class ScheduleThread(threading.Thread):
        @classmethod
        def run(cls):
            while not cease_continous_run.is_set():
                schedule.run_pending()
                time.sleep(interval)

    continuous_thread = ScheduleThread()
    continuous_thread.start()
    return cease_continous_run


def rule_retriever(sqlalchemy_session):

    # Let's retrieve rules from database and cache it
    # create a session
    session = sqlalchemy_session()

    try:
        rules = session.query(Rules).all()
        all_rules = {}
        print(rules)
        for rule in rules:
            if rule.client_key not in all_rules:
                all_rules[rule.client_key] = {}
            all_rules[rule.client_key][rule.service_name] = {
                "max_token": float(rule.max_token),
                "rate_pm": float(rule.allowed_requests_per_minute),
            }

        # Let's write these rules in redis cache
        for key, val in all_rules.items():
            print(key, val)
            REDIS_DB.set(key, json.dumps(val))

    except sqlalchemy.exc.NoResultFound as e:
        pass


def get_client_identifier(request):

    try:
        return (request["userData"]["username"], "user")
    except Exception as e:
        return (request.remote, "non-user")


def check_for_throttle(request):

    # Get client key
    client_key, client_type = get_client_identifier(request)
    rel_url = request.rel_url
    service_name = REL_URL_TO_SERVICE_DICT.get(str(rel_url), None)

    # Get the rate limit data from cache

    if client_type == "user":
        client_limits = json.loads(REDIS_DB.get(client_key))
    else:
        client_limits = OPEN_ROUTES

    try:

        if isinstance(client_limits, dict) and service_name in client_limits:

            # Implement token bucket algorithm
            if client_key not in CLIENT_BUCKET_STORE:
                CLIENT_BUCKET_STORE[client_key] = TokenBucketAlgorithm(
                    float(client_limits[service_name]["max_token"]),
                    float(client_limits[service_name]["rate_pm"]) / 60,
                )

            else:
                # Check if token size has changed
                if (
                    CLIENT_BUCKET_STORE[client_key].max_token_size
                    != client_limits[service_name]["max_token"]
                ):
                    CLIENT_BUCKET_STORE[
                        client_key
                    ].max_token_size = client_limits[service_name]["max_token"]
                    CLIENT_BUCKET_STORE[client_key].refill_rate = (
                        client_limits[service_name]["rate_pm"] / 60
                    )

            # Now let's check whether to allow request or not
            return CLIENT_BUCKET_STORE[client_key].throttle_request(1)
    except Exception as e:
        import traceback

        print(traceback.print_exc())
        raise Exception(e)

    return True


class TokenBucketAlgorithm:
    def __init__(self, max_token_size: int, refill_rate: float):

        self.max_token_size = max_token_size
        self.refill_rate = refill_rate
        self.current_bucket_size = max_token_size
        self.last_refill_time = time.time()

    def throttle_request(self, tokens):

        self.refill()

        if self.current_bucket_size > tokens:
            self.current_bucket_size -= tokens

            return False
        else:
            return True

    def refill(self):

        now = time.time()
        tokens_to_add = (now - self.last_refill_time) * self.refill_rate
        self.current_bucket_size = min(
            self.current_bucket_size + tokens_to_add, self.max_token_size
        )
        self.last_refill_time = now
