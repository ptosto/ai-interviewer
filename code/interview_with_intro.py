
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
    # Initialize with a system message
    st.session_state.messages = [{"role": "system", "content": config.SYSTEM_PROMPT}]

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
    completed_message = "Interview already completed."
    st.markdown(completed_message)


# Add 'Quit' button to dashboard
col1, col2 = st.columns([0.85, 0.15])
with col2:
    if st.session_state.interview_active and st.button(
        "Quit", help="End the interview."
    ):
        st.session_state.interview_active = False
        quit_message = "You have cancelled the interview."
        st.session_state.messages.append({"role": "assistant", "content": quit_message})
        save_interview_data(
            st.session_state.username,
            config.TRANSCRIPTS_DIRECTORY,
            config.TIMES_DIRECTORY,
        )


# Display the introduction message at initialization
if "intro_message_sent" not in st.session_state:
    st.session_state.intro_message_sent = False

if not st.session_state.intro_message_sent:
    intro_message = {
        "role": "assistant",
        "content": """Hello! I’m glad to have the opportunity to discuss your knowledge and readiness for an IT Analyst role.

I’ll ask you questions across several topics. Answer in a way that demonstrates your level of understanding and personal point of view on the topic (e.g., value, importance, preferred method).

Please do not hesitate to ask if anything is unclear.

Start by telling me your full name."""
    }
    st.session_state.messages.append(intro_message)
    st.session_state.intro_message_sent = True

# Upon rerun, display the previous conversation (except system prompt or first message)
for message in st.session_state.messages[1:]:
    avatar = config.AVATAR_INTERVIEWER if message["role"] == "assistant" else config.AVATAR_RESPONDENT
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])


# API kwargs
api_kwargs = {
    "model": config.MODEL,
    "messages": st.session_state.messages,
    "temperature": config.TEMPERATURE or 0.7,
    "max_tokens": config.MAX_OUTPUT_TOKENS or 1024,
    "stream": True  # Stream responses
}

# Main chat if interview is active
if st.session_state.interview_active:

    # Chat input and message for respondent
    if message_respondent := st.chat_input("Your message here"):
        st.session_state.messages.append(
            {"role": "user", "content": message_respondent}
        )

        # Display respondent message
        with st.chat_message("user", avatar=config.AVATAR_RESPONDENT):
            st.markdown(message_respondent)

        # Generate and display interviewer message
        with st.chat_message("assistant", avatar=config.AVATAR_INTERVIEWER):

            # Create placeholder for message in chat interface
            message_placeholder = st.empty()

            # Initialise message of interviewer
            message_interviewer = ""

            try:
                # Call OpenAI API
                response = openai.ChatCompletion.create(**api_kwargs)
                
                # Handle streaming response
                for chunk in response:
                    text_delta = chunk.choices[0].delta.get("content", "")
                    if text_delta:
                        message_interviewer += text_delta
                        message_placeholder.markdown(message_interviewer + "▌")
                    # Check for codes
                    if any(code in message_interviewer for code in config.CLOSING_MESSAGES.keys()):
                        message_placeholder.empty()
                        break
            except Exception as e:
                st.error(f"Error during API call: {e}")
                #return

            # If no code is in the message, display and store the message
            if not any(
                code in message_interviewer for code in config.CLOSING_MESSAGES.keys()
            ):

                message_placeholder.markdown(message_interviewer)
                st.session_state.messages.append(
                    {"role": "assistant", "content": message_interviewer}
                )

                # Regularly store interview progress as backup, but prevent script from
                # stopping in case of a write error
                try:

                    save_interview_data(
                        username=st.session_state.username,
                        transcripts_directory=config.BACKUPS_DIRECTORY,
                        times_directory=config.BACKUPS_DIRECTORY,
                        file_name_addition_transcript=f"_transcript_started_{st.session_state.start_time_file_names}",
                        file_name_addition_time=f"_time_started_{st.session_state.start_time_file_names}",
                    )

                except:
                    pass

            # If code in the message, display the associated closing message instead
            # Loop over all codes
            for code in config.CLOSING_MESSAGES.keys():

                if code in message_interviewer:
                    st.session_state.messages.append(
                        {"role": "assistant", "content": message_interviewer}
                    )

                    # Set chat to inactive and display closing message
                    st.session_state.interview_active = False
                    closing_message = config.CLOSING_MESSAGES[code]
                    st.markdown(closing_message)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": closing_message}
                    )

                    # Store final transcript and time
                    final_transcript_stored = False
                    while final_transcript_stored == False:

                        save_interview_data(
                            username=st.session_state.username,
                            transcripts_directory=config.TRANSCRIPTS_DIRECTORY,
                            times_directory=config.TIMES_DIRECTORY,
                        )

                        final_transcript_stored = check_if_interview_completed(
                            config.TRANSCRIPTS_DIRECTORY, st.session_state.username
                        )
                        time.sleep(0.1)
