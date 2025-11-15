from playwright.sync_api import Page, expect

def test_basic_flow(page: Page):
    page.goto("http://localhost:8501")
    
    # check for UI elements
    expect(page.get_by_text("Persona Simulation")).to_be_visible()

    # type user message
    page.fill("textarea", "What do you think of this feature?")

    # click generate
    page.get_by_role("button", name="Generate Responses").click()

    # wait for output
    expect(page.get_by_text("Response")).to_be_visible(timeout=10000)
