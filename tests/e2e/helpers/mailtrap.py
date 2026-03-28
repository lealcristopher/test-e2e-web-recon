import time
import re
import httpx
import os


class MailtrapClient:
    def __init__(self):
        self.token = os.environ["MAILTRAP_API_TOKEN"]
        self.account_id = os.environ["MAILTRAP_ACCOUNT_ID"]
        self.inbox_id = os.environ["MAILTRAP_INBOX_ID"]
        self.base = f"https://mailtrap.io/api/accounts/{self.account_id}/inboxes/{self.inbox_id}"

    def _headers(self):
        return {"Api-Token": self.token}

    def list_messages(self) -> list[dict]:
        r = httpx.get(f"{self.base}/messages", headers=self._headers(), timeout=10)
        r.raise_for_status()
        return r.json()

    def get_message_body(self, message_id: str) -> str:
        r = httpx.get(f"{self.base}/messages/{message_id}/body.html", headers=self._headers(), timeout=10)
        r.raise_for_status()
        return r.text

    def delete_message(self, message_id: str) -> None:
        httpx.delete(f"{self.base}/messages/{message_id}", headers=self._headers(), timeout=10)

    def clean_inbox(self) -> None:
        httpx.patch(f"{self.base}/clean", headers=self._headers(), timeout=10)

    def wait_for_email(self, to_email: str, subject_contains: str = "", timeout: int = 30) -> dict:
        deadline = time.time() + timeout
        while time.time() < deadline:
            messages = self.list_messages()
            for msg in messages:
                to_match = to_email.lower() in msg.get("to_email", "").lower()
                subj_match = subject_contains.lower() in msg.get("subject", "").lower() if subject_contains else True
                if to_match and subj_match:
                    return msg
            time.sleep(2)
        raise TimeoutError(f"Email para '{to_email}' não chegou em {timeout}s")

    def extract_invite_url(self, message_id: str, base_url: str) -> str:
        body = self.get_message_body(message_id)
        pattern = rf'href="({re.escape(base_url)}/accept-invite\?token=[^"]+)"'
        match = re.search(pattern, body)
        if not match:
            raise ValueError(f"Invite URL não encontrado no e-mail.\nBody:\n{body[:500]}")
        return match.group(1)
