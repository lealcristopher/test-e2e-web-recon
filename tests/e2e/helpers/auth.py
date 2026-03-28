import os
import time

from playwright.sync_api import Page

BASE_URL = os.environ.get("BASE_URL", "https://recon.lealcyber.com")


def generate_test_email(prefix: str = "e2e") -> str:
    """Gera email único roteado para o inbox Cloudflare Worker (@lealcyber.com)."""
    ts = int(time.time())
    return f"{prefix}-{ts}@lealcyber.com"


def generate_test_password() -> str:
    return "ReconTest@2026!"


def signup(page: Page, email: str, password: str) -> None:
    page.goto(BASE_URL)
    page.wait_for_url("**/u/login**")
    page.get_by_role("link", name="Sign up").click()
    page.wait_for_url("**/u/signup**")
    page.get_by_role("textbox", name="Email address").fill(email)
    page.get_by_role("textbox", name="Password").fill(password)
    page.get_by_role("button", name="Continue", exact=True).click()
    page.wait_for_url(f"{BASE_URL}/**", timeout=20_000)
    page.wait_for_selector("button:has-text('Logout')", timeout=10_000)


def login(page: Page, email: str, password: str) -> None:
    page.goto(BASE_URL)
    page.wait_for_url("**/u/login**")
    page.get_by_role("textbox", name="Email address").fill(email)
    page.get_by_role("textbox", name="Password").fill(password)
    page.get_by_role("button", name="Continue", exact=True).click()
    page.wait_for_url(f"{BASE_URL}/**", timeout=20_000)
    page.wait_for_selector("button:has-text('Logout')", timeout=10_000)


def logout(page: Page) -> None:
    page.get_by_role("button", name="Logout").click()
    page.wait_for_url("**/u/login**", timeout=10_000)
