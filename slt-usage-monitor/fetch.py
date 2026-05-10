import os
import json
import re
from pathlib import Path
from datetime import datetime, timezone

from playwright.sync_api import sync_playwright

SLT_URL = "https://www.myslt.lk/"
STORAGE_STATE_PATH = os.environ.get("STORAGE_STATE_PATH", "storage_state.json")
SCREENSHOT_PATH = Path("slt_debug.png")
HISTORY_PATH = Path("storage.json")


def try_selectors(page, selectors):
    for sel in selectors:
        try:
            locator = page.locator(sel)
            if locator.count() > 0:
                return locator
        except Exception:
            continue
    return None


def extract_usage_summary(page_text):
    lowered = page_text.lower()
    summary = {}

    patterns = {
        "used_gb": [r"(?:used|usage|consumed)[^\d]{0,20}(\d+(?:\.\d+)?)\s*(gb|mb)", r"(\d+(?:\.\d+)?)\s*(gb|mb)[^\n]{0,20}(?:used|usage|consumed)"],
        "total_gb": [r"(?:total|quota|package)[^\d]{0,20}(\d+(?:\.\d+)?)\s*(gb|mb)", r"(\d+(?:\.\d+)?)\s*(gb|mb)[^\n]{0,20}(?:total|quota|package)"],
        "remaining_gb": [r"(?:remaining|balance|left)[^\d]{0,20}(\d+(?:\.\d+)?)\s*(gb|mb)", r"(\d+(?:\.\d+)?)\s*(gb|mb)[^\n]{0,20}(?:remaining|balance|left)"],
    }

    def to_gb(value, unit):
        number = float(value)
        if unit.lower() == "mb":
            return round(number / 1024, 3)
        return round(number, 3)

    for key, regex_list in patterns.items():
        for regex in regex_list:
            match = re.search(regex, lowered, re.IGNORECASE)
            if match:
                summary[key] = to_gb(match.group(1), match.group(2))
                break

    if "used_gb" not in summary and "remaining_gb" in summary and "total_gb" in summary:
        summary["used_gb"] = round(summary["total_gb"] - summary["remaining_gb"], 3)

    return summary


def append_history_entry(entry):
    history = []
    if HISTORY_PATH.exists():
        try:
            loaded = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
            if isinstance(loaded, list):
                history = loaded
        except Exception:
            history = []

    history.append(entry)
    HISTORY_PATH.write_text(json.dumps(history, indent=2), encoding="utf-8")


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

            page.wait_for_timeout(2000)

            page_text = ""
            try:
                page_text = page.locator("body").inner_text(timeout=10000)
            except Exception as exc:
                print(f"Unable to read page body text for extraction: {exc}")

            usage_summary = extract_usage_summary(page_text) if page_text else {}
            if usage_summary:
                print("Extracted usage summary:")
                for key, value in usage_summary.items():
                    print(f"  {key}: {value}")
            else:
                print("No usage summary detected yet; page content will still be stored in history")

            history_entry = {
                "date": datetime.now(timezone.utc).date().isoformat(),
                "used_gb": usage_summary.get("used_gb", 0),
                "total_gb": usage_summary.get("total_gb", 0),
                "remaining_gb": usage_summary.get("remaining_gb", 0),
                "page_title": page.title(),
            }
            append_history_entry(history_entry)
            print(f"Saved history entry to {HISTORY_PATH}")
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
