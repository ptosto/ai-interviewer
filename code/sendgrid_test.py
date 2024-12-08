

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import logging
import streamlit as st

logging.basicConfig(level=logging.DEBUG)
logging.debug(f"sendgrid_test.py")

def send_email():
    message = Mail(
        from_email=st.secrets["sendgrid"]["twilio_sender"],
        to_emails='peter@tosto.com',
        subject='Test Sendgrid Email',
        plain_text_content='This is another test email sent via SendGrid.'
    )
    try:
        logging.debug(f"Fiing to send: {message}")
        sg = SendGridAPIClient(st.secrets["sendgrid"]["twilio_pw"])
        response = sg.send(message)
        logging.debug(f"Email sent: {response.status_code}")
    except Exception as e:
        logging.debug(f"Error: {e}")

send_email()
