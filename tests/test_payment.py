"""
tests/test_payment.py
---------------------
End-to-end Playwright + Pytest automation suite for Indian (INR) payment workflows
using Razorpay Checkout v2 (Test Mode).

Covers multiple payment methods across Desktop and Mobile Web viewports:
  1. Card (Mastercard) — Desktop Web — ₹50 INR -> OTP 2FA -> Verified
  2. Netbanking (Bank of Baroda) — Desktop Web — ₹499 INR -> Bank 2FA -> Verified
  3. Wallet (Mobikwik) — Desktop Web — ₹50 INR -> Wallet OTP 2FA -> Verified
  4. Card (Visa) — Mobile Web (Pixel 7 Touch Viewport) — ₹1,499 INR -> OTP 2FA -> Verified
"""

import os
from dotenv import load_dotenv
from pages.payment_page import PaymentPage

load_dotenv()

# Official Razorpay India Test Mode cards (zero real money charged)
TEST_MASTERCARD = "5555510000081006"
TEST_MASTERCARD_PREPAID = "5180287200091001"
TEST_EXPIRY = "12/29"
TEST_CVV = "123"


def _get_test_config() -> tuple[str, str, str]:
    mobile = os.getenv("TEST_MOBILE_NUMBER", "").strip()
    assert mobile, "TEST_MOBILE_NUMBER is missing or empty in .env"
    email = os.getenv("TEST_EMAIL", "testuser@example.com").strip()
    otp = os.getenv("TEST_OTP", "1234").strip()
    return mobile, email, otp


def test_card_payment_desktop_inr(flask_server, desktop_page, manual_otp):
    """Desktop Web: Card (Mastercard) payment in INR -> OTP 2FA -> Backend Verified."""
    mobile, email, otp = _get_test_config()
    payment = PaymentPage(
        desktop_page,
        base_url=flask_server,
        flow_name="01_card_desktop",
        is_mobile=False,
    )

    payment.open_website(product_id="starter")
    payment.assert_website_loaded(expected_amount_text="₹50")
    payment.click_pay_button()
    payment.enter_mobile_number(mobile)
    payment.pay_with_card(
        card_number=TEST_MASTERCARD,
        expiry=TEST_EXPIRY,
        cvv=TEST_CVV,
        email=email,
    )
    payment.handle_2fa_screen(otp=otp, manual=manual_otp)
    receipt = payment.assert_payment_verified()
    assert receipt["currency"] == "INR"


def test_netbanking_payment_desktop_inr(flask_server, desktop_page, manual_otp):
    """Desktop Web: Netbanking (Bank of Baroda) in INR -> Bank 2FA -> Backend Verified."""
    mobile, email, _ = _get_test_config()
    payment = PaymentPage(
        desktop_page,
        base_url=flask_server,
        flow_name="02_netbanking_desktop",
        is_mobile=False,
    )

    payment.open_website(product_id="pro")
    payment.assert_website_loaded(expected_amount_text="₹499")
    payment.click_pay_button()
    payment.enter_mobile_number(mobile)
    bank_popup = payment.pay_with_netbanking(bank_name="Bank of Baroda", email=email)
    payment.handle_2fa_screen(popup_page=bank_popup, manual=manual_otp)
    receipt = payment.assert_payment_verified()
    assert receipt["currency"] == "INR"


def test_wallet_payment_desktop_inr(flask_server, desktop_page, manual_otp):
    """Desktop Web: Wallet (Mobikwik) in INR -> Wallet OTP 2FA -> Backend Verified."""
    mobile, email, otp = _get_test_config()
    payment = PaymentPage(
        desktop_page,
        base_url=flask_server,
        flow_name="03_wallet_desktop",
        is_mobile=False,
    )

    payment.open_website(product_id="starter")
    payment.assert_website_loaded(expected_amount_text="₹50")
    payment.click_pay_button()
    payment.enter_mobile_number(mobile)
    payment.pay_with_wallet(wallet_name="Mobikwik", email=email)
    payment.handle_2fa_screen(otp=otp, manual=manual_otp)
    receipt = payment.assert_payment_verified()
    assert receipt["currency"] == "INR"


def test_card_payment_mobile_web_inr(flask_server, mobile_page, manual_otp):
    """Mobile Web (560x960 touch): Card (Mastercard Prepaid) in INR -> OTP 2FA -> Backend Verified."""
    mobile, email, otp = _get_test_config()
    payment = PaymentPage(
        mobile_page,
        base_url=flask_server,
        flow_name="04_card_mobile_web",
        is_mobile=True,
    )

    payment.open_website(product_id="enterprise")
    payment.assert_website_loaded(expected_amount_text="₹1,499")
    payment.click_pay_button()
    payment.enter_mobile_number(mobile)
    payment.pay_with_card(
        card_number=TEST_MASTERCARD_PREPAID,
        expiry=TEST_EXPIRY,
        cvv="456",
        email=email,
    )
    payment.handle_2fa_screen(otp=otp, manual=manual_otp)
    receipt = payment.assert_payment_verified()
    assert receipt["currency"] == "INR"
