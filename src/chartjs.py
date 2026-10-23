"""Download Chart.js locally (once) so it can be inlined into dashboard.html.

No Node.js / npm needed. Run directly with:  python -m src.chartjs
"""

import io
import logging
import sys
import tarfile
import urllib.request
from pathlib import Path

logger = logging.getLogger("amazon_analytics")

CHART_JS_VERSION = "4.6.1"
WORKSPACE_DIR = Path(__file__).resolve().parent.parent
CHART_JS_PATH = (
    WORKSPACE_DIR / "node_modules" / "chart.js" / "dist" / "chart.umd.min.js"
)

CDN_URLS = [
    f"https://cdn.jsdelivr.net/npm/chart.js@{CHART_JS_VERSION}/dist/chart.umd.min.js",
    f"https://unpkg.com/chart.js@{CHART_JS_VERSION}/dist/chart.umd.min.js",
]
NPM_TARBALL_URL = (
    f"https://registry.npmjs.org/chart.js/-/chart.js-{CHART_JS_VERSION}.tgz"
)
MIN_SIZE = 10_000  # sanity check against error pages


def _is_present(path: Path) -> bool:
    return path.exists() and path.stat().st_size > MIN_SIZE


def ensure_chart_js(chart_js_path: Path = CHART_JS_PATH) -> bool:
    """Return True if Chart.js exists at chart_js_path, downloading it if missing."""
    if _is_present(chart_js_path):
        return True

    chart_js_path.parent.mkdir(parents=True, exist_ok=True)

    for url in CDN_URLS:
        try:
            logger.info(f"Downloading Chart.js {CHART_JS_VERSION} from {url}")
            with urllib.request.urlopen(url, timeout=30) as resp:
                data = resp.read()
            if len(data) > MIN_SIZE:
                chart_js_path.write_bytes(data)
                return True
        except Exception as e:
            logger.warning(f"Could not download {url}: {e}")

    # Fallback: official npm tarball (plain HTTP download, no npm CLI)
    try:
        logger.info(f"Downloading Chart.js {CHART_JS_VERSION} from {NPM_TARBALL_URL}")
        with urllib.request.urlopen(NPM_TARBALL_URL, timeout=60) as resp:
            blob = resp.read()
        with tarfile.open(fileobj=io.BytesIO(blob), mode="r:gz") as tar:
            data = tar.extractfile("package/dist/chart.umd.min.js").read()
        if len(data) > MIN_SIZE:
            chart_js_path.write_bytes(data)
            return True
    except Exception as e:
        logger.warning(f"Could not download npm tarball: {e}")

    logger.error(
        "Chart.js could not be downloaded - graphs will not render. "
        "Check your internet connection and run the launcher again."
    )
    return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="  %(message)s")
    ok = ensure_chart_js()
    if ok:
        print("  OK: Chart.js present")
    sys.exit(0 if ok else 1)
