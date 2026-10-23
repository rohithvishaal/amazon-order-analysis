# 📦 Amazon Order Analytics & Intelligence Dashboard

A modern, offline analytical suite to visualize and explore your complete Amazon purchase history in a rich, interactive dashboard. **100% private & local — runs entirely on Python's built-in standard library with zero external pip dependencies. Your personal data never leaves your computer.**

---

## 📸 Preview

![Amazon Order Analytics Dashboard](docs/screenshots/dashboard_overview.png)

---

## ⚡ 1. Quick Start (Zero-Setup Point & Click)

The launchers are **self-bootstrapping**: as long as Python 3.10+ is installed on your computer, the launcher **automatically sets up a virtual environment, validates offline assets, processes your orders, and opens the dashboard in your browser**.

* **On Mac**: Double-click **`Run_Dashboard.command`** in Finder.
* **On Windows**: Double-click **`run.bat`** in File Explorer.
* **On Linux / Mac Terminal**: Run **`./run.sh`**.

The launcher will automatically start a local server and open your default browser at:
👉 **`http://localhost:8000/dashboard.html`**

*(To test it right away without your own data, the app includes a preloaded sample dataset in `sample_data/`.)*

---

## ⚙️ Prerequisites & Zero-Dependency Architecture

### System Requirements
| Requirement | Supported Version | Purpose | How to Install |
| :--- | :--- | :--- | :--- |
| **Python** | **3.10 or newer** *(Python 3.10 – 3.14)* | Runtime engine | [Download from python.org](https://www.python.org/downloads/) *(On Windows, tick "Add Python to PATH")* |
| **Dependencies** | **None (0 external packages)** | Complete data ingestion & analytics | Runs 100% on Python's standard library (`csv`, `collections`, `datetime`, `json`) |
| **Astral `uv`** *(Optional)* | Any version | Instant virtual environment isolation | **Handled automatically by the run scripts!** |
| **Web Browser** | Any modern browser | Renders the interactive dashboard UI | Chrome, Brave, Edge, Firefox, or Safari |

### Automated Bootstrap Workflow
When you double-click any launcher (`Run_Dashboard.command`, `run.bat`, or `run.sh`), the script automatically:
1. **Checks for Python 3.10+**: Verifies your system has a compatible Python version installed. If missing, it provides direct download instructions.
2. **Initializes Virtual Environment**: Automatically runs `uv venv .venv` (or fallback) for clean isolation.
3. **Validates Offline Assets**: Ensures local `Chart.js` is cached for standalone offline graphing without CDN reliance.
4. **Processes Orders & Launches Server**: Parses and harmonizes all order files, generates `dashboard.html` and `amazon_orders_master.json`, and launches the interactive dashboard.

---

## 📥 2. How to Get Your Amazon Data

To visualize your own real Amazon order history, follow these 3 simple steps:

### Step A: Request your data from Amazon
1. Log in to your Amazon account.
2. Go to **Your Account** &rarr; scroll to **Data and Privacy** &rarr; click **Request Your Information** (or visit [amazon.in/privacy/data-request](https://www.amazon.in/privacy/data-request) / [amazon.com/hz/privacy-central/data-requests/preview.html](https://www.amazon.com/hz/privacy-central/data-requests/preview.html)).
3. Under *"Select the data you want to request"*, choose **Your Orders**.
4. Click **Submit Request**.

### Step B: Download the archive
* Amazon will email you when your archive is ready (usually takes between 30 minutes to a few hours).
* Click the download link in the email to download the `.zip` file.

### Step C: Place it in the folder
1. Extract / unzip the downloaded archive.
2. Move the extracted folder into this project and name it **`Your Orders`**:
   ```
   amazon_order_analysis/
   ├── Your Orders/                <--- 📂 Place your extracted Amazon data here!
   │   ├── Your Amazon Orders/
   │   │   ├── Order History.csv
   │   │   └── Digital Content Orders.csv
   │   └── Your Returns & Refunds/
   │       └── Returns Status.csv
   ├── Run_Dashboard.command       <--- Double-click to launch on Mac!
   ├── run.bat                     <--- Double-click to launch on Windows!
   └── run.sh                      <--- Run in Linux/Mac terminal!
   ```
3. Double-click **`Run_Dashboard.command`** (Mac) or **`run.bat`** (Windows) to instantly generate your dashboard!

---

## 🛠️ 3. Command-Line Options (For Developers)

If you prefer running commands manually in your terminal:

```bash
# 1. Initialize virtual environment using uv:
uv venv .venv
source .venv/bin/activate    # On Windows: .venv\Scripts\activate

# 2. Ensure Chart.js is cached locally for offline use (one time):
python -m src.chartjs

# 3. Generate dashboard and start local web server:
python main.py --serve

# 4. Run on a custom folder:
python main.py --data-dir /path/to/orders/

# 5. Run with demo sample data:
python main.py --data-dir sample_data/

# 6. Inspect details of a specific Order ID:
python main.py --inspect "408-1234567-8901234"

# 7. Run automated test suite:
python -m unittest discover tests
```

---

## ✨ Features & Capabilities

* **Zero External Dependencies**: Pure Python standard-library implementation. No bulky dependencies, no version conflicts, instant startup.
* **Unified Order Harmonization**: Seamlessly unifies physical shipments, prepaid mobile recharges, electricity & utility payments, Prime subscriptions, and digital media into a single relational dataset.
* **Realized vs. Gross Spend**: Accurately accounts for order cancellations, returns, replacements, and cash refunds so your financial metrics reflect actual net expenditure.
* **Interactive Click-to-Filter Navigation**: Click on any chart element (annual waterfall bar, category slice, carrier, peak month, or utility row) to immediately filter and jump to those exact orders in the Master Ledger.
* **Deep Multi-Column Ledger Filtering**: Filter orders by Date range, Order ID, item keywords, categories, payment types, delivery status, and price tiers with instant chip management.
* **Longitudinal Strategic Insights**: Dynamically calculated observations across purchasing rhythms, active shopping days, day-of-week and time-of-day purchase heat patterns, and geographic delivery timelines.
* **Complete Offline Privacy**: Built as a self-contained local application. None of your order details, amounts, or personal addresses ever leave your local machine.
