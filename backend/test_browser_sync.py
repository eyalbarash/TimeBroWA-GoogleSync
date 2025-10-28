#!/usr/bin/env python3
"""
Browser test using Playwright to debug the sync button functionality
"""
import asyncio
from playwright.async_api import async_playwright
import sys
from datetime import datetime, timedelta

async def test_sync_button():
    """Test the sync all button and debug why it's not working"""

    async with async_playwright() as p:
        # Launch browser with visible UI
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        context = await browser.new_context()
        page = await context.new_page()

        # Enable console logging
        page.on("console", lambda msg: print(f"🖥️  Console: {msg.type}: {msg.text}"))

        # Enable error logging
        page.on("pageerror", lambda err: print(f"❌ Page Error: {err}"))

        # Enable request/response logging
        page.on("request", lambda req: print(f"➡️  Request: {req.method} {req.url}"))
        page.on("response", lambda res: print(f"⬅️  Response: {res.status} {res.url}"))

        try:
            print("🌐 Navigating to localhost:8080...")
            await page.goto("http://localhost:8080", timeout=10000)
            print("✅ Page loaded successfully")

            # Wait for the page to be ready
            await page.wait_for_load_state("networkidle")

            # Check if datetime inputs exist
            print("\n🔍 Checking datetime inputs...")
            start_input = page.locator("#sync-start-date-all")
            end_input = page.locator("#sync-end-date-all")

            start_exists = await start_input.count() > 0
            end_exists = await end_input.count() > 0

            print(f"Start datetime input exists: {start_exists}")
            print(f"End datetime input exists: {end_exists}")

            if not start_exists or not end_exists:
                print("❌ Datetime inputs not found!")
                return

            # Get current values
            start_value = await start_input.input_value()
            end_value = await end_input.input_value()

            print(f"\n📅 Current datetime values:")
            print(f"  Start: '{start_value}'")
            print(f"  End: '{end_value}'")

            # Check if values are empty
            if not start_value or not end_value:
                print("\n⚠️  DateTime inputs are EMPTY - this is likely the problem!")
                print("Setting datetime values manually...")

                # Set datetime values (30 days ago to today)
                end_dt = datetime.now()
                start_dt = end_dt - timedelta(days=30)

                start_str = start_dt.strftime("%Y-%m-%dT%H:%M")
                end_str = end_dt.strftime("%Y-%m-%dT%H:%M")

                print(f"  Setting start: {start_str}")
                print(f"  Setting end: {end_str}")

                await start_input.fill(start_str)
                await end_input.fill(end_str)

                # Verify values were set
                start_value = await start_input.input_value()
                end_value = await end_input.input_value()
                print(f"\n✅ Values after setting:")
                print(f"  Start: '{start_value}'")
                print(f"  End: '{end_value}'")

            # Check if sync button exists
            print("\n🔍 Checking sync button...")
            sync_btn = page.locator("#sync-all-btn")
            btn_exists = await sync_btn.count() > 0
            print(f"Sync button exists: {btn_exists}")

            if not btn_exists:
                print("❌ Sync button not found!")
                return

            # Get button text
            btn_text = await sync_btn.text_content()
            print(f"Button text: '{btn_text}'")

            # Check if button is visible and enabled
            is_visible = await sync_btn.is_visible()
            is_enabled = await sync_btn.is_enabled()
            print(f"Button visible: {is_visible}")
            print(f"Button enabled: {is_enabled}")

            # Setup dialog handler before clicking
            dialog_appeared = False
            dialog_message = ""

            async def on_dialog(dialog):
                nonlocal dialog_appeared, dialog_message
                dialog_appeared = True
                dialog_message = dialog.message
                print(f"\n💬 Dialog appeared: {dialog.message}")
                await dialog.accept()

            page.on("dialog", on_dialog)

            # Click the button
            print("\n🖱️  Clicking sync button...")
            await sync_btn.click()

            # Wait for dialog or response
            print("\n⏳ Waiting for confirmation dialog or response...")
            await page.wait_for_timeout(3000)

            if dialog_appeared:
                print(f"✅ Dialog appeared with message: {dialog_message}")
            else:
                print("\n❌ No confirmation dialog appeared!")
                print("This means the JavaScript validation is failing.")
                print("\n🔍 Checking for JavaScript errors in console...")

            # Wait a bit more to see any network activity
            print("\n⏳ Waiting for any network activity...")
            await page.wait_for_timeout(3000)

            print("\n✅ Test completed. Check the output above for issues.")

        except Exception as e:
            print(f"\n❌ Error during test: {e}")
            import traceback
            traceback.print_exc()

        finally:
            print("\n🔚 Closing browser in 5 seconds...")
            await page.wait_for_timeout(5000)
            await browser.close()

if __name__ == "__main__":
    print("🧪 Starting sync button test with Playwright...")
    print("=" * 60)

    # First install playwright browsers if needed
    import subprocess
    print("📦 Ensuring Playwright browsers are installed...")
    try:
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"],
                      check=True, capture_output=True)
        print("✅ Playwright browsers ready")
    except Exception as e:
        print(f"⚠️  Could not install browsers: {e}")
        print("Continuing anyway...")

    asyncio.run(test_sync_button())
