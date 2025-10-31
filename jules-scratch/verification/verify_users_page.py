from playwright.sync_api import sync_playwright

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    page.goto("http://localhost:5179")
    page.get_by_placeholder("Enter your email").click()
    page.get_by_placeholder("Enter your email").fill("admin@example.com")
    page.get_by_placeholder("Enter your password").click()
    page.get_by_placeholder("Enter your password").fill("password")
    page.get_by_role("button", name="Sign In").click()
    page.get_by_role("link", name="Users").click()
    page.screenshot(path="jules-scratch/verification/verification.png")
    context.close()
    browser.close()

with sync_playwright() as playwright:
    run(playwright)
