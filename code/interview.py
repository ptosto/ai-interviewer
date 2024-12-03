import streamlit as st
import time
import os
import config
import openai  # Correct import
import logging

from utils import (
    check_password,
    check_if_interview_completed,
    save_interview_data,
)

# Set page title and icon
st.set_page_config(page_title="Interview", page_icon=config.AVATAR_INTERVIEWER)

# Set OpenAI API key
openai.api_key = st.secrets["API_KEY"]

# Initialize directories
os.makedirs(config.TRANSCRIPTS_DIRECTORY, exist_ok=True)
os.makedirs(config.TIMES_DIRECTORY, exist_ok=True)
os.makedirs(config.BACKUPS_DIRECTORY, exist_ok=True)

# Initialize session state
if "interview_active" not in st.session_state:
    st.session_state.interview_active = True

if "messages" not in st.session_state:
    # Initialize with a system message
    st.session_state.messages = [{"role": "system", "content": config.SYSTEM_PROMPT}]

if "start_time" not in st.session_state:
    st.session_state.start_time = time.time()

# Check if interview previously completed
if check_if_interview_completed(config.TIMES_DIRECTORY, st.session_state.get("username", "testaccount")):
    st.session_state.interview_active = False
    st.markdown("This interview has already been completed.")

# Display previous messages
for message in st.session_state.messages:
    avatar = config.AVATAR_INTERVIEWER if message["role"] == "assistant" else config.AVATAR_RESPONDENT
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# Quit button
if st.button("Quit"):
    logging.debug(f"Google Drive folder ID: {st.secrets['google_drive']['folder_id']}")
    st.session_state.interview_active = False
    save_interview_data(
        st.session_state.get("username", "testaccount"),
        config.TRANSCRIPTS_DIRECTORY,
        config.TIMES_DIRECTORY,
        google_drive_folder_id="1jBdHfHDHXW4rlsaXmZz6DBUTvJWjEFet",  # Confirm this matches the folder ID
    )
    st.stop()

# Main chat logic
if st.session_state.interview_active:
    user_input = st.chat_input("Your message here")
    if user_input:
        # Add user input to messages
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user", avatar=config.AVATAR_RESPONDENT):
            st.markdown(user_input)

        # Generate assistant response
        with st.chat_message("assistant", avatar=config.AVATAR_INTERVIEWER):
            placeholder = st.empty()
            assistant_message = ""

            try:
                # Get OpenAI response
                response = openai.ChatCompletion.create(
                    model=config.MODEL,
                    messages=st.session_state.messages,
                    max_tokens=config.MAX_OUTPUT_TOKENS,
                    temperature=config.TEMPERATURE if config.TEMPERATURE is not None else 1.0,
                    stream=True,
                )

                # Stream and display response
                for chunk in response:
                    delta = chunk["choices"][0]["delta"].get("content", "")
                    assistant_message += delta
                    placeholder.markdown(assistant_message + "▌")
                placeholder.markdown(assistant_message)  # Final response

                # Add assistant response to messages
                st.session_state.messages.append({"role": "assistant", "content": assistant_message})

                # Backup data
                save_interview_data(
                    st.session_state.get("username", "testaccount"),
                    config.TRANSCRIPTS_DIRECTORY,
                    config.TIMES_DIRECTORY,
                )

            except Exception as e:
                placeholder.markdown("An error occurred. Please try again.")
                st.error(f"Error: {e}")
