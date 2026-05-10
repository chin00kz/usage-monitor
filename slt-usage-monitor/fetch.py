import os
from pathlib import Path

from playwright.sync_api import sync_playwright

SLT_URL = "https://www.myslt.lk/"
STORAGE_STATE_PATH = os.environ.get("STORAGE_STATE_PATH", "storage_state.json")
SCREENSHOT_PATH = Path("slt_debug.png")


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

        try:
            page.goto(SLT_URL, wait_until="domcontentloaded", timeout=60000)
            print("SLT portal loaded successfully")

            # Phase 2 skeleton: attempt login if credentials are present.
            if user and password:
                print("SLT credentials provided in environment - attempting login (skeleton)")

                login_links = ["text=Login", "text=Log In", "a:has-text('Login')", "a:has-text('Log In')"]
                for link in login_links:
                    try:
                        if page.locator(link).count() > 0:
                            page.locator(link).first.click()
                            break
                    except Exception:
                        continue

                username_selectors = [
                    "input[name='username']",
                    "input[name='user']",
                    "input#username",
                    "input[name='email']",
                    "input[type='email']",
                ]
                password_selectors = ["input[name='password']", "input#password", "input[type='password']"]

                user_field = try_selectors(page, username_selectors)
                pass_field = try_selectors(page, password_selectors)

                if user_field and pass_field:
                    user_field.fill(user)
                    pass_field.fill(password)

                    submit = try_selectors(page, ["button[type='submit']", "button:has-text('Login')", "button:has-text('Log In')"])
                    if submit:
                        submit.first.click()
                    else:
                        page.keyboard.press("Enter")

                    page.wait_for_timeout(5000)
                    print("Login attempt finished (check screenshot/artifacts for result)")

                    context.storage_state(path=STORAGE_STATE_PATH)
                    print(f"Saved storage state to {STORAGE_STATE_PATH}")
                else:
                    print("Could not locate username/password fields - login skeleton skipped")
            else:
                print("No SLT credentials provided - running in safe mode")
        except Exception as exc:
            print(f"SLT run encountered an error but will continue to capture artifacts: {exc}")
        finally:
            try:
                page.screenshot(path=str(SCREENSHOT_PATH), full_page=True)
                print(f"Saved screenshot: {SCREENSHOT_PATH}")
            except Exception as exc:
                print(f"Unable to save screenshot: {exc}")

            browser.close()


if __name__ == "__main__":
    main()
