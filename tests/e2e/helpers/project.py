import os
import time

from playwright.sync_api import Page

BASE_URL = os.environ.get("BASE_URL", "https://recon.lealcyber.com")


def generate_project_slugs() -> tuple[str, str]:
    """Retorna (name, slug) únicos com timestamp."""
    ts = int(time.time())
    name = f"E2E Project {ts}"
    slug = f"e2e-proj-{ts}"
    return name, slug


def create_project(page: Page, name: str, slug: str, org_name: str | None = None) -> None:
    """Cria projeto via UI. org_name=None → projeto pessoal."""
    page.goto(f"{BASE_URL}/projects")
    page.wait_for_selector("button:has-text('+ New Project')")
    page.get_by_role("button", name="+ New Project").click()
    page.get_by_placeholder("My Project").fill(name)
    page.get_by_placeholder("my-project").fill(slug)
    if org_name:
        page.get_by_role("combobox").select_option(label=org_name)
    page.get_by_role("button", name="Create").click()
    page.wait_for_selector(f"text={slug}", timeout=10_000)


def go_to_project_detail(page: Page, project_name: str) -> None:
    """Navega para o detalhe do projeto clicando na linha da lista."""
    page.goto(f"{BASE_URL}/projects")
    page.wait_for_selector(f"text={project_name}")
    page.get_by_role("row").filter(has_text=project_name).click()
    page.wait_for_selector("h2", timeout=10_000)


def add_wildcard(page: Page, pattern: str) -> None:
    """Adiciona wildcard via formulário na página de detalhe."""
    page.get_by_placeholder("*.example.com").fill(pattern)
    page.get_by_role("button", name="Add Wildcard").click()
    page.wait_for_selector(f"td:has-text('{pattern}')", timeout=8_000)


def add_domain(page: Page, domain: str) -> None:
    """Adiciona domínio via formulário na página de detalhe."""
    page.get_by_placeholder("api.example.com").fill(domain)
    page.get_by_role("button", name="Add Domain").click()
    page.wait_for_selector(f"td:has-text('{domain}')", timeout=8_000)


def delete_wildcard(page: Page, pattern: str) -> None:
    """Deleta wildcard clicando no botão Delete da linha correspondente."""
    page.get_by_role("row").filter(has_text=pattern).get_by_role("button", name="Delete").click()
    page.wait_for_selector(f"td:has-text('{pattern}')", state="hidden", timeout=8_000)


def delete_domain(page: Page, domain: str) -> None:
    """Deleta domínio clicando no botão Delete da linha correspondente."""
    page.get_by_role("row").filter(has_text=domain).get_by_role("button", name="Delete").click()
    page.wait_for_selector(f"td:has-text('{domain}')", state="hidden", timeout=8_000)
