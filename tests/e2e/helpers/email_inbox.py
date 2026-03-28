import os
import quopri
import re
import time
from typing import Optional

import httpx

EMAIL_INBOX_URL = os.environ.get(
    "EMAIL_INBOX_URL",
    "https://email-inbox.cloudflare-protrude525.workers.dev",
)
EMAIL_INBOX_API_KEY = os.environ.get("EMAIL_INBOX_API_KEY", "recon-email-inbox-2026")
AUTH0_DOMAIN = os.environ.get("AUTH0_DOMAIN", "dev-alrmpcah6fsf0yyl.us.auth0.com")


class EmailInboxClient:
    def __init__(self) -> None:
        self.base_url = EMAIL_INBOX_URL.rstrip("/")
        self.api_key = EMAIL_INBOX_API_KEY

    def _headers(self) -> dict:
        return {"X-API-Key": self.api_key}

    def list_messages(
        self,
        to: Optional[str] = None,
        subject: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> list[dict]:
        r = httpx.get(f"{self.base_url}/messages", headers=self._headers(), timeout=15)
        r.raise_for_status()
        messages: list[dict] = r.json()
        if to:
            messages = [m for m in messages if to.lower() in m.get("to", "").lower()]
        if subject:
            messages = [m for m in messages if subject.lower() in m.get("subject", "").lower()]
        if limit:
            messages = messages[:limit]
        return messages

    def get_message(self, message_id: str) -> dict:
        r = httpx.get(f"{self.base_url}/messages/{message_id}", headers=self._headers(), timeout=15)
        r.raise_for_status()
        return r.json()

    def delete_message(self, message_id: str) -> None:
        httpx.delete(f"{self.base_url}/messages/{message_id}", headers=self._headers(), timeout=15)

    def clear_inbox(self) -> dict:
        r = httpx.delete(f"{self.base_url}/messages", headers=self._headers(), timeout=15)
        r.raise_for_status()
        return r.json()

    def wait_for_email(
        self,
        to: Optional[str] = None,
        subject: Optional[str] = None,
        body_contains: Optional[str] = None,
        timeout_seconds: int = 60,
        poll_interval_seconds: int = 3,
    ) -> dict:
        deadline = time.time() + timeout_seconds
        while True:
            for msg in self.list_messages(to=to, subject=subject):
                if body_contains:
                    combined = msg.get("text", "") + msg.get("html", "")
                    if body_contains.lower() not in combined.lower():
                        continue
                return msg
            remaining = deadline - time.time()
            if remaining <= 0:
                raise TimeoutError(
                    f"Email não chegou em {timeout_seconds}s"
                    + (f" (to={to})" if to else "")
                    + (f" (subject={subject})" if subject else "")
                )
            time.sleep(min(poll_interval_seconds, remaining))

    def _decode_body(self, message: dict) -> str:
        """Retorna texto completo do email decodificado de quoted-printable.
        O campo 'html' pode estar truncado — usa 'raw' como fonte primária."""
        text = message.get("text", "")
        raw = message.get("raw", "")
        html_field = message.get("html", "")

        # Decodifica o campo 'raw' (contém o email MIME completo em QP)
        decoded_raw = ""
        if raw:
            try:
                decoded_raw = quopri.decodestring(
                    raw.encode("latin-1", errors="replace")
                ).decode("utf-8", errors="replace")
            except Exception:
                decoded_raw = raw

        # Decodifica o campo 'html' também (pode estar parcialmente decodificado)
        decoded_html = ""
        if html_field:
            try:
                decoded_html = quopri.decodestring(
                    html_field.encode("latin-1", errors="replace")
                ).decode("utf-8", errors="replace")
            except Exception:
                decoded_html = html_field

        return text + "\n" + decoded_html + "\n" + decoded_raw

    def _extract_url(self, message: dict, pattern: str) -> str:
        combined = self._decode_body(message)
        m = re.search(pattern, combined)
        if not m:
            raise ValueError(f"URL não encontrada com pattern '{pattern}'")
        return m.group(1) if m.lastindex else m.group(0)

    def extract_invite_url(self, message: dict, base_url: str) -> str:
        """Extrai URL de aceite de convite do email do backend (Resend)."""
        escaped = re.escape(base_url)
        return self._extract_url(message, rf'href="({escaped}/accept-invite\?token=[^"]+)"')

    def extract_verify_url(self, message: dict) -> str:
        """Extrai URL de verificação de email enviada pelo Auth0."""
        auth0 = re.escape(AUTH0_DOMAIN)
        return self._extract_url(message, rf'(https://{auth0}/u/email-verification\?ticket=[^#<"\s]+)')

    def extract_reset_url(self, message: dict) -> str:
        """Extrai URL de reset de senha enviada pelo Auth0."""
        auth0 = re.escape(AUTH0_DOMAIN)
        return self._extract_url(message, rf'(https://{auth0}/u/reset-verify\?ticket=[^#<"\s]+)')
