from slack import WebClient
from sst.CommonFunctions.functions import run_report


run_report(__file__)


class RSoXSBot:
    # The constructor for the class. It takes the channel name as the a
    # parameter and then sets it as an instance variable
    def __init__(self, token, proxy, channel):
        self.channel = channel
        self.webclient = WebClient(token=token, proxy=proxy)

    # Craft and return the entire message payload as a dictionary.
    def send_message(self, message):
        composed_message = {
            "channel": self.channel,
            "blocks": [
                {"type": "section", "text": {"type": "mrkdwn", "text": message}},
            ],
        }
        try:
            self.webclient.chat_postMessage(**composed_message)
        except Exception:
            pass
