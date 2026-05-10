from playwright.sync_api import sync_playwright
import os
import re
from datetime import datetime

SLT_URL = "https://www.myslt.lk/"
STORAGE_STATE_PATH = os.environ.get("STORAGE_STATE_PATH", "storage_state.json")


def try_selectors(page, selectors):
    for sel in selectors:
        try:
            locator = page.locator(sel)
            if locator.count() > 0:
                return locator
        except Exception:
            continue
    return None


def main():
    user = os.environ.get("SLT_USER")
    password = os.environ.get("SLT_PASS")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        context = browser.new_context()
        page = context.new_page()

        page.goto(SLT_URL, timeout=60000)
        print("SLT portal loaded successfully")

        # Save a screenshot for debugging
        ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        screenshot_name = f"slt_debug_{ts}.png"
        page.screenshot(path=screenshot_name)
        print(f"Saved screenshot: {screenshot_name}")

        # Phase 2 skeleton: attempt login if credentials present
        if user and password:
            print("SLT credentials provided in environment — attempting login (skeleton)")

            # Try to find common login entry points
            login_links = ["text=Login", "text=Log In", "a:has-text('Login')", "a:has-text('Log In')"]
            for l in login_links:
                try:
                    if page.locator(l).count() > 0:
                        page.locator(l).first.click()
                        break
                except Exception:
                    continue

            # Try common username/password selectors
            username_selectors = ["input[name='username']", "input[name='user']", "input#username", "input[name='email']", "input[type='email']"]
            password_selectors = ["input[name='password']", "input#password", "input[type='password']"]

            user_field = try_selectors(page, username_selectors)
            pass_field = try_selectors(page, password_selectors)

            if user_field and pass_field:
                try:
                    user_field.fill(user)
                    pass_field.fill(password)

                    # Try to submit the form
                    # Look for a submit button nearby
                    submit = try_selectors(page, ["button[type='submit']", "button:has-text('Login')", "button:has-text('Log In')"]) 
                    if submit:
                        submit.first.click()
                    else:
                        page.keyboard.press('Enter')

                    # wait for navigation or some known element
                    page.wait_for_timeout(5000)
                    print("Login attempt finished (check screenshot/artifacts for result)")

                    # Save storage state for reuse in subsequent runs
                    context.storage_state(path=STORAGE_STATE_PATH)
                    print(f"Saved storage state to {STORAGE_STATE_PATH}")
                except Exception as e:
                    print(f"Login attempt failed: {e}")
            else:
                print("Could not locate username/password fields — login skeleton skipped")

        browser.close()


if __name__ == "__main__":
    main()
