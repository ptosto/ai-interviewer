import streamlit as st
import time
import os
import config
import openai
import logging

from utils import (
    check_password,
    check_if_interview_completed,
    save_interview_data,
    upload_to_google_drive,
    save_session_to_file,
    load_session_from_file,
)

# Fetch Google Drive folder ID early to ensure it's available
google_drive_folder_id = None
try:
    google_drive_folder_id = st.secrets.get("google_drive", {}).get("folder_id")
    logging.debug(f"Google Drive folder ID fetched: {google_drive_folder_id}")
except Exception as e:
    logging.error(f"Error fetching Google Drive folder ID: {e}")

# Initialize session state variables
if "interview_active" not in st.session_state:
    st.session_state.interview_active = True  # Default to active if not set

if "messages" not in st.session_state:
    st.session_state.messages = []  # Initialize messages as an empty list

if "start_time" not in st.session_state:
    st.session_state.start_time = time.time()
    st.session_state.start_time_file_names = time.strftime(
        "%Y_%m_%d_%H_%M_%S", time.localtime(st.session_state.start_time)
    )
# Set page title and icon
st.set_page_config(page_title="Interview", page_icon=config.AVATAR_INTERVIEWER)

# Check if usernames and logins are enabled
if config.LOGINS:
    pwd_correct, username = check_password()
    if not pwd_correct:
        st.stop()
    else:
        st.session_state.username = username
else:
    st.session_state.username = "testaccount"

# Ensure 'messages' is initialized in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# If no messages exist, trigger the assistant's first message
if not st.session_state.messages:
    try:
        # Generate the first assistant message using the system prompt
        response = openai.ChatCompletion.create(
            model=config.MODEL,
            messages=[{"role": "system", "content": config.SYSTEM_PROMPT}],
            max_tokens=config.MAX_OUTPUT_TOKENS or 1024,
            temperature=config.TEMPERATURE or 0.7,
        )
        first_message = response["choices"][0]["message"]["content"]
        st.session_state.messages.append({"role": "assistant", "content": first_message})

        # Display the assistant's first message
        with st.chat_message("assistant", avatar=config.AVATAR_INTERVIEWER):
            st.markdown(first_message)
    except Exception as e:
        st.error(f"Error generating the first message: {e}")
        st.session_state.messages.append({"role": "assistant", "content": "I'm ready to begin the interview."})
        with st.chat_message("assistant", avatar=config.AVATAR_INTERVIEWER):
            st.markdown("I'm ready to begin the interview.")

# Display all messages in the chat
for message in st.session_state.messages:
    avatar = config.AVATAR_INTERVIEWER if message["role"] == "assistant" else config.AVATAR_RESPONDENT
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# Initialize session state and load any existing session data
if "messages" not in st.session_state:
    if not load_session_from_file(st.session_state.username, config.BACKUPS_DIRECTORY):
        # Initialize new session if no saved data is found
        st.session_state.messages = [{"role": "system", "content": config.SYSTEM_PROMPT}]
    else:
        st.session_state.interview_active = True
        logging.debug("Session resumed from previous state.")

if "start_time" not in st.session_state:
    st.session_state.start_time = time.time()
    st.session_state.start_time_file_names = time.strftime(
        "%Y_%m_%d_%H_%M_%S", time.localtime(st.session_state.start_time)
    )

# Check if interview previously completed
interview_previously_completed = check_if_interview_completed(
    config.TIMES_DIRECTORY, st.session_state.username
)

if interview_previously_completed and not st.session_state.messages:
    st.session_state.interview_active = False
    st.markdown("Interview already completed.")

# Display all messages in chat
for message in st.session_state.messages[1:]:
    avatar = config.AVATAR_INTERVIEWER if message["role"] == "assistant" else config.AVATAR_RESPONDENT
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# Add 'Quit' button to dashboard
col1, col2 = st.columns([0.85, 0.15])
with col2:
    if st.session_state.interview_active and st.button("Quit", help="End the interview."):
        st.session_state.interview_active = False
        quit_message = "You have cancelled the interview."
        st.session_state.messages.append({"role": "assistant", "content": quit_message})

        try:
            # Save the final session data
            save_session_to_file(
                username=st.session_state.username,
                directory=config.BACKUPS_DIRECTORY,
                google_drive_folder_id=google_drive_folder_id,
            )
        except Exception as e:
            logging.error(f"Error during save/upload: {e}")
            st.error(f"Error saving/uploading data: {e}")

# Main chat if interview is active
if st.session_state.interview_active:
    message_respondent = st.chat_input("Your thoughts here")

    if message_respondent:
        st.session_state.messages.append({"role": "user", "content": message_respondent})

        with st.chat_message("user", avatar=config.AVATAR_RESPONDENT):
            st.markdown(message_respondent)

        with st.chat_message("assistant", avatar=config.AVATAR_INTERVIEWER):
            message_placeholder = st.empty()
            message_interviewer = ""

            try:
                response = openai.ChatCompletion.create(
                    model=config.MODEL,
                    messages=st.session_state.messages,
                    max_tokens=config.MAX_OUTPUT_TOKENS or 1024,
                    temperature=config.TEMPERATURE or 0.7,
                    stream=True,
                )
                for chunk in response:
                    text_delta = chunk.choices[0].delta.get("content", "")
                    if text_delta:
                        message_interviewer += text_delta
                        message_placeholder.markdown(message_interviewer + "▌")
            except Exception as e:
                st.error(f"Error during API call: {e}")

            message_placeholder.markdown(message_interviewer)
            st.session_state.messages.append({"role": "assistant", "content": message_interviewer})

            # Save session data after each interaction
            try:
                save_session_to_file(
                    username=st.session_state.username,
                    directory=config.BACKUPS_DIRECTORY,
                    google_drive_folder_id=google_drive_folder_id,
                )
            except Exception as e:
                logging.error(f"Error saving session: {e}")
                st.error(f"Error saving progress: {e}")
