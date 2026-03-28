import os
import pytest
from dotenv import load_dotenv
from playwright.sync_api import Browser, BrowserContext, Page

load_dotenv()

from tests.e2e.helpers.email_inbox import EmailInboxClient
from tests.e2e.helpers.auth import login


@pytest.fixture(scope="session")
def email_inbox() -> EmailInboxClient:
    """Cliente do inbox Cloudflare Worker (compartilhado na sessão)."""
    return EmailInboxClient()


@pytest.fixture(scope="session")
def owner_credentials() -> dict:
    return {
        "email": os.environ["TEST_OWNER_EMAIL"],
        "password": os.environ["TEST_OWNER_PASSWORD"],
    }


@pytest.fixture(scope="session")
def browser_context_args():
    return {"ignore_https_errors": True}


@pytest.fixture
def owner_page(browser: Browser, owner_credentials: dict) -> Page:
    """Contexto fresh pré-autenticado como o owner de teste."""
    context = browser.new_context()
    page = context.new_page()
    login(page, owner_credentials["email"], owner_credentials["password"])
    yield page
    context.close()


@pytest.fixture
def fresh_context(browser: Browser) -> BrowserContext:
    """Contexto de browser limpo (sem autenticação)."""
    context = browser.new_context()
    yield context
    context.close()


@pytest.fixture
def fresh_page(fresh_context: BrowserContext) -> Page:
    """Página limpa sem autenticação."""
    return fresh_context.new_page()
