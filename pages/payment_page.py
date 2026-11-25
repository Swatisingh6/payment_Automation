"""
pages/payment_page.py
---------------------
Page Object Model for the Indian Payment Automation storefront (Flask + INR)
and the Razorpay Checkout v2 overlay (Desktop & Mobile Web).

Supported India payment methods:
  - Card (Mastercard / Visa / RuPay) -> OTP 2FA inside Checkout
  - Netbanking (Indian Banks, e.g. Bank of Baroda / Canara / HDFC) -> Bank 2FA popup
  - Wallet (Mobikwik / Airtel Payments Bank) -> Email + OTP 2FA inside Checkout
"""

import os
import time
from typing import Optional
from playwright.sync_api import Page, FrameLocator, TimeoutError as PWTimeout

SCREENSHOTS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "screenshots")
)


class PaymentPage:
    """Encapsulates merchant storefront and Razorpay Checkout v2 interactions."""

    # Storefront selectors
    PRODUCT_SELECT_SEL = "#productSelect"
    DISPLAY_AMOUNT_SEL = "#displayAmount"
    PAY_BUTTON_SEL = "#payButton"
    MESSAGE_SEL = "#message"
    RECEIPT_SEL = "#paymentReceipt"
    RECEIPT_PAYMENT_ID_SEL = "#receiptPaymentId"
    RECEIPT_ORDER_ID_SEL = "#receiptOrderId"

    # Razorpay Checkout iframe
    CHECKOUT_IFRAME_SEL = "iframe.razorpay-checkout-frame"

    # Mobile entry screen
    MOBILE_INPUT_SEL = 'input[name="contact"]'
    MOBILE_CONTINUE_SEL = 'button.btn-block'

    # Card inputs (dot notation verified against live Razorpay Checkout v2 DOM)
    CARD_NUMBER_SEL = 'input[name="card.number"]'
    CARD_EXPIRY_SEL = 'input[name="card.expiry"]'
    CARD_CVV_SEL = 'input[name="card.cvv"]'
    CARD_NAME_SEL = 'input[name="card.name"], input[placeholder*="name" i]'

    # Email / OTP / Action buttons inside Checkout
    EMAIL_INPUT_SEL = 'input[name="email"], input[placeholder*="Email" i]'
    OTP_INPUT_SEL = 'input[name="otp"], input[placeholder*="OTP" i]'
    CONTINUE_BTN_SEL = 'button:has-text("Continue")'
    MAYBE_LATER_BTN_SEL = 'button:has-text("Maybe later")'
    BANK_SEARCH_SEL = 'input[name="bank"]'

    def __init__(
        self,
        page: Page,
        base_url: str = "http://127.0.0.1:5001",
        flow_name: str = "payment",
        is_mobile: bool = False,
    ):
        self.page = page
        self.base_url = base_url
        self.flow_name = flow_name
        self.is_mobile = is_mobile

    def save_screenshot(self, stage: str, target_page: Optional[Page] = None) -> None:
        """Save a stage screenshot in screenshots/<flow_name>_<stage>.png."""
        os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
        filename = f"{self.flow_name}_{stage}.png"
        path = os.path.join(SCREENSHOTS_DIR, filename)
        pg = target_page or self.page
        pg.screenshot(path=path, full_page=not self.is_mobile)
        print(f"  📸 Screenshot saved → screenshots/{filename}")

    def _checkout(self) -> FrameLocator:
        return self.page.frame_locator(self.CHECKOUT_IFRAME_SEL)

    def _fill_optional(self, checkout: FrameLocator, selector: str, value: Optional[str]) -> None:
        if not value:
            return
        loc = checkout.locator(selector)
        try:
            if loc.count() > 0 and loc.first.is_visible():
                loc.first.fill(value)
        except Exception:
            pass

    def _click_continue(self, checkout: FrameLocator, timeout: int = 10_000) -> None:
        btn = checkout.locator(self.CONTINUE_BTN_SEL).last
        btn.wait_for(state="visible", timeout=timeout)
        try:
            btn.click(timeout=5_000)
        except Exception:
            # On mobile viewports Razorpay's sticky footer CTA inside the iframe
            # can sit beyond the host viewport height; trigger click directly.
            btn.evaluate("el => { el.scrollIntoView({block: 'center'}); el.click(); }")

    # ── Stage 1: Open Indian INR storefront ────────────────────────────
    def open_website(self, product_id: str = "starter") -> None:
        """Navigate to the local Flask storefront for the chosen INR product."""
        url = f"{self.base_url}/?product={product_id}"
        print(f"\n🌐 Opening storefront: {url}")
        self.page.goto(url, wait_until="networkidle")
        self.save_screenshot("01_website_opened")

    def assert_website_loaded(self, expected_amount_text: str = "₹") -> None:
        """Verify the storefront loaded with Indian Rupee (₹) pricing."""
        assert "India" in self.page.title() and "INR" in self.page.title(), (
            f"Unexpected page title: {self.page.title()!r}"
        )
        amount_txt = self.page.locator(self.DISPLAY_AMOUNT_SEL).inner_text().strip()
        assert expected_amount_text in amount_txt, (
            f"Expected {expected_amount_text!r} in amount, got {amount_txt!r}"
        )
        pay_btn = self.page.locator(self.PAY_BUTTON_SEL)
        assert pay_btn.is_visible() and pay_btn.is_enabled(), "Pay Now button not ready."
        print(f"  ✅ Stage 1 passed: Storefront loaded ({amount_txt} INR).")

    # ── Stage 2: Launch Razorpay Checkout ──────────────────────────────
    def click_pay_button(self) -> FrameLocator:
        """Click Pay Now and wait for the Razorpay Checkout iframe to attach."""
        print("🖱️  Clicking Pay Now …")
        self.page.locator(self.PAY_BUTTON_SEL).click()
        iframe_loc = self.page.locator(self.CHECKOUT_IFRAME_SEL)
        iframe_loc.wait_for(state="attached", timeout=30_000)

        checkout = self._checkout()
        # Wait until contact input or payment options appear inside checkout
        checkout.locator(self.MOBILE_INPUT_SEL).wait_for(state="visible", timeout=30_000)
        self.save_screenshot("02_checkout_opened")
        print("  ✅ Stage 2 passed: Razorpay Checkout opened (INR).")
        return checkout

    # ── Stage 3: Enter Indian mobile number (+91) ──────────────────────
    def enter_mobile_number(self, mobile: str) -> FrameLocator:
        """
        Enter the 10-digit Indian mobile number.
        On mobile viewports Razorpay may auto-advance directly to Payment Options;
        on desktop we click Continue if still on the contact screen.
        """
        print(f"📱 Entering +91 mobile number ({mobile[-4:].rjust(10, '*')}) …")
        checkout = self._checkout()
        mobile_field = checkout.locator(self.MOBILE_INPUT_SEL)
        mobile_field.wait_for(state="visible", timeout=20_000)
        mobile_field.click()
        mobile_field.fill(mobile)
        self.save_screenshot("03_mobile_entered")

        # Give Razorpay a moment to either auto-advance (mobile) or stay on Continue (desktop)
        self.page.wait_for_timeout(800)

        options_visible = False
        for probe in (self.CARD_NUMBER_SEL, 'text="All Payment Options"', 'text="Cards"'):
            try:
                loc = checkout.locator(probe)
                if loc.count() > 0 and loc.first.is_visible():
                    options_visible = True
                    break
            except Exception:
                pass

        if not options_visible:
            btn = checkout.locator(self.MOBILE_CONTINUE_SEL).last
            try:
                btn.wait_for(state="visible", timeout=5_000)
                btn.click()
            except Exception:
                self._click_continue(checkout, timeout=10_000)

        print("  ✅ Stage 3 passed: Contact step completed.")
        return checkout

    # ── Payment Method 1: Credit / Debit Card ──────────────────────────
    def pay_with_card(
        self,
        card_number: str,
        expiry: str,
        cvv: str,
        cardholder_name: str = "Test User",
        email: str = "testuser@example.com",
    ) -> FrameLocator:
        """Fill Indian test card details and advance to the Card OTP / 3DS 2FA screen."""
        checkout = self._checkout()

        # On mobile layout, Payment Options lists "Cards" as an expandable/navigable item
        card_input = checkout.locator(self.CARD_NUMBER_SEL)
        if card_input.count() == 0 or not card_input.first.is_visible():
            cards_tab = checkout.get_by_text("Cards", exact=True).first
            cards_tab.wait_for(state="visible", timeout=15_000)
            cards_tab.click()

        card_input.wait_for(state="visible", timeout=20_000)
        print("💳 Entering card details …")
        card_input.click()
        card_input.press_sequentially(card_number, delay=25)

        expiry_field = checkout.locator(self.CARD_EXPIRY_SEL)
        expiry_field.wait_for(state="visible", timeout=10_000)
        expiry_field.click()
        expiry_field.press_sequentially(expiry.replace("/", ""), delay=25)

        cvv_field = checkout.locator(self.CARD_CVV_SEL)
        cvv_field.wait_for(state="visible", timeout=10_000)
        cvv_field.click()
        cvv_field.press_sequentially(cvv, delay=25)

        # Fill optional Name / Email if Razorpay prompts for them
        self._fill_optional(checkout, self.CARD_NAME_SEL, cardholder_name)
        self._fill_optional(checkout, self.EMAIL_INPUT_SEL, email)

        self.save_screenshot("04_card_details_entered")
        self._click_continue(checkout)

        # Dismiss RBI card tokenization consent modal if shown
        maybe_later = checkout.locator(self.MAYBE_LATER_BTN_SEL)
        try:
            maybe_later.wait_for(state="visible", timeout=6_000)
            maybe_later.click()
            print("  ℹ️ Dismissed RBI save-card prompt ('Maybe later').")
        except PWTimeout:
            pass

        print("  ✅ Stage 4 passed: Card details submitted.")
        return checkout

    # ── Payment Method 2: Netbanking (India) ───────────────────────────
    def pay_with_netbanking(
        self,
        bank_name: str = "Bank of Baroda",
        email: str = "testuser@example.com",
    ) -> Page:
        """
        Select Netbanking, pick an Indian bank, and return the Razorpay
        Demo Bank 2FA popup Page.
        """
        checkout = self._checkout()
        print(f"🏦 Selecting Netbanking ({bank_name}) …")
        nb_tab = checkout.get_by_text("Netbanking", exact=True).first
        nb_tab.wait_for(state="visible", timeout=15_000)
        nb_tab.click()

        bank_item = checkout.get_by_text(bank_name, exact=False).first
        try:
            bank_item.wait_for(state="visible", timeout=6_000)
        except PWTimeout:
            search_box = checkout.locator(self.BANK_SEARCH_SEL)
            search_box.wait_for(state="visible", timeout=10_000)
            search_box.fill(bank_name)
            bank_item.wait_for(state="visible", timeout=10_000)

        self.save_screenshot("04_netbanking_selected")

        with self.page.context.expect_page(timeout=20_000) as popup_info:
            bank_item.click()
            # Some sessions prompt for email before opening the bank popup
            email_inp = checkout.locator(self.EMAIL_INPUT_SEL)
            try:
                email_inp.wait_for(state="visible", timeout=2_500)
                email_inp.fill(email)
                self._click_continue(checkout)
            except PWTimeout:
                pass

        popup = popup_info.value
        popup.wait_for_load_state("domcontentloaded")
        print("  ✅ Stage 4 passed: Bank 2FA popup opened.")
        return popup

    # ── Payment Method 3: Indian Wallet (Mobikwik / Airtel) ────────────
    def pay_with_wallet(
        self,
        wallet_name: str = "Mobikwik",
        email: str = "testuser@example.com",
    ) -> FrameLocator:
        """Select an Indian Wallet and submit email if prompted to reach Wallet OTP."""
        checkout = self._checkout()
        print(f"👛 Selecting Wallet ({wallet_name}) …")
        wallet_tab = checkout.get_by_text("Wallet", exact=True).first
        wallet_tab.wait_for(state="visible", timeout=15_000)
        wallet_tab.click()

        wallet_item = checkout.get_by_text(wallet_name, exact=False).first
        wallet_item.wait_for(state="visible", timeout=10_000)
        self.save_screenshot("04_wallet_selected")
        wallet_item.click()

        email_inp = checkout.locator(self.EMAIL_INPUT_SEL)
        try:
            email_inp.wait_for(state="visible", timeout=5_000)
            email_inp.fill(email)
            self._click_continue(checkout)
        except PWTimeout:
            pass

        print("  ✅ Stage 4 passed: Wallet selected.")
        return checkout

    # ── Stage 5 & 6: Reach 2FA Screen & Complete Authentication ──────────
    def handle_2fa_screen(
        self,
        otp: str = "1234",
        popup_page: Optional[Page] = None,
        manual: bool = False,
    ) -> None:
        """
        Wait for the 2FA screen (OTP modal or Bank Auth popup), capture a
        screenshot at the 2FA gate, and complete authentication automatically
        (unless manual=True, in which case Playwright Inspector pauses).
        """
        print("🔐 Waiting for 2FA / OTP authentication screen …")

        if popup_page is not None:
            success_btn = popup_page.locator('button:has-text("Success")')
            success_btn.wait_for(state="visible", timeout=20_000)
            self.save_screenshot("05_2fa_bank_auth", target_page=popup_page)
            print("  ✅ 2FA Bank Authentication page reached.")

            if manual:
                print("⏸  PAUSED at Bank 2FA page — click Success manually, then Resume.")
                popup_page.pause()
            else:
                success_btn.click()
                print("  ✅ Automated 2FA: Clicked 'Success' on Demo Bank page.")
            return

        # In-iframe OTP screen (Cards & Wallets)
        checkout = self._checkout()
        otp_input = checkout.locator(self.OTP_INPUT_SEL).first
        otp_input.wait_for(state="visible", timeout=25_000)
        self.save_screenshot("05_2fa_otp_screen")
        print("  ✅ 2FA OTP screen reached.")

        if manual:
            print("⏸  PAUSED at OTP screen — complete OTP in browser, then Resume.")
            self.page.pause()
        else:
            otp_input.fill(otp)
            self.save_screenshot("06_otp_entered")
            self._click_continue(checkout)
            print(f"  ✅ Automated 2FA: Entered test OTP ({otp}) and submitted.")

    # ── Stage 7: Verify Backend Signature & Receipt ────────────────────
    def assert_payment_verified(self, timeout_seconds: int = 25) -> dict:
        """Wait for Razorpay handler -> Flask /verify-payment and assert receipt."""
        print("🔍 Verifying payment signature via Flask backend …")
        deadline = time.time() + timeout_seconds
        msg_text = ""

        while time.time() < deadline:
            msg_text = self.page.locator(self.MESSAGE_SEL).inner_text().strip()
            if "verified" in msg_text.lower():
                break
            if "failed" in msg_text.lower():
                pytest_fail_msg = f"Payment failed on UI: {msg_text!r}"
                self.save_screenshot("07_payment_failed")
                raise AssertionError(pytest_fail_msg)
            time.sleep(0.4)

        assert "verified" in msg_text.lower(), (
            f"Timed out waiting for verified payment message; got: {msg_text!r}"
        )

        receipt = self.page.locator(self.RECEIPT_SEL)
        receipt.wait_for(state="visible", timeout=5_000)
        payment_id = self.page.locator(self.RECEIPT_PAYMENT_ID_SEL).inner_text().strip()
        order_id = self.page.locator(self.RECEIPT_ORDER_ID_SEL).inner_text().strip()

        assert payment_id.startswith("pay_"), f"Unexpected payment ID: {payment_id!r}"
        assert order_id.startswith("order_"), f"Unexpected order ID: {order_id!r}"

        self.save_screenshot("07_payment_verified")
        print(
            f"  ✅ Stage 7 passed: {msg_text} | "
            f"Payment ID={payment_id} | Order ID={order_id} | Currency=INR"
        )
        return {
            "message": msg_text,
            "payment_id": payment_id,
            "order_id": order_id,
            "currency": "INR",
        }
