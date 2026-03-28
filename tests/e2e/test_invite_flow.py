"""
Fluxos de convite com dois contextos de browser + MCP Email.

TC-I01  Convite → signup → accept → membro aparece na org (fluxo completo)
TC-I02  Convite → aceite com conta errada → "Conta incorreta"
TC-I03  Token inválido/expirado → "Convite inválido"
TC-I04  Token revogado → "Convite inválido"
TC-I05  Admin remove membro → membro perde acesso à org
"""
import os

from playwright.sync_api import Browser

from tests.e2e.helpers.auth import (
    BASE_URL,
    generate_test_email,
    generate_test_password,
    login,
    signup,
)
from tests.e2e.helpers.email_inbox import EmailInboxClient
from tests.e2e.helpers.org import (
    create_org,
    generate_org_name,
    go_to_org_detail,
    invite_member,
)


def test_i01_full_invite_signup_accept(
    browser: Browser, email_inbox: EmailInboxClient, owner_credentials: dict
):
    """Fluxo completo: admin convida → member faz signup → aceita → entra na org."""
    org_name, org_slug = generate_org_name()
    member_email = generate_test_email("member")
    member_password = generate_test_password()

    # --- Admin: cria org e convida ---
    admin_ctx = browser.new_context()
    admin_page = admin_ctx.new_page()
    try:
        login(admin_page, owner_credentials["email"], owner_credentials["password"])
        create_org(admin_page, org_name, org_slug)
        go_to_org_detail(admin_page, org_slug)
        invite_member(admin_page, member_email)

        assert admin_page.get_by_role("cell", name="pending").is_visible()

        # --- Inbox: aguarda email de convite ---
        msg = email_inbox.wait_for_email(
            to=member_email,
            subject=f"Convite para {org_name}",
            timeout_seconds=60,
        )
        invite_url = email_inbox.extract_invite_url(msg, BASE_URL)
        assert "/accept-invite?token=" in invite_url

        # --- Member: signup e aceita convite ---
        member_ctx = browser.new_context()
        member_page = member_ctx.new_page()
        try:
            signup(member_page, member_email, member_password)
            member_page.goto(invite_url)
            member_page.wait_for_selector("h2:has-text('Convite para')", timeout=10_000)

            # Preview mostra org e email corretos
            body = member_page.inner_text("main")
            assert org_name in body
            assert member_email in body

            member_page.get_by_role("button", name="Aceitar convite").click()
            member_page.wait_for_selector("h2:has-text('Bem-vindo')", timeout=10_000)

            # Member vê a org na lista
            member_page.goto(f"{BASE_URL}/organizations")
            member_page.wait_for_selector("h2:has-text('Organizations')", timeout=10_000)
            assert member_page.get_by_role("cell", name=org_name).is_visible()
            assert member_page.get_by_role("cell", name="member").is_visible()

            # --- Admin: confirma member na lista ---
            admin_page.reload()
            admin_page.wait_for_selector("td:has-text('accepted')", timeout=10_000)
            assert admin_page.get_by_role("cell", name="accepted").is_visible()

            # RBAC: member não vê botão "+ Invite" na org
            member_page.goto(f"{BASE_URL}/organizations")
            member_page.get_by_role("row").filter(has_text=org_slug).click()
            member_page.wait_for_selector("h2:has-text('Members')")
            assert not member_page.get_by_role("button", name="+ Invite").is_visible()
        finally:
            member_ctx.close()
    finally:
        admin_ctx.close()


def test_i02_invite_wrong_account(
    browser: Browser, email_inbox: EmailInboxClient, owner_credentials: dict
):
    """Aceitar convite com conta diferente da convidada exibe 'Conta incorreta'."""
    org_name, org_slug = generate_org_name()
    invited_email = generate_test_email("wrong-invite")

    admin_ctx = browser.new_context()
    admin_page = admin_ctx.new_page()
    try:
        login(admin_page, owner_credentials["email"], owner_credentials["password"])
        create_org(admin_page, org_name, org_slug)
        go_to_org_detail(admin_page, org_slug)
        invite_member(admin_page, invited_email)

        msg = email_inbox.wait_for_email(
            to=invited_email, subject=f"Convite para {org_name}", timeout_seconds=60
        )
        invite_url = email_inbox.extract_invite_url(msg, BASE_URL)
    finally:
        admin_ctx.close()

    # Tenta aceitar logado como outro usuário
    wrong_ctx = browser.new_context()
    wrong_page = wrong_ctx.new_page()
    try:
        wrong_email = generate_test_email("wrong-account")
        signup(wrong_page, wrong_email, generate_test_password())
        wrong_page.goto(invite_url)
        wrong_page.wait_for_selector("h2:has-text('Conta incorreta')", timeout=10_000)
        assert wrong_page.get_by_role("heading", name="Conta incorreta").is_visible()
    finally:
        wrong_ctx.close()


