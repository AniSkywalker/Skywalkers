from slack_sdk import WebClient


class SlackClient:
    def __init__(self, auth):
        self.client = WebClient(token=auth)
        print("Communication established!!!")

    def read_message(self, channel, return_latest=True, limit=100):
        message = None
        try:
            messages = self.client.conversations_history(channel=channel, limit=limit)["messages"]
            if return_latest:
                message = messages[0]
            else:
                message = messages
        except Exception as e:
            print(e)
        return message
