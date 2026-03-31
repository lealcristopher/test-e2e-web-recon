"""
Testes de RBAC de escrita em projetos (BAT-8).

TC-RW01  Member NÃO vê botão "+ New Project"
TC-RW02  Member NÃO vê formulário "Add Wildcard" no projeto de org
TC-RW03  Member NÃO vê formulário "Add Domain" no projeto de org
TC-RW04  Member NÃO vê botões "Delete" em wildcards/domains
TC-RW05  Member NÃO vê botão "Delete Project"
TC-RW06  User externo NÃO vê projeto de org na lista de projetos

Reusa o fixture visibility_state de test_project_visibility para evitar
recriação desnecessária de org + projetos.
"""
import os

from playwright.sync_api import Page

from tests.e2e.helpers.auth import BASE_URL
from tests.e2e.helpers.project import go_to_project_detail
from tests.e2e.test_project_visibility import visibility_state  # reutiliza fixture

__all__ = ["visibility_state"]  # noqa: F401 — necessário para pytest coletar o fixture


def test_rw01_member_no_new_project_button(member_page: Page):
    """Member não vê o botão '+ New Project' (reservado para admins)."""
    member_page.goto(f"{BASE_URL}/projects")
    member_page.wait_for_selector("h2:has-text('Projects')")
    assert not member_page.get_by_role("button", name="+ New Project").is_visible()


def test_rw02_member_no_add_wildcard(member_page: Page, visibility_state: dict):
    """Member não vê formulário Add Wildcard no projeto de org."""
    go_to_project_detail(member_page, visibility_state["org_proj_name"])
    assert not member_page.get_by_placeholder("*.example.com").is_visible()
    assert not member_page.get_by_role("button", name="Add Wildcard").is_visible()


def test_rw03_member_no_add_domain(member_page: Page, visibility_state: dict):
    """Member não vê formulário Add Domain no projeto de org."""
    go_to_project_detail(member_page, visibility_state["org_proj_name"])
    assert not member_page.get_by_placeholder("api.example.com").is_visible()
    assert not member_page.get_by_role("button", name="Add Domain").is_visible()


def test_rw04_member_no_delete_scope_buttons(member_page: Page, visibility_state: dict):
    """Member não vê botões Delete em wildcards e domínios."""
    go_to_project_detail(member_page, visibility_state["org_proj_name"])
    assert not member_page.get_by_role("button", name="Delete").is_visible()


def test_rw05_member_no_delete_project(member_page: Page, visibility_state: dict):
    """Member não vê botão Delete Project."""
    go_to_project_detail(member_page, visibility_state["org_proj_name"])
    assert not member_page.get_by_role("button", name="Delete Project").is_visible()


def test_rw06_user_no_org_project_in_list(user_page: Page, visibility_state: dict):
    """User externo não enxerga o projeto de org na lista."""
    user_page.goto(f"{BASE_URL}/projects")
    user_page.wait_for_selector("h2:has-text('Projects')")
    assert not user_page.get_by_role("cell", name=visibility_state["org_proj_slug"]).is_visible()
