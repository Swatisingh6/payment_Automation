# 🇮🇳 India Payment Automation Framework (INR)

> **Automation Challenge — Multi-Method Payment Workflow**  
> End-to-end automated Indian payment flows (**INR / ₹**) using **Flask + Razorpay Checkout v2 (Test Mode) + Playwright + Pytest (Page Object Model)** across **Desktop Web** and **Mobile Web**.

---

## 🎯 Challenge Objectives Covered

- **Live Payment Gateway Journey (India / INR):** Automates real Razorpay Checkout v2 flows in Test Mode with Indian Rupee (`₹` / `INR`) orders and `+91` mobile verification.
- **Multiple Payment Methods Automated:**
  1. **Credit / Debit Card (Mastercard Business)** — Desktop Web (`₹50 INR`)
  2. **Netbanking (Bank of Baroda)** — Desktop Web (`₹499 INR`)
  3. **Digital Wallet (Mobikwik)** — Desktop Web (`₹50 INR`)
  4. **Credit / Debit Card (Mastercard Prepaid)** — Mobile Web Touch Viewport `560x960` (`₹1,499 INR`)
- **Target & Bonus Points Achieved:**
  - Reaches the **Second-Factor Authentication (2FA) / OTP / Bank Auth** screen and captures stage screenshots + full `.webm` video recordings.
  - **Automates the 2FA / OTP & Demo Bank screen** (`1234` OTP / `Success` bank approval) and verifies the Razorpay cryptographic payment signature server-side via Flask (`/verify-payment`).
  - Optional `--manual-otp` flag is also supported if a tester wants to pause at the 2FA screen and enter OTP manually.
- **Framework Architecture:** Pytest + Playwright + Page Object Model (`pages/payment_page.py`) with isolated test fixtures (`conftest.py`), deterministic video recording, and stage-by-stage screenshots.

---

## 🗂️ Project Structure

```
payment_Automation/
├── app.py                   # Flask merchant backend (INR orders + Razorpay signature verification)
├── conftest.py              # Pytest fixtures (Flask server thread, desktop/mobile Playwright pages, video naming)
├── pytest.ini               # Pytest configuration
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variable template (India Test Mode)
├── .gitignore               # Excludes .env, venv, caches (keeps screenshots/ & videos/)
├── README.md                # Setup, execution, and deliverable documentation
│
├── pages/
│   ├── __init__.py
│   └── payment_page.py      # Page Object Model for storefront & Razorpay Checkout v2
│
├── tests/
│   └── test_payment.py      # End-to-end tests for Card, Netbanking, Wallet & Mobile Web (INR)
│
├── templates/
│   └── index.html           # Responsive INR (₹) storefront & receipt UI
│
├── screenshots/             # Stage-by-stage screenshots (including 2FA & verified receipt)
└── videos/                  # Full .webm video recordings of every automated flow
```

---

## 🧪 Automated Test Matrix

| Test Case | Platform / Viewport | Payment Method | Amount | 2FA Screen Automated | Recorded Video |
|---|---|---|---|---|---|
| `test_card_payment_desktop_inr` | Desktop (`1280x800`) | Card (Mastercard `5555 5100 0008 1006`) | `₹50 INR` | In-checkout OTP (`1234`) | [`videos/test_card_payment_desktop_inr.webm`](videos/test_card_payment_desktop_inr.webm) |
| `test_netbanking_payment_desktop_inr` | Desktop (`1280x800`) | Netbanking (`Bank of Baroda`) | `₹499 INR` | Demo Bank 2FA Popup (`Success`) | [`videos/test_netbanking_payment_desktop_inr.webm`](videos/test_netbanking_payment_desktop_inr.webm) |
| `test_wallet_payment_desktop_inr` | Desktop (`1280x800`) | Wallet (`Mobikwik`) | `₹50 INR` | Wallet OTP (`1234`) | [`videos/test_wallet_payment_desktop_inr.webm`](videos/test_wallet_payment_desktop_inr.webm) |
| `test_card_payment_mobile_web_inr` | Mobile Web (`560x960`, touch, Pixel 7 UA) | Card (Mastercard Prepaid `5180 2872 0009 1001`) | `₹1,499 INR` | In-checkout OTP (`1234`) | [`videos/test_card_payment_mobile_web_inr.webm`](videos/test_card_payment_mobile_web_inr.webm) |

