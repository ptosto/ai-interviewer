from google_auth_oauthlib.flow import InstalledAppFlow
flow = InstalledAppFlow.from_client_config(oauth_info, scopes=["https://www.googleapis.com/auth/gmail.send"])
credentials = flow.run_local_server(port=0)


from utils import send_email
send_email("Test email body for debugging")
