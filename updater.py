import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

APP_VERSION = "1.0.0"

# Thay bằng tên tài khoản và tên repository GitHub của bạn
GITHUB_OWNER = "vantienngo39-del"
GITHUB_REPO = "MathMate"


def _parse_version(v: str) -> tuple[int, ...]:
    nums = re.findall(r"\d+", v or "0")
    return tuple(int(x) for x in nums) if nums else (0,)


def get_app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def check_for_update(current_version: str = APP_VERSION) -> dict | None:
    """
    Kiểm tra bản release mới nhất trên GitHub.
    Trả về dict nếu có bản mới hơn, ngược lại trả về None.
    """
    if "TEN_USER" in GITHUB_OWNER:
        return None

    api_url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
    req = urllib.request.Request(
        api_url,
        headers={
            "User-Agent": f"MathMate-Updater/{current_version}",
            "Accept": "application/vnd.github+json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None

    latest_tag = str(data.get("tag_name") or "").strip()
    if not latest_tag:
        return None

    if _parse_version(latest_tag) <= _parse_version(current_version):
        return None

    zip_url = None
    for asset in data.get("assets", []):
        name = str(asset.get("name") or "").lower()
        url = str(asset.get("browser_download_url") or "")
        if name.endswith(".zip") and url:
            zip_url = url
            break

    if not zip_url:
        return None

    return {
        "version": latest_tag.lstrip("vV"),
        "tag": latest_tag,
        "zip_url": zip_url,
        "notes": str(data.get("body") or "").strip(),
    }


def apply_update_and_restart(zip_url: str) -> None:
    """
    Tải file ZIP về thư mục tạm, đợi tiến trình hiện tại đóng hẳn,
    giải nén đè lên thư mục ứng dụng hiện tại và khởi chạy lại MathMate.exe.
    """
    app_dir = get_app_dir()
    temp_dir = Path(tempfile.mkdtemp(prefix="mathmate_update_"))
    zip_path = temp_dir / "update.zip"
    extract_dir = temp_dir / "extracted"
    ps_script = temp_dir / "run_update.ps1"

    urllib.request.urlretrieve(zip_url, str(zip_path))

    pid = os.getpid()
    exe_name = Path(sys.executable).name if getattr(sys, "frozen", False) else "MathMate.exe"
    target_exe = app_dir / exe_name

    # Script PowerShell chờ app tắt hẳn rồi giải nén đè và mở lại app
    ps_content = f"""
$ErrorActionPreference = "Stop"
try {{
    Wait-Process -Id {pid} -ErrorAction SilentlyContinue
}} catch {{}}
Start-Sleep -Milliseconds 600

Expand-Archive -Path "{zip_path}" -DestinationPath "{extract_dir}" -Force

# Nếu bên trong zip có 1 thư mục bọc ngoài chứa exe thì lấy thư mục đó làm nguồn
$sourceRoot = "{extract_dir}"
$innerDirs = Get-ChildItem -Path $sourceRoot -Directory
if ($innerDirs.Count -eq 1 -and -not (Test-Path (Join-Path $sourceRoot "{exe_name}"))) {{
    $sourceRoot = $innerDirs[0].FullName
}}

Copy-Item -Path (Join-Path $sourceRoot "*") -Destination "{app_dir}" -Recurse -Force

if (Test-Path "{target_exe}") {{
    Start-Process -FilePath "{target_exe}" -WorkingDirectory "{app_dir}"
}}
"""
    ps_script.write_text(ps_content, encoding="utf-8")

    subprocess.Popen(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-WindowStyle",
            "Hidden",
            "-File",
            str(ps_script),
        ],
        close_fds=True,
    )

    if getattr(sys, "frozen", False):
        os._exit(0)
