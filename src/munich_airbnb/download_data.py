from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen
from datetime import datetime
import html as html_parser
import json
import re


PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
RESULTS_DIR = PROJECT_ROOT / "results"

INSIDE_AIRBNB_GET_DATA_URL = "https://insideairbnb.com/get-the-data/"

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

DOWNLOAD_TARGETS = {
    "summary_listings": {
        "file_name": "listings.csv",
        "required_path_part": "/visualisations/",
        "output_name": "listings.csv",
        "minimum_file_size_bytes": 50_000,
    },
    "calendar": {
        "file_name": "calendar.csv.gz",
        "required_path_part": "/data/",
        "output_name": "calendar.csv.gz",
        "minimum_file_size_bytes": 500_000,
    },
}


def fetch_get_data_page():
    request = Request(INSIDE_AIRBNB_GET_DATA_URL,headers=DEFAULT_HEADERS,)
    with urlopen(request, timeout=60) as response:
        page_content = response.read().decode("utf-8", errors="replace")
    return page_content

def extract_links_from_page(page_content):
    raw_links = re.findall(r'href=["\']([^"\']+)["\']', page_content)
    clean_links = []
    for raw_link in raw_links:
        decoded_link = html_parser.unescape(raw_link)
        absolute_link = urljoin(INSIDE_AIRBNB_GET_DATA_URL, decoded_link)
        clean_links.append(absolute_link)
    return clean_links

def extract_snapshot_date_from_url(url):
    match = re.search(r"/(\d{4}-\d{2}-\d{2})/", url)
    if match:
        return match.group(1)
    return "unknown"

def find_latest_munich_file_url(links, file_name, required_path_part):
    candidates = []
    for link in links:
        lower_link = link.lower()
        if "data.insideairbnb.com" not in lower_link:
            continue
        if "/munich/" not in lower_link:
            continue
        if required_path_part not in lower_link:
            continue
        if not lower_link.endswith(file_name.lower()):
            continue
        snapshot_date = extract_snapshot_date_from_url(link)
        candidates.append(
            {
                "url": link,
                "snapshot_date": snapshot_date,
            }
        )
    if not candidates:
        raise ValueError(
            f"No Munich file found for {file_name} with path part {required_path_part}."
        )
    candidates = sorted(
        candidates,
        key=lambda candidate: candidate["snapshot_date"],
        reverse=True,
    )
    return candidates[0]

def download_file(url, output_path, minimum_file_size_bytes, force=False):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists() and not force:
        return {
            "status": "skipped_existing_file",
            "output_path": str(output_path),
            "file_size_bytes": output_path.stat().st_size,
        }
    temporary_output_path = output_path.with_suffix(output_path.suffix + ".tmp")
    request = Request(
        url,
        headers=DEFAULT_HEADERS,
    )
    downloaded_bytes = 0
    with urlopen(request, timeout=300) as response:
        with open(temporary_output_path, "wb") as file:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                file.write(chunk)
                downloaded_bytes += len(chunk)
    if downloaded_bytes < minimum_file_size_bytes:
        temporary_output_path.unlink(missing_ok=True)
        raise ValueError(
            f"Downloaded file is too small: {downloaded_bytes} bytes. "
            f"This may mean the website returned an error page instead of the data file."
        )
    temporary_output_path.replace(output_path)
    return {
        "status": "downloaded",
        "output_path": str(output_path),
        "file_size_bytes": downloaded_bytes,
    }

def save_download_manifest(manifest):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    manifest_path = RESULTS_DIR / "download_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as file:
        json.dump(manifest, file, indent=4)
    return manifest_path

def download_latest_munich_data(force=False):
    print("Downloading latest Munich Inside Airbnb data")
    print("=" * 50)
    page_content = fetch_get_data_page()
    links = extract_links_from_page(page_content)
    manifest = {
        "source_page": INSIDE_AIRBNB_GET_DATA_URL,
        "downloaded_at": datetime.now().isoformat(timespec="seconds"),
        "city": "Munich",
        "files": [],
    }
    for target_name, target_settings in DOWNLOAD_TARGETS.items():
        latest_file = find_latest_munich_file_url(
            links=links,
            file_name=target_settings["file_name"],
            required_path_part=target_settings["required_path_part"],
        )
        output_path = RAW_DATA_DIR / target_settings["output_name"]
        result = download_file(
            url=latest_file["url"],
            output_path=output_path,
            minimum_file_size_bytes=target_settings["minimum_file_size_bytes"],
            force=force,
        )
        file_record = {
            "target_name": target_name,
            "snapshot_date": latest_file["snapshot_date"],
            "source_url": latest_file["url"],
            "local_path": result["output_path"],
            "status": result["status"],
            "file_size_bytes": result["file_size_bytes"],
        }
        manifest["files"].append(file_record)
        print(
            f"- {target_name}: {result['status']} "
            f"({latest_file['snapshot_date']})"
        )
    manifest_path = save_download_manifest(manifest)
    print("\nDownload manifest saved to:")
    print(f"- {manifest_path}")
    return manifest