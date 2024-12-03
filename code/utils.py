import streamlit as st
import hmac
import time
import os


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

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os

import logging
logging.basicConfig(level=logging.DEBUG)

import json  # Add this at the top of the file if not already imported

def upload_to_google_drive(file_path, folder_id):
    try:
        logging.debug(f"Attempting to upload {file_path} to folder {folder_id}")
        
        # Parse the JSON string into a dictionary
        service_account_info = json.loads(st.secrets["google_drive"]["service_account_file"])
        
        credentials = Credentials.from_service_account_info(service_account_info)
        drive_service = build("drive", "v3", credentials=credentials)

        file_metadata = {
            "name": os.path.basename(file_path),
            "parents": [folder_id],
        }
        logging.debug(f"File metadata: {file_metadata}")

        media = MediaFileUpload(file_path, mimetype="text/plain")
        uploaded_file = drive_service.files().create(
            body=file_metadata, media_body=media
        ).execute()

        logging.info(f"Uploaded file ID: {uploaded_file.get('id')}")
        return uploaded_file.get("id")
    except Exception as e:
        logging.error(f"Upload error: {e}")
        st.error(f"Upload error: {e}")
        return None



def save_interview_data(
    username,
    transcripts_directory,
    times_directory,
    file_name_addition_transcript="",
    file_name_addition_time="",
    google_drive_folder_id=None,
):
    """Write interview data (transcript and time) to disk and upload to Google Drive."""
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



def og_save_interview_data(
    username,
    transcripts_directory,
    times_directory,
    file_name_addition_transcript="",
    file_name_addition_time="",
):
    """Write interview data (transcript and time) to disk."""

    # Store chat transcript
    with open(
        os.path.join(
            transcripts_directory, f"{username}{file_name_addition_transcript}.txt"
        ),
        "w",
    ) as t:
        for message in st.session_state.messages:
            t.write(f"{message['role']}: {message['content']}\n")

    # Store file with start time and duration of interview
    with open(
        os.path.join(times_directory, f"{username}{file_name_addition_time}.txt"),
        "w",
    ) as d:
        duration = (time.time() - st.session_state.start_time) / 60
        d.write(
            f"Start time (UTC): {time.strftime('%d/%m/%Y %H:%M:%S', time.localtime(st.session_state.start_time))}\nInterview duration (minutes): {duration:.2f}"
        )