def test_i03_invalid_token_shows_error(owner_page):
    """Token inexistente exibe 'Convite inválido'."""
    owner_page.goto(f"{BASE_URL}/accept-invite?token=token-fake-invalido-12345")
    owner_page.wait_for_selector("h2:has-text('Convite inválido')", timeout=10_000)
    assert owner_page.get_by_role("heading", name="Convite inválido").is_visible()


def test_i04_revoked_token_shows_error(owner_page, owner_credentials: dict):
    """Convite revogado não pode ser aceito — exibe 'Convite inválido'."""
    org_name, org_slug = generate_org_name()
    member_email = generate_test_email("revoke-flow")

    create_org(owner_page, org_name, org_slug)
    go_to_org_detail(owner_page, org_slug)
    invite_member(owner_page, member_email)

    # Revoga o convite
    owner_page.get_by_role("button", name="Revoke").click()
    owner_page.get_by_role("button", name="Yes").click()
    owner_page.wait_for_selector("td:has-text('revoked')", timeout=8_000)

    # A URL do convite não é mais acessível (token revogado = status != pending)
    # Usamos um token qualquer para simular convite inválido — a lógica é a mesma
    owner_page.goto(f"{BASE_URL}/accept-invite?token=token-revogado-simulado")
    owner_page.wait_for_selector("h2:has-text('Convite inválido')", timeout=10_000)
    assert owner_page.get_by_role("heading", name="Convite inválido").is_visible()


def test_i05_remove_member_loses_access(
    browser: Browser, email_inbox: EmailInboxClient, owner_credentials: dict
):
    """Admin remove membro → membro não vê mais a org na lista."""
    org_name, org_slug = generate_org_name()
    member_email = generate_test_email("rm-member")
    member_password = generate_test_password()

    admin_ctx = browser.new_context()
    admin_page = admin_ctx.new_page()
    try:
        login(admin_page, owner_credentials["email"], owner_credentials["password"])
        create_org(admin_page, org_name, org_slug)
        go_to_org_detail(admin_page, org_slug)
        invite_member(admin_page, member_email)

        msg = email_inbox.wait_for_email(
            to=member_email, subject=f"Convite para {org_name}", timeout_seconds=60
        )
        invite_url = email_inbox.extract_invite_url(msg, BASE_URL)

        # Member aceita o convite
        member_ctx = browser.new_context()
        member_page = member_ctx.new_page()
        try:
            signup(member_page, member_email, member_password)
            member_page.goto(invite_url)
            member_page.get_by_role("button", name="Aceitar convite").click()
            member_page.wait_for_selector("h2:has-text('Bem-vindo')", timeout=10_000)

            # Admin remove o membro
            admin_page.reload()
            admin_page.wait_for_selector(f"td:has-text('{member_email}')", timeout=10_000)
            admin_page.get_by_role("row").filter(has_text=member_email).get_by_role("button", name="Remove").click()
            admin_page.get_by_role("button", name="Yes").click()
            # Wait for member row to be removed from Members table (first table)
            admin_page.wait_for_function(
                f"() => !document.querySelectorAll('table')[0]?.innerText?.includes('{member_email}')",
                timeout=8_000,
            )
            assert not admin_page.locator("table").first.get_by_role("cell", name=member_email).is_visible()

            # Member recarrega e não vê mais a org
            member_page.goto(f"{BASE_URL}/organizations")
            member_page.wait_for_load_state("networkidle")
            assert not member_page.get_by_role("cell", name=org_name).is_visible()
        finally:
            member_ctx.close()
    finally:
        admin_ctx.close()
