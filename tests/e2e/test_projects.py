"""
Testes de lifecycle de projetos (BAT-5).

TC-P01  Owner cria projeto pessoal — aparece na lista com type "Personal"
TC-P02  Owner cria projeto de org — aparece na lista com type "Org"
TC-P03  Owner adiciona wildcard ao projeto — aparece na tabela
TC-P04  Owner adiciona domínio ao projeto — aparece na tabela
TC-P05  ProjectDetail exibe total correto de assets
TC-P06  Owner deleta wildcard — desaparece da tabela
TC-P07  Owner deleta domínio — desaparece da tabela
TC-P08  Owner deleta projeto — desaparece da lista de projetos
"""
import os

from playwright.sync_api import Page

from tests.e2e.helpers.org import create_org, generate_org_name
from tests.e2e.helpers.project import (
    add_domain,
    add_wildcard,
    create_project,
    delete_domain,
    delete_wildcard,
    generate_project_slugs,
    go_to_project_detail,
)

BASE_URL = os.environ.get("BASE_URL", "https://recon.lealcyber.com")

TEST_WILDCARD = "*.e2e-web.lealcyber.com"
TEST_DOMAIN = "e2e-web.lealcyber.com"


def test_p01_create_personal_project(owner_page: Page):
    name, slug = generate_project_slugs()
    create_project(owner_page, name, slug)

    row = owner_page.get_by_role("row").filter(has_text=slug)
    assert row.is_visible()
    assert row.get_by_text("Personal").is_visible()


def test_p02_create_org_project(owner_page: Page):
    org_name, org_slug = generate_org_name()
    create_org(owner_page, org_name, org_slug)

    proj_name, proj_slug = generate_project_slugs()
    create_project(owner_page, proj_name, proj_slug, org_name=org_name)

    row = owner_page.get_by_role("row").filter(has_text=proj_slug)
    assert row.is_visible()
    assert row.get_by_text("Org").is_visible()


def test_p03_add_wildcard(owner_page: Page):
    name, slug = generate_project_slugs()
    create_project(owner_page, name, slug)
    go_to_project_detail(owner_page, name)

    add_wildcard(owner_page, TEST_WILDCARD)
    assert owner_page.get_by_role("cell", name=TEST_WILDCARD).is_visible()


def test_p04_add_domain(owner_page: Page):
    name, slug = generate_project_slugs()
    create_project(owner_page, name, slug)
    go_to_project_detail(owner_page, name)

    add_domain(owner_page, TEST_DOMAIN)
    assert owner_page.get_by_role("cell", name=TEST_DOMAIN).is_visible()


def test_p05_total_assets(owner_page: Page):
    name, slug = generate_project_slugs()
    create_project(owner_page, name, slug)
    go_to_project_detail(owner_page, name)

    add_wildcard(owner_page, TEST_WILDCARD)
    add_domain(owner_page, TEST_DOMAIN)

    assert owner_page.get_by_text("2 assets").is_visible()


def test_p06_delete_wildcard(owner_page: Page):
    name, slug = generate_project_slugs()
    create_project(owner_page, name, slug)
    go_to_project_detail(owner_page, name)

    add_wildcard(owner_page, TEST_WILDCARD)
    delete_wildcard(owner_page, TEST_WILDCARD)

    assert not owner_page.get_by_role("cell", name=TEST_WILDCARD).is_visible()


def test_p07_delete_domain(owner_page: Page):
    name, slug = generate_project_slugs()
    create_project(owner_page, name, slug)
    go_to_project_detail(owner_page, name)

    add_domain(owner_page, TEST_DOMAIN)
    delete_domain(owner_page, TEST_DOMAIN)

    assert not owner_page.get_by_role("cell", name=TEST_DOMAIN).is_visible()


def test_p08_delete_project(owner_page: Page):
    name, slug = generate_project_slugs()
    create_project(owner_page, name, slug)

    go_to_project_detail(owner_page, name)
    owner_page.on("dialog", lambda d: d.accept())
    owner_page.get_by_role("button", name="Delete Project").click()

    owner_page.wait_for_url(f"{BASE_URL}/projects", timeout=10_000)
    assert not owner_page.get_by_role("cell", name=slug).is_visible()
