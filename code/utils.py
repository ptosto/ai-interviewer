import streamlit as st
import hmac
import time
import os
import json
import config
import logging
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


logging.basicConfig(level=logging.DEBUG)

def save_session_to_file(username, directory, google_drive_folder_id=None):
    """Save session messages to a JSON file and optionally upload to Google Drive."""
    session_file = os.path.join(directory, f"{username}_session.json")
    try:
        with open(session_file, "w") as f:
            json.dump(st.session_state.messages, f)
        logging.debug(f"Session saved to {session_file}")

        # Upload to Google Drive if folder ID is provided
        if google_drive_folder_id:
            upload_to_google_drive(session_file, google_drive_folder_id)
    except Exception as e:
        logging.error(f"Error saving session to file: {e}")
        st.error(f"Error saving session: {e}")

def load_session_from_file(username, directory):
    """Load session messages from a JSON file."""
    session_file = os.path.join(directory, f"{username}_session.json")
    try:
        if os.path.exists(session_file):
            with open(session_file, "r") as f:
                st.session_state.messages = json.load(f)
            logging.debug(f"Session loaded from {session_file}")
            return True
    except Exception as e:
        logging.error(f"Error loading session from file: {e}")
    return False


# Password screen for dashboard (note: only very basic authentication!)
# Based on https://docs.streamlit.io/knowledge-base/deploy/authentication-without-sso
def check_password():
    """Returns 'True' if the user has entered a correct password."""

    def login_form():
        """Form with widgets to collect user information"""
        with st.form("Credentials"):
            st.text_input("Username", key="username")
            st.text_input("Password", type="password", key="password")
            st.form_submit_button("Log in", on_click=password_entered)

    def password_entered():
        """Checks whether username and password entered by the user are correct."""
        if st.session_state.username in st.secrets.passwords and hmac.compare_digest(
            st.session_state.password,
            st.secrets.passwords[st.session_state.username],
        ):
            st.session_state.password_correct = True

        else:
            st.session_state.password_correct = False

        del st.session_state.password  # don't store password in session state

    # Return True, username if password was already entered correctly before
    if st.session_state.get("password_correct", False):
        return True, st.session_state.username

    # Otherwise show login screen
    login_form()
    if "password_correct" in st.session_state:
        st.error("User or password incorrect")
    return False, st.session_state.username


def check_if_interview_completed(directory, username):
    """Check if interview transcript/time file exists which signals that interview was completed."""

    # Test account has multiple interview attempts
    if username != "testaccount":

        # Check if file exists
        try:
            with open(os.path.join(directory, f"{username}.txt"), "r") as _:
                return True

        except FileNotFoundError:
            return False

    else:

        return False

def save_interview_data(
    username,
    transcripts_directory,
    times_directory,
    file_name_addition_transcript="",
    file_name_addition_time="",
    google_drive_folder_id=None,
):
    """Write interview data (transcript and time) to disk
       Then upload the saved files to Google Drive."""
    # Local paths for temporary saving
    transcript_path = os.path.join(
        transcripts_directory, f"{username}{file_name_addition_transcript}.txt"
    )
    time_path = os.path.join(
        times_directory, f"{username}{file_name_addition_time}.txt"
    )

    # Store chat transcript locally
    with open(transcript_path, "w") as t:
        for message in st.session_state.messages:
            t.write(f"{message['role']}: {message['content']}\n")

    # Store file with start time and duration of interview
    with open(time_path, "w") as d:
        duration = (time.time() - st.session_state.start_time) / 60
        d.write(
            f"Start time (UTC): {time.strftime('%d/%m/%Y %H:%M:%S', time.localtime(st.session_state.start_time))}\nInterview duration (minutes): {duration:.2f}"
        )

    # Upload files to Google Drive if folder ID is provided
    if google_drive_folder_id:
        upload_to_google_drive(transcript_path, google_drive_folder_id)
        upload_to_google_drive(time_path, google_drive_folder_id)

    # Cleanup local files after uploading
    #os.remove(transcript_path)
    #os.remove(time_path)

def upload_to_google_drive(file_path, folder_id):
    """Upload a file to Google Drive, overwriting if the file already exists."""
    try:
        # Parse the service account credentials
        service_account_info = json.loads(st.secrets["google_drive"]["service_account_file"])
        credentials = Credentials.from_service_account_info(service_account_info)
        drive_service = build("drive", "v3", credentials=credentials)

        # Extract file name
        file_name = os.path.basename(file_path)

        # Check if the file already exists in the folder
        query = f"'{folder_id}' in parents and name = '{file_name}' and trashed = false"
        response = drive_service.files().list(q=query, spaces='drive').execute()
        files = response.get('files', [])

        if files:
            # File exists, update it
            file_id = files[0]['id']
            media = MediaFileUpload(file_path, mimetype="application/json")
            drive_service.files().update(fileId=file_id, media_body=media).execute()
            logging.info(f"Updated file {file_name} in Google Drive folder {folder_id}")
        else:
            # File doesn't exist, create a new one
            file_metadata = {
                "name": file_name,
                "parents": [folder_id],
            }
            media = MediaFileUpload(file_path, mimetype="application/json")
            drive_service.files().create(body=file_metadata, media_body=media).execute()
            logging.info(f"Uploaded new file {file_name} to Google Drive folder {folder_id}")
    except HttpError as e:
        logging.error(f"An error occurred while uploading to Google Drive: {e}")
    except Exception as e:
        logging.error(f"Unexpected error during Google Drive upload: {e}")


def send_email(message_body):
    message = Mail(
        from_email=config.SENDER_EMAIL,
        to_emails=config.SEND_TO,
        subject=config.SEND_SUBJECT.format(username=st.session_state.username),
        plain_text_content=message_body
    )
    try:
        logging.debug(f"Fixing to send: {message}")
        sg = SendGridAPIClient(st.secrets["sendgrid"]["twilio_pw"])
        response = sg.send(message)
        logging.debug(f"Email sent: {response.status_code}")
    except Exception as e:
        logging.debug(f"Error: {e}")

