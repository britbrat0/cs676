from playwright.sync_api import expect

def test_multi_persona_generation(page):
    page.goto("http://localhost:8501")

    # select multiple personas
    multi = page.locator("select")
    multi.select_option(["Alex", "Jordan"])

    page.fill("textarea", "Give feedback on onboarding")

    page.get_by_role("button", name="Generate Responses").click()
    expect(page.get_by_text("Alex")).to_be_visible(timeout=10000)
    expect(page.get_by_text("Jordan")).to_be_visible(timeout=10000)
