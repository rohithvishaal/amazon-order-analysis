# 📦 Amazon Order Analytics & Intelligence Dashboard

A modern, offline analytical tool to visualize and explore your complete Amazon purchase history in a rich, interactive dashboard. **100% private & local — your personal data never leaves your computer.**

---

## 📸 Preview

![Amazon Order Analytics Dashboard](docs/screenshots/dashboard_overview.png)

---

## ⚡ 1. Quick Start (Zero-Setup Point & Click)

The launchers are **self-bootstrapping**: as long as Python 3.10+ is installed on your computer, the launcher **automatically installs `uv` (if not already present), creates a virtual environment, installs dependencies, and opens the dashboard**.

* **On Mac**: Double-click **`Run_Dashboard.command`** in Finder.
* **On Windows**: Double-click **`run.bat`** in File Explorer.
* **On Linux / Mac Terminal**: Run **`./run.sh`**.

The launcher will automatically open your default browser at:
👉 **`http://localhost:8000/dashboard.html`**

*(To test it right away without your own data, the app includes a preloaded sample dataset in `sample_data/`.)*

---

## ⚙️ Prerequisites & Automated Setup

### System Requirements
| Requirement | Supported Version | Purpose | How to Install |
| :--- | :--- | :--- | :--- |
| **Python** | **3.10 or newer** *(Python 3.10 – 3.13)* | Runtime engine | [Download from python.org](https://www.python.org/downloads/) *(On Windows, check "Add Python to PATH")* |
| **Astral `uv`** *(Auto-installed)* | Any version | Ultra-fast package & venv manager | **Handled automatically by the run scripts!** |
| **Web Browser** | Any modern browser | Renders the dashboard UI | Chrome, Brave, Edge, Firefox, or Safari |

### Automated Bootstrap Workflow
When you double-click any launcher (`Run_Dashboard.command`, `run.bat`, or `run.sh`), the script automatically performs the following checks:
1. **Checks for Python 3.10+**: Verifies your system has a compatible Python version installed. If missing, it alerts you with direct download links.
2. **Installs `uv`**: If `uv` is not found on your system, the script installs Astral `uv` automatically.
3. **Initializes Virtual Environment**: Automatically runs `uv venv .venv` to ensure clean, isolated execution.
4. **Installs Project Dependencies**: Installs and syncs required analytics libraries (`duckdb>=1.0.0`, `pandas>=2.0.0`, `python-dateutil`).
5. **Processes Orders & Launches Server**: Runs the pipeline and opens your web browser to the interactive dashboard.

---

## 📥 2. How to Get Your Amazon Data

To visualize your own real Amazon order history, follow these 3 steps:

### Step A: Request your data from Amazon
1. Log in to your Amazon account.
2. Go to **Your Account** &rarr; scroll to **Data and Privacy** &rarr; click **Request Your Information** (or visit [amazon.in/privacy/data-request](https://www.amazon.in/privacy/data-request)).
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
3. Double-click **`Run_Dashboard.command`** (Mac) or **`run.bat`** (Windows) to instantly update your dashboard!

---

## 🛠️ 3. Command-Line Options (For Developers)

If you prefer running commands manually in your terminal:

```bash
# 1. Initialize environment & install dependencies using uv:
uv venv .venv
source .venv/bin/activate    # On Windows: .venv\Scripts\activate
uv pip install "duckdb>=1.0.0" "pandas>=2.0.0" "python-dateutil"
python -m src.chartjs
# 2. Generate dashboard and start local web server:
python main.py --serve

# 3. Run on a custom folder:
python main.py --data-dir /path/to/orders/

# 4. Run with demo fake data:
python main.py --data-dir sample_data/

# 5. Inspect details of a specific Order ID:
python main.py --inspect "408-1234567-8901234"

# 6. Run automated test suite:
python -m unittest discover tests
```

---

## ✨ Features

* **Zero-Setup Bootstrapping**: Automatically manages `uv`, virtual environments, and package installations seamlessly.
* **Interactive Graph Filtering**: Click on any bar or pie slice (year, category, weekday, status) to instantly filter the orders table to that specific group.
* **Column Filters & Sorting**: Search by Order ID, item keyword, price tier, or delivery status directly from table headers.
* **Accurate Returns & Refunds Accounting**: Realized spend automatically excludes cancelled orders and subtracts refunded returns.
* **Universal Portability**: Automatically recognizes Amazon addresses and cities across India, the US, and internationally without hardcoding.
