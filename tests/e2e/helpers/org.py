import os
import time

from playwright.sync_api import Page

BASE_URL = os.environ.get("BASE_URL", "https://recon.lealcyber.com")


def generate_org_name() -> tuple[str, str]:
    ts = int(time.time())
    name = f"E2E Org {ts}"
    slug = f"e2e-org-{ts}"
    return name, slug


def create_org(page: Page, name: str, slug: str) -> None:
    """Cria uma organização via UI. Espera estar na página /organizations."""
    page.goto(f"{BASE_URL}/organizations")
    page.wait_for_selector("button:has-text('+ New Organization')")
    page.get_by_role("button", name="+ New Organization").click()
    page.get_by_placeholder("Acme Corp").fill(name)
    page.get_by_placeholder("acme-corp").fill(slug)
    page.get_by_role("button", name="Create").click()
    # Aguarda a org aparecer na tabela (confirma criação)
    page.wait_for_selector(f"text={slug}", timeout=10_000)


def go_to_org_detail(page: Page, org_slug: str) -> None:
    """Navega para o detalhe da org pelo slug."""
    page.goto(f"{BASE_URL}/organizations")
    page.wait_for_selector(f"text={org_slug}")
    page.get_by_role("row").filter(has_text=org_slug).click()
    page.wait_for_selector("h2:has-text('Members')", timeout=10_000)


def invite_member(page: Page, email: str) -> None:
    """Envia convite. Deve estar na página de detalhe da org."""
    page.get_by_role("button", name="+ Invite").click()
    page.get_by_placeholder("email@example.com").fill(email)
    page.get_by_role("button", name="Send Invite").click()
    page.wait_for_selector(f"td:has-text('{email}')", timeout=10_000)
