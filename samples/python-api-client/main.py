import os

from careerpilot_sdk import CareerPilotClient

with CareerPilotClient(api_key=os.environ["CAREERPILOT_API_KEY"]) as client:
    print(client.status())

