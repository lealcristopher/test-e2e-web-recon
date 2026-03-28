"""
Smoke tests — sanidade básica do sistema.

TC-S01  Acesso sem auth redireciona para Auth0
TC-S02  Health check do backend retorna 200
TC-S03  Login com conta válida aterra em /projects
"""
import os

import httpx
from playwright.sync_api import Page

BASE_URL = os.environ.get("BASE_URL", "https://recon.lealcyber.com")
API_URL = os.environ.get("API_URL", "https://api.lealcyber.com")


def test_s01_unauthenticated_redirect_to_auth0(fresh_page: Page):
    fresh_page.goto(f"{BASE_URL}/projects")
    fresh_page.wait_for_url("**/u/login**", timeout=10_000)
    assert "u/login" in fresh_page.url


def test_s02_backend_health():
    r = httpx.get(f"{API_URL}/health", timeout=10)
    assert r.status_code == 200
    assert r.json().get("status") == "online"


def test_s03_login_lands_on_projects(owner_page: Page):
    owner_page.goto(f"{BASE_URL}/projects")
    owner_page.wait_for_selector("h2:has-text('Projects')", timeout=10_000)
    assert owner_page.get_by_role("heading", name="Projects").is_visible()
