"""
Testes de autenticação.

TC-A01  Signup → email de verificação chega no inbox → link funciona
TC-A02  Login / Logout ciclo completo
TC-A03  Login com senha errada exibe mensagem de erro
TC-A04  Signup com email já registrado exibe erro do Auth0
TC-A05  Password reset → email no inbox → link de reset funciona
"""
import os

from playwright.sync_api import Browser, Page

from tests.e2e.helpers.auth import (
    BASE_URL,
    generate_test_email,
    generate_test_password,
    login,
    logout,
    signup,
)
from tests.e2e.helpers.email_inbox import EmailInboxClient


def test_a01_signup_and_email_verification(browser: Browser, email_inbox: EmailInboxClient):
    """Signup com novo email → verificação chega no inbox → link de verificação funciona."""
    email = generate_test_email("signup")
    password = generate_test_password()

    ctx = browser.new_context()
    page = ctx.new_page()
    try:
        signup(page, email, password)

        # Usuário já está logado (Auth0 não bloqueia antes de verificar)
        assert page.url.startswith(BASE_URL)
        assert page.get_by_role("button", name="Logout").is_visible()
        assert email in page.inner_text("nav")

        # Email de verificação deve chegar no inbox
        msg = email_inbox.wait_for_email(
            to=email, subject="Verify your email", timeout_seconds=60
        )
        assert msg is not None

        # Link de verificação deve ser acessível
        verify_url = email_inbox.extract_verify_url(msg)
        assert "email-verification" in verify_url

        # Navega ao link e verifica que não cai numa página de erro
        page.goto(verify_url)
        page.wait_for_load_state("networkidle", timeout=15_000)
        # Auth0 redireciona para o app ou exibe página de confirmação
        # Em ambos os casos, não deve estar em uma página de erro 4xx/5xx
        assert "error" not in page.url.lower() or BASE_URL in page.url
    finally:
        ctx.close()


def test_a02_login_logout(owner_page: Page, owner_credentials: dict):
    """Login exibe navbar com email; logout redireciona para Auth0."""
    assert owner_page.get_by_role("button", name="Logout").is_visible()
    assert owner_credentials["email"] in owner_page.inner_text("nav")

    logout(owner_page)
    assert "u/login" in owner_page.url


def test_a03_invalid_credentials(fresh_page: Page):
    """Login com senha errada exibe erro do Auth0."""
    fresh_page.goto(BASE_URL)
    fresh_page.wait_for_url("**/u/login**")
    fresh_page.get_by_role("textbox", name="Email address").fill("nobody@lealcyber.com")
    fresh_page.get_by_role("textbox", name="Password").fill("SenhaErrada!999")
    fresh_page.get_by_role("button", name="Continue", exact=True).click()

    # Auth0 exibe mensagem de erro inline
    fresh_page.wait_for_selector("[class*='error'], [class*='alert'], p[class*='error']", timeout=8_000)
    assert "u/login" in fresh_page.url


def test_a04_signup_existing_email(fresh_page: Page, owner_credentials: dict):
    """Tentar registrar email já existente exibe erro do Auth0."""
    fresh_page.goto(BASE_URL)
    fresh_page.wait_for_url("**/u/login**")
    fresh_page.get_by_role("link", name="Sign up").click()
    fresh_page.wait_for_url("**/u/signup**")
    fresh_page.get_by_role("textbox", name="Email address").fill(owner_credentials["email"])
    fresh_page.get_by_role("textbox", name="Password").fill(owner_credentials["password"])
    fresh_page.get_by_role("button", name="Continue", exact=True).click()

    # Permanece na página de signup com mensagem de erro
    fresh_page.wait_for_selector("[class*='error'], [class*='alert'], p", timeout=8_000)
    assert "u/signup" in fresh_page.url or "u/login" in fresh_page.url


def test_a05_password_reset_email(browser: Browser, email_inbox: EmailInboxClient):
    """Reset de senha → email chega no inbox → link de reset é válido."""
    # Usa um email existente (do owner) para acionar o reset
    # Cria um usuário temporário para não interferir com o owner
    temp_email = generate_test_email("reset")
    temp_password = generate_test_password()

    ctx = browser.new_context()
    page = ctx.new_page()
    try:
        # Cria conta temporária
        signup(page, temp_email, temp_password)
        logout(page)

        # Aciona reset de senha
        page.goto(BASE_URL)
        page.wait_for_url("**/u/login**")
        page.get_by_role("link", name="Reset password").click()
        page.wait_for_url("**/reset-password/**")
        page.get_by_role("textbox", name="Email address").fill(temp_email)
        page.get_by_role("button", name="Continue", exact=True).click()

        # Auth0 exibe confirmação de envio
        page.wait_for_selector("text=email", timeout=10_000)

        # Email de reset deve chegar no inbox
        msg = email_inbox.wait_for_email(
            to=temp_email, subject="Reset your password", timeout_seconds=60
        )
        assert msg is not None

        # Link de reset deve ser acessível
        reset_url = email_inbox.extract_reset_url(msg)
        assert "reset-verify" in reset_url
    finally:
        ctx.close()
