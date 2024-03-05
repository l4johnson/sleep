#!/usr/bin/env python3
"""
pip3 install garth requests readchar

export EMAIL=<your garmin email>
export PASSWORD=<your garmin password>

"""
import datetime
import pytz
import json
import logging
import os
import sys
from getpass import getpass

import readchar
import requests
from garth.exc import GarthHTTPError

from garminconnect import (
    Garmin,
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)

# Configure debug logging
# logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables if defined
email = os.getenv("EMAIL")
password = os.getenv("PASSWORD")
tokenstore = os.getenv("GARMINTOKENS") or "~/.garminconnect"
tokenstore_base64 = os.getenv("GARMINTOKENS_BASE64") or "~/.garminconnect_base64"
api = None

# Example selections and settings
today = datetime.date.today()
startdate = today - datetime.timedelta(days=7)  # Select past week
yesterday = today - datetime.timedelta(days=2)
start = 0
limit = 100
start_badge = 1  # Badge related calls calls start counting at 1
activitytype = ""  # Possible values are: cycling, running, swimming, multi_sport, fitness_equipment, hiking, walking, other
activityfile = "MY_ACTIVITY.fit"  # Supported file types are: .fit .gpx .tcx
weight = 89.6
weightunit = 'kg'

def get_credentials():
    """Get user credentials."""

    email = input("Login e-mail: ")
    password = getpass("Enter password: ")

    return email, password


def init_api(email, password):
    """Initialize Garmin API with your credentials."""

    try:
        # Using Oauth1 and OAuth2 token files from directory
        print(
            f"Trying to login to Garmin Connect using token data from directory '{tokenstore}'...\n"
        )

        # Using Oauth1 and Oauth2 tokens from base64 encoded string
        # print(
        #     f"Trying to login to Garmin Connect using token data from file '{tokenstore_base64}'...\n"
        # )
        # dir_path = os.path.expanduser(tokenstore_base64)
        # with open(dir_path, "r") as token_file:
        #     tokenstore = token_file.read()

        garmin = Garmin()
        garmin.login(tokenstore)

    except (FileNotFoundError, GarthHTTPError, GarminConnectAuthenticationError):
        # Session is expired. You'll need to log in again
        print(
            "Login tokens not present, login with your Garmin Connect credentials to generate them.\n"
            f"They will be stored in '{tokenstore}' for future use.\n"
        )
        try:
            # Ask for credentials if not set as environment variables
            if not email or not password:
                email, password = get_credentials()

            garmin = Garmin(email, password)
            garmin.login()
            # Save Oauth1 and Oauth2 token files to directory for next login
            garmin.garth.dump(tokenstore)
            print(
                f"Oauth tokens stored in '{tokenstore}' directory for future use. (first method)\n"
            )
            # Encode Oauth1 and Oauth2 tokens to base64 string and safe to file for next login (alternative way)
            token_base64 = garmin.garth.dumps()
            dir_path = os.path.expanduser(tokenstore_base64)
            with open(dir_path, "w") as token_file:
                token_file.write(token_base64)
            print(
                f"Oauth tokens encoded as base64 string and saved to '{dir_path}' file for future use. (second method)\n"
            )
        except (FileNotFoundError, GarthHTTPError, GarminConnectAuthenticationError, requests.exceptions.HTTPError) as err:
            logger.error(err)
            return None

    return garmin

def sumDay(dataList, value):
    total = 0
    for item in dataList:
        total = total + item[value]
    return total

def convert_gmt_timestamp_to_local(gmt_timestamp, local_timezone='America/Los_Angeles'):
    # Convert milliseconds to seconds
    timestamp_seconds = gmt_timestamp / 1000

    # Create a timezone-aware UTC datetime object
    utc_datetime = datetime.datetime.fromtimestamp(timestamp_seconds, tz=datetime.timezone.utc)

    # Convert to local time (Pacific Time)
    local_timezone_obj = pytz.timezone(local_timezone)
    local_datetime = utc_datetime.astimezone(local_timezone_obj)

    return local_datetime.replace(tzinfo=None)

api = init_api(email, password)
stats = api.get_stats(today.isoformat())
print(f"Stats: {stats}")
print(f"totalKilocalories: {stats['totalKilocalories']}")

stepsData = api.get_steps_data(today.isoformat())
steps = sumDay(stepsData, 'steps')
print(f"Steps: {steps}")
print(f"Steps data type: {type(stepsData)}")

## gathering all sleep data
sleepData = api.get_sleep_data(today)
sleepSummary = sleepData['dailySleepDTO']
print(f"Sleep Summary: {sleepSummary}")

sleepWindowConfirmed = sleepData['dailySleepDTO']['sleepWindowConfirmed']
print(f"SleepWindowConfirmed: {sleepWindowConfirmed}")

if sleepWindowConfirmed == True: 
    sleepTimeHours = sleepSummary['sleepTimeSeconds'] / 3600
    print(f"Time asleep: {sleepTimeHours:.2f} hours")
    sleepStartTime = sleepSummary['sleepStartTimestampGMT']
    sleepStartTime = convert_gmt_timestamp_to_local(sleepStartTime)
    print(f"Sleep start time: {sleepStartTime}")
    sleepEndTime = sleepSummary['sleepEndTimestampGMT']
    sleepEndTime = convert_gmt_timestamp_to_local(sleepEndTime)
    print(f"Sleep end time: {sleepEndTime}")
    sleepScore = sleepSummary['sleepScores']['overall']['value']
    print(f"Sleepscore: {sleepScore}")