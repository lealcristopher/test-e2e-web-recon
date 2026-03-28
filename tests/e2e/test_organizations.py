"""
Testes de Organizações.

TC-O01  Criar organização aparece na lista
TC-O02  Slug duplicado é rejeitado com mensagem de erro
TC-O03  Detalhe da org exibe Members + Invitations
TC-O04  Convidar membro cria convite com status pending
TC-O05  Convite duplicado (mesmo email + pending) é rejeitado
TC-O06  Revogar convite pending → status vira revoked
"""
import os

from playwright.sync_api import Page

from tests.e2e.helpers.auth import generate_test_email
from tests.e2e.helpers.org import (
    create_org,
    generate_org_name,
    go_to_org_detail,
    invite_member,
)

BASE_URL = os.environ.get("BASE_URL", "https://recon.lealcyber.com")


def test_o01_create_organization(owner_page: Page):
    name, slug = generate_org_name()
    create_org(owner_page, name, slug)

    # Confirma que aparece na lista
    assert owner_page.get_by_role("row").filter(has_text=slug).is_visible()
    assert owner_page.get_by_role("cell", name=name).first.is_visible()


def test_o02_duplicate_slug_rejected(owner_page: Page):
    name, slug = generate_org_name()
    create_org(owner_page, name, slug)

    # Tenta criar com o mesmo slug
    owner_page.get_by_role("button", name="+ New Organization").click()
    owner_page.get_by_placeholder("Acme Corp").fill(name + " 2")
    owner_page.get_by_placeholder("acme-corp").fill(slug)
    owner_page.get_by_role("button", name="Create").click()

    # Backend retorna "Slug já em uso"; frontend exibe inline no form
    owner_page.wait_for_selector("text=Slug já em uso", timeout=8_000)
    assert owner_page.get_by_text("Slug já em uso").is_visible()


def test_o03_org_detail_shows_members_and_invitations(owner_page: Page):
    name, slug = generate_org_name()
    create_org(owner_page, name, slug)
    go_to_org_detail(owner_page, slug)

    assert owner_page.get_by_role("heading", name="Members").is_visible()
    assert owner_page.get_by_role("heading", name="Invitations").is_visible()
    # O botão "+ Invite" depende do OrgContext (isAdmin). Aguarda até 5s para o contexto carregar.
    owner_page.wait_for_selector("button:has-text('+ Invite')", timeout=8_000)
    assert owner_page.get_by_role("button", name="+ Invite").is_visible()


def test_o04_invite_member_creates_pending(owner_page: Page):
    name, slug = generate_org_name()
    create_org(owner_page, name, slug)
    go_to_org_detail(owner_page, slug)

    member_email = generate_test_email("invite")
    invite_member(owner_page, member_email)

    assert owner_page.get_by_role("cell", name=member_email).is_visible()
    assert owner_page.get_by_role("cell", name="pending").is_visible()


def test_o05_duplicate_invite_rejected(owner_page: Page):
    name, slug = generate_org_name()
    create_org(owner_page, name, slug)
    go_to_org_detail(owner_page, slug)

    member_email = generate_test_email("dup-invite")
    invite_member(owner_page, member_email)

    # Segunda tentativa com mesmo email
    owner_page.get_by_role("button", name="+ Invite").click()
    owner_page.get_by_placeholder("email@example.com").fill(member_email)
    owner_page.get_by_role("button", name="Send Invite").click()

    # Backend retorna "Convite pendente já existe para esse e-mail"
    owner_page.wait_for_selector("text=Convite pendente já existe", timeout=8_000)
    assert owner_page.get_by_text("Convite pendente já existe").is_visible()


def test_o06_revoke_invitation(owner_page: Page):
    name, slug = generate_org_name()
    create_org(owner_page, name, slug)
    go_to_org_detail(owner_page, slug)

    member_email = generate_test_email("revoke")
    invite_member(owner_page, member_email)

    # Clica em Revoke (abre confirmação)
    owner_page.get_by_role("button", name="Revoke").click()
    # Confirma com "Yes"
    owner_page.get_by_role("button", name="Yes").click()

    # Status muda para revoked
    owner_page.wait_for_selector("td:has-text('revoked')", timeout=8_000)
    assert owner_page.get_by_role("cell", name="revoked").is_visible()
    # Botão Revoke desaparece (convite não é mais pending)
    assert not owner_page.get_by_role("button", name="Revoke").is_visible()