---

## ⚙️ Setup & Re-running on a New System

### Prerequisites
- Python **3.10+** (tested on Python 3.14)
- Internet access (to reach Razorpay Checkout & Razorpay Test Mode APIs)
- Free [Razorpay Test Mode API Keys](https://dashboard.razorpay.com/app/keys) (`rzp_test_...`)

### 1. Clone the repository
```bash
git clone <your-github-repo-url>
cd payment_Automation
```

### 2. Create and activate a virtual environment
```bash
# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies & Chromium browser
```bash
pip install -r requirements.txt
playwright install chromium
```

### 4. Configure environment variables
Copy `.env.example` to `.env` and add your Razorpay **Test Mode** credentials:
```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Edit `.env`:
```env
RAZORPAY_KEY_ID=rzp_test_xxxxxxxxxxxx
RAZORPAY_KEY_SECRET=xxxxxxxxxxxxxxxxxxxxxxxx
TEST_MOBILE_NUMBER=9999999999
TEST_EMAIL=testuser@example.com
TEST_OTP=1234
```
> ⚠️ Use **Test Mode** keys (`rzp_test_...`) only. No real money is charged, and `.env` is excluded by `.gitignore`.

---

## ▶️ Running the Automation

### Run the full multi-method suite (headed browser + video recording)
```bash
pytest
```
`conftest.py` automatically launches the Flask INR server on `http://127.0.0.1:5001`, runs all 4 payment flows, saves stage screenshots in `screenshots/`, and saves named `.webm` recordings in `videos/`.

### Optional CLI flags
```bash
# Run headless (useful for CI environments)
pytest --headless

# Pause at the 2FA / OTP screen for manual entry instead of automated OTP
pytest --manual-otp

# Run a single payment method flow
pytest -k test_netbanking_payment_desktop_inr
```

---

## 📸 Captured Deliverables

- **Videos (`videos/`):**
  - `test_card_payment_desktop_inr.webm`
  - `test_netbanking_payment_desktop_inr.webm`
  - `test_wallet_payment_desktop_inr.webm`
  - `test_card_payment_mobile_web_inr.webm`
- **Stage Screenshots (`screenshots/`):**
  - Storefront (`01_website_opened`), Checkout (`02_checkout_opened`), Mobile entry (`03_mobile_entered`), Payment instrument (`04_*`), **2FA / OTP / Bank Auth gate (`05_2fa_*`)**, OTP submitted (`06_otp_entered`), and **Verified INR Payment Receipt (`07_payment_verified`)**.

---

## 🔒 Security & Test Data Notes

- `.env` is listed in `.gitignore` so API keys are never committed to GitHub.
- All transactions execute strictly in **Razorpay India Test Mode** using `INR (₹)` and official Razorpay test cards.
- Every successful test verifies `razorpay_order_id`, `razorpay_payment_id`, and `razorpay_signature` on the Flask backend before passing.

---

## 🐛 Troubleshooting

| Problem | Fix |
|---|---|
| `Flask server did not start` | Ensure port `5001` is free (`netstat -an \| findstr 5001`). |
| `Razorpay API keys are missing` | Verify `.env` exists in the project root with `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET`. |
| `Playwright executable doesn't exist` | Run `playwright install chromium`. |
| Card network warning in Test Mode | Switch between official Mastercard test cards (`5555510000081006` / `5180287200091001`) if a specific test card rail is under maintenance. |
