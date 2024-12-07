import streamlit as st
import time
import config
import openai
import logging
from utils import (
    check_password,
    save_interview_data,
    upload_to_google_drive,
    save_session_to_file,
)

# Fetch Google Drive folder ID early to ensure it's available
google_drive_folder_id = None
try:
    google_drive_folder_id = st.secrets.get("google_drive", {}).get("folder_id")
    logging.debug(f"Google Drive folder ID fetched: {google_drive_folder_id}")
except Exception as e:
    logging.error(f"Error fetching Google Drive folder ID: {e}")

# Set OpenAI API key
openai.api_key = st.secrets["API_KEY"]

# Initialize session state variables
if "messages" not in st.session_state:
    st.session_state.messages = []  # Initialize messages as an empty list
if "start_time" not in st.session_state:
    st.session_state.start_time = time.time()
    st.session_state.start_time_file_names = time.strftime(
        "%Y_%m_%d_%H_%M_%S", time.localtime(st.session_state.start_time)
    )
if "interview_active" not in st.session_state:
    st.session_state.interview_active = True

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

# Generate assistant's first message only if there are no existing messages
if not st.session_state.messages:
    try:
        # Use SYSTEM_PROMPT as hidden context for the assistant
        response = openai.ChatCompletion.create(
            model=config.MODEL,
            messages=[{"role": "system", "content": config.SYSTEM_PROMPT}],
            max_tokens=config.MAX_OUTPUT_TOKENS or 1024,
            temperature=config.TEMPERATURE or 0.7,
        )
        first_message = response["choices"][0]["message"]["content"]
        st.session_state.messages.append({"role": "assistant", "content": first_message})
    except Exception as e:
        st.error(f"Error generating the first assistant message: {e}")

# Display all messages in the chat (no duplicates)
for message in st.session_state.messages:
    avatar = (
        config.AVATAR_INTERVIEWER
        if message["role"] == "assistant"
        else config.AVATAR_RESPONDENT
    )
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# Main chat loop
if st.session_state.interview_active:
    user_input = st.chat_input("Your thoughts here")
    if user_input:
        # Append user's message
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user", avatar=config.AVATAR_RESPONDENT):
            st.markdown(user_input)

        # Generate assistant's response
        with st.chat_message("assistant", avatar=config.AVATAR_INTERVIEWER):
            response_placeholder = st.empty()
            response_text = ""
            try:
                # Always include the SYSTEM_PROMPT as the first message
                full_conversation = [{"role": "system", "content": config.SYSTEM_PROMPT}] + st.session_state.messages
                response = openai.ChatCompletion.create(
                    model=config.MODEL,
                    messages=full_conversation,  # Include system prompt + user-assistant conversation
                    max_tokens=config.MAX_OUTPUT_TOKENS or 1024,
                    temperature=config.TEMPERATURE or 0.7,
                    stream=True,
                )
                for chunk in response:
                    text_delta = chunk.choices[0].delta.get("content", "")
                    if text_delta:
                        response_text += text_delta
                        response_placeholder.markdown(response_text + "▌")
            except Exception as e:
                st.error(f"Error during API call: {e}")

            # Finalize and display assistant's response
            response_placeholder.markdown(response_text)
            st.session_state.messages.append(
                {"role": "assistant", "content": response_text}
            )

            # Save progress
            try:
                save_session_to_file(
                    username=st.session_state.username,
                    directory=config.BACKUPS_DIRECTORY,
                    google_drive_folder_id=google_drive_folder_id,
                )
            except Exception as e:
                logging.error(f"Error saving session: {e}")
                st.error(f"Error saving progress: {e}")

# Quit button
if st.button("Quit", help="End the interview."):
    st.session_state.interview_active = False
    st.session_state.messages.append(
        {"role": "assistant", "content": "The interview has ended. Thank you!"}
    )
    save_interview_data(
        username=st.session_state.username,
        transcripts_directory=config.TRANSCRIPTS_DIRECTORY,
        times_directory=config.TIMES_DIRECTORY,
        google_drive_folder_id=google_drive_folder_id,
    )
    st.success("The interview has been saved and ended.")
