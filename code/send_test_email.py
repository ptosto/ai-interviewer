"""Send a test email using the existing send_email helper.

The script populates Streamlit secrets from environment variables when
running outside of a Streamlit app. Required environment variables:
    - GMAIL_USER
    - GMAIL_PW
    - GMAIL_FROM
Optional:
    - EMAIL_TEST_USERNAME (default: "testuser")

The recipient and subject template come from config.py (SEND_TO and
SEND_SUBJECT). The message body is fixed to a short test string.
"""

import os
import streamlit as st
from utils import send_email


def _ensure_secret(key: str, env_var: str) -> None:
    """Populate st.secrets[key] from environment variable if not set."""
    if key in st.secrets:
        return
    env_value = os.getenv(env_var)
    if env_value:
        # _secrets is a mutable mapping in the runtime Secrets object
        st.secrets._secrets[key] = env_value


def _load_secrets_from_env() -> None:
    # Prime the underlying mapping in case Streamlit did not load secrets
    if not hasattr(st.secrets, "_secrets") or st.secrets._secrets is None:
        st.secrets._secrets = {}

    _ensure_secret("gmail_user", "GMAIL_USER")
    _ensure_secret("gmailpw", "GMAIL_PW")
    _ensure_secret("gmail_from", "GMAIL_FROM")

    missing = [key for key in ("gmail_user", "gmailpw", "gmail_from") if key not in st.secrets]
    if missing:
        raise SystemExit(
            "Missing required secrets: "
            + ", ".join(missing)
            + ". Set them as environment variables or via Streamlit secrets."
        )


def main() -> None:
    _load_secrets_from_env()
    st.session_state.username = os.getenv("EMAIL_TEST_USERNAME", "testuser")
    send_email("Test email sent via send_test_email.py")


if __name__ == "__main__":
    main()
