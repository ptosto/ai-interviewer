
import streamlit as st
import time
import os
import config
import openai

from utils import (
    check_password,
    check_if_interview_completed,
    save_interview_data,
)

# Set page title and icon
st.set_page_config(page_title="Interview", page_icon=config.AVATAR_INTERVIEWER)

# Set OpenAI API key
openai.api_key = st.secrets["API_KEY"]

# Check if usernames and logins are enabled
if config.LOGINS:
    # Check password (displays login screen)
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

# Initialize session state
if "interview_active" not in st.session_state:
    st.session_state.interview_active = True

if "messages" not in st.session_state:
    # Initialize with a system message and first assistant message
    st.session_state.messages = [{"role": "system", "content": config.SYSTEM_PROMPT}]

    # Generate the first assistant message from the system prompt
    response = openai.ChatCompletion.create(
        model=config.MODEL,
        messages=st.session_state.messages,
        max_tokens=config.MAX_OUTPUT_TOKENS or 1024,
        temperature=config.TEMPERATURE or 0.7,
    )
    intro_message = response["choices"][0]["message"]["content"]
    st.session_state.messages.append({"role": "assistant", "content": intro_message})

if "start_time" not in st.session_state:
    st.session_state.start_time = time.time()
    st.session_state.start_time_file_names = time.strftime(
        "%Y_%m_%d_%H_%M_%S", time.localtime(st.session_state.start_time)
    )

# Check if interview previously completed
interview_previously_completed = check_if_interview_completed(
    config.TIMES_DIRECTORY, st.session_state.username
)

# If app started but interview was previously completed
if interview_previously_completed and not st.session_state.messages:
    st.session_state.interview_active = False
    st.markdown("Interview already completed.")

# Add 'Quit' button to dashboard
col1, col2 = st.columns([0.85, 0.15])
with col2:
    if st.session_state.interview_active and st.button("Quit", help="End the interview."):
        st.session_state.interview_active = False
        quit_message = "You have cancelled the interview."
        st.session_state.messages.append({"role": "assistant", "content": quit_message})
        save_interview_data(
            st.session_state.username,
            config.TRANSCRIPTS_DIRECTORY,
            config.TIMES_DIRECTORY,
        )

# Display all previous messages
for message in st.session_state.messages[1:]:
    avatar = config.AVATAR_INTERVIEWER if message["role"] == "assistant" else config.AVATAR_RESPONDENT
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# Main chat if interview is active
if st.session_state.interview_active:
    # Chat input and message for respondent
    if message_respondent := st.chat_input("Your message here"):
        st.session_state.messages.append({"role": "user", "content": message_respondent})

        # Display respondent message
        with st.chat_message("user", avatar=config.AVATAR_RESPONDENT):
            st.markdown(message_respondent)

        # Generate and display interviewer message
        with st.chat_message("assistant", avatar=config.AVATAR_INTERVIEWER):
            message_placeholder = st.empty()
            message_interviewer = ""

            try:
                # Call OpenAI API
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

            # Finalize interviewer message
            message_placeholder.markdown(message_interviewer)
            st.session_state.messages.append({"role": "assistant", "content": message_interviewer})

            # Regularly save interview progress
            save_interview_data(
                username=st.session_state.username,
                transcripts_directory=config.BACKUPS_DIRECTORY,
                times_directory=config.BACKUPS_DIRECTORY,
                file_name_addition_transcript=f"_transcript_{st.session_state.start_time_file_names}",
                file_name_addition_time=f"_time_{st.session_state.start_time_file_names}",
            )
