
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
    send_email,
    upload_to_google_drive,
)

openai.api_key = st.secrets["API_KEY"]

# Set page title and icon
st.set_page_config(page_title="IT Analyst Interview", page_icon=config.AVATAR_INTERVIEWER)

import streamlit as st

# Check if usernames and logins are enabled
if config.LOGINS:
    pwd_correct, username = check_password()
    if not pwd_correct:
        st.stop()
    else:
        st.session_state.username = username
else:
    st.session_state.username = "testaccount"

# Initialize directories
os.makedirs(config.TRANSCRIPTS_DIRECTORY, exist_ok=True)
os.makedirs(config.TIMES_DIRECTORY, exist_ok=True)
os.makedirs(config.BACKUPS_DIRECTORY, exist_ok=True)

# Get google drive folder
drive_folder_id = st.secrets.get("google_drive", {}).get("folder_id")

# Initialize session state
if "interview_active" not in st.session_state:
    st.session_state.interview_active = True

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": config.SYSTEM_PROMPT}]

    response = openai.ChatCompletion.create(
        model=config.MODEL,
        messages=st.session_state.messages,
        max_tokens=config.MAX_OUTPUT_TOKENS or 1024,
        temperature=config.TEMPERATURE or 0.7,
    )
    first_message = response["choices"][0]["message"]["content"]
    st.session_state.messages.append({"role": "assistant", "content": first_message})

if "start_time" not in st.session_state:
    st.session_state.start_time = time.time()
    st.session_state.start_time_file_names = time.strftime(
        "%Y-%m-%d_%H-%M_%S", time.localtime(st.session_state.start_time)
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

abort_interview_message = ""

# Add 'Quit' button to dashboard
col1, col2 = st.columns([0.85, 0.15])
# Place where the second column is
with col2:

    # If interview is active and 'Quit' button is clicked
    if st.session_state.interview_active and st.button(
        "Quit", help="End the interview early."
    ):
        abort_interview_message = "End the interview"

# Main chat if interview is active
if st.session_state.interview_active:

    if abort_interview_message:
        message_respondent = abort_interview_message
        st.session_state.interview_active = False
    else:
        message_respondent = st.chat_input("Your thoughtful response here")

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

            # signal from the assistant that the interview should end
            if "x7y8" in message_interviewer:
                logging.debug(f"End interview signal received")

                message_interviewer = message_interviewer.replace("x7y8", "").strip()
                st.session_state.interview_active = False 

                # Send the final interviewer message via email
                send_email(message_body=message_interviewer)


            message_placeholder.markdown(message_interviewer)
            st.session_state.messages.append({"role": "assistant", "content": message_interviewer})

            try:
                save_interview_data(
                    username=st.session_state.username,
                    transcripts_directory=config.BACKUPS_DIRECTORY,
                    times_directory=config.BACKUPS_DIRECTORY,
                    file_name_addition_transcript=f"_transcript_{st.session_state.start_time_file_names}",
                    file_name_addition_time=f"_time_{st.session_state.start_time_file_names}",
                    google_drive_folder_id=drive_folder_id
                )
            except Exception as e:
                st.error(f"Error saving progress: {e}")
