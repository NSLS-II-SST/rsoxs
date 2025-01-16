import os
from nbs_bl.printing import run_report
from ..Functions.slack import RSoXSBot


run_report(__file__)
slack_token = os.environ.get("SLACK_API_TOKEN", None)
rsoxs_bot = RSoXSBot(token=slack_token, proxy=None, channel="#instrument-status")
