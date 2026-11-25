"""
conftest.py
-----------
Pytest fixtures and CLI options for the India Payment Automation suite.

CLI options:
  --headless    Run Chromium in headless mode (default: False / headed).
  --manual-otp  Pause at the 2FA / OTP screen for manual completion
                instead of automating the Razorpay Test Mode 2FA step.

Fixtures:
  flask_server  Starts the Flask merchant app in a daemon thread (INR).
  desktop_page  Yields a desktop Chromium Page (1280x800) with video recording.
  mobile_page   Yields a mobile-emulated Chromium Page (412x915, touch) with video recording.
  manual_otp    Boolean flag from --manual-otp.
"""

import os
import sys
import time
import shutil
import threading
import requests
import pytest

PROJECT_ROOT = os.path.dirname(__file__)
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()

FLASK_HOST = "127.0.0.1"
FLASK_PORT = 5001
BASE_URL = f"http://{FLASK_HOST}:{FLASK_PORT}"
VIDEOS_DIR = os.path.join(PROJECT_ROOT, "videos")
SCREENSHOTS_DIR = os.path.join(PROJECT_ROOT, "screenshots")

MOBILE_UA = (
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Mobile Safari/537.36"
)


def pytest_addoption(parser):
    parser.addoption(
        "--headless",
        action="store_true",
        default=False,
        help="Run Playwright Chromium in headless mode.",
    )
    parser.addoption(
        "--manual-otp",
        action="store_true",
        default=False,
        help="Pause at the 2FA/OTP screen instead of automating it.",
    )


@pytest.fixture(scope="session")
def manual_otp(request) -> bool:
    return bool(request.config.getoption("--manual-otp"))


@pytest.fixture(scope="session", autouse=True)
def flask_server():
    """Start the local Flask INR merchant app in a background daemon thread."""
    import app as flask_app

    flask_app.app.config["TESTING"] = True

    server_thread = threading.Thread(
        target=lambda: flask_app.app.run(
            host=FLASK_HOST,
            port=FLASK_PORT,
            debug=False,
            use_reloader=False,
        ),
        daemon=True,
    )
    server_thread.start()

    deadline = time.time() + 10
    while time.time() < deadline:
        try:
            resp = requests.get(BASE_URL, timeout=1)
            if resp.status_code == 200:
                break
        except requests.ConnectionError:
            time.sleep(0.3)
    else:
        pytest.fail(f"Flask server did not start at {BASE_URL} within 10 seconds.")

    yield BASE_URL


def _launch_recorded_page(request, context_kwargs: dict):
    """Launch Chromium, record video for the test, and save it under a deterministic name."""
    os.makedirs(VIDEOS_DIR, exist_ok=True)
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

    headless = bool(request.config.getoption("--headless"))
    test_name = request.node.name

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=headless,
            slow_mo=120,
        )
        context = browser.new_context(
            record_video_dir=VIDEOS_DIR,
            **context_kwargs,
        )
        page = context.new_page()

        yield page

        video = page.video
        try:
            page.close()
        except Exception:
            pass
        context.close()
        browser.close()

        # Rename Playwright's UUID video file to <test_name>.webm
        if video is not None:
            try:
                raw_path = video.path()
                target_path = os.path.join(VIDEOS_DIR, f"{test_name}.webm")
                if os.path.exists(raw_path):
                    if os.path.exists(target_path):
                        os.remove(target_path)
                    shutil.move(raw_path, target_path)
                    print(f"  🎥 Video saved → videos/{test_name}.webm")
            except Exception as exc:
                print(f"  ⚠️ Could not rename video for {test_name}: {exc}")


@pytest.fixture(scope="function")
def desktop_page(request):
    """Desktop Chromium Page (1280x800) with video recording."""
    yield from _launch_recorded_page(
        request,
        {
            "viewport": {"width": 1280, "height": 800},
            "record_video_size": {"width": 1280, "height": 800},
        },
    )


@pytest.fixture(scope="function")
def mobile_page(request):
    """Mobile Web Chromium Page (560x960, touch enabled, Pixel 7 UA) with video recording."""
    yield from _launch_recorded_page(
        request,
        {
            "viewport": {"width": 560, "height": 960},
            "record_video_size": {"width": 560, "height": 960},
            "has_touch": True,
            "is_mobile": False,
            "user_agent": MOBILE_UA,
        },
    )
