import json
import os
import re
from pathlib import Path
from typing import Optional

import pendulum
import requests


def sync_episode_to_obsidian(episode: dict, podcast_name: str, notion_page_id: Optional[str] = None):
    """Sync one episode as a Markdown note for Obsidian and optional Google Drive."""
    if not _is_enabled():
        return

    export_dir = os.getenv("OBSIDIAN_EXPORT_DIR", "").strip()
    if not export_dir:
        print("OBSIDIAN_SYNC_ENABLED=true but OBSIDIAN_EXPORT_DIR is empty, skip Obsidian sync")
        return

    base = Path(export_dir)
    podcast_dir = base / _safe_filename(podcast_name or "Podcast")
    podcast_dir.mkdir(parents=True, exist_ok=True)

    eid = str(episode.get("Eid") or "unknown")
    title = str(episode.get("标题") or "Untitled")
    file_name = f"{_safe_filename(eid)}-{_safe_filename(title)[:80]}.md"
    file_path = podcast_dir / file_name

    content = _build_episode_markdown(episode=episode, podcast_name=podcast_name, notion_page_id=notion_page_id)
    file_path.write_text(content, encoding="utf-8")
    print(f"Obsidian synced: {file_path}")

    _upload_to_google_drive_if_enabled(file_path)


def _build_episode_markdown(episode: dict, podcast_name: str, notion_page_id: Optional[str]) -> str:
    title = str(episode.get("标题") or "Untitled")
    eid = str(episode.get("Eid") or "")
    status = str(episode.get("状态") or "")
    progress = episode.get("收听进度")
    duration = episode.get("时长")
    desc = str(episode.get("Description") or "")
    audio = str(episode.get("音频") or "")
    xiaoyuzhou_url = str(episode.get("链接") or "")
    tongyi_url = str(episode.get("通义链接") or "")
    pub_ts = episode.get("发布时间")
    played_ts = episode.get("日期")

    pub_date = _timestamp_to_local_time(pub_ts)
    played_date = _timestamp_to_local_time(played_ts)
    notion_url = f"https://www.notion.so/{notion_page_id.replace('-', '')}" if notion_page_id else ""

    lines = [
        "---",
        f'title: "{_escape_yaml(title)}"',
        f'podcast: "{_escape_yaml(podcast_name or "")}"',
        f'eid: "{_escape_yaml(eid)}"',
        f'status: "{_escape_yaml(status)}"',
        f'progress_seconds: {progress if isinstance(progress, (int, float)) else "null"}',
        f'duration_seconds: {duration if isinstance(duration, (int, float)) else "null"}',
        f'published_at: "{pub_date}"',
        f'played_at: "{played_date}"',
        f'notion_page_id: "{_escape_yaml(notion_page_id or "")}"',
        f'notion_url: "{_escape_yaml(notion_url)}"',
        f'xiaoyuzhou_url: "{_escape_yaml(xiaoyuzhou_url)}"',
        f'tongyi_url: "{_escape_yaml(tongyi_url)}"',
        "---",
        "",
        f"# {title}",
        "",
        f"- Podcast: {podcast_name or ''}",
        f"- Status: {status or ''}",
        f"- Published: {pub_date}",
        f"- Played: {played_date}",
        f"- Progress: {progress if progress is not None else ''}",
        f"- Duration: {duration if duration is not None else ''}",
        "",
        "## Description",
        "",
        desc or "(empty)",
        "",
    ]
    if audio:
        lines.append(f"[Audio Link]({audio})")
    if xiaoyuzhou_url:
        lines.append(f"[Xiaoyuzhou]({xiaoyuzhou_url})")
    if tongyi_url:
        lines.append(f"[Tongyi Transcript]({tongyi_url})")
    if notion_url:
        lines.append(f"[Notion Page]({notion_url})")

    return "\n".join(lines) + "\n"


def _upload_to_google_drive_if_enabled(file_path: Path):
    folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "").strip()
    if not folder_id:
        return

    access_token = _get_valid_drive_access_token()
    if not access_token:
        print("Google Drive sync skipped: no valid access token")
        return

    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {access_token}"})
    file_name = file_path.name
    content = file_path.read_bytes()

    existing_file_id = _find_drive_file_id(session=session, folder_id=folder_id, file_name=file_name)
    if existing_file_id:
        upload_url = f"https://www.googleapis.com/upload/drive/v3/files/{existing_file_id}?uploadType=media"
        resp = session.patch(upload_url, headers={"Content-Type": "text/markdown; charset=UTF-8"}, data=content)
        if resp.ok:
            print(f"Google Drive updated: {file_name}")
        else:
            print(f"Google Drive update failed: {resp.status_code} {resp.text}")
        return

    upload_url = "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart"
    metadata = {"name": file_name, "parents": [folder_id], "mimeType": "text/markdown"}
    files = {
        "metadata": ("metadata", json.dumps(metadata), "application/json; charset=UTF-8"),
        "file": (file_name, content, "text/markdown; charset=UTF-8"),
    }
    resp = session.post(upload_url, files=files)
    if resp.ok:
        print(f"Google Drive uploaded: {file_name}")
    else:
        print(f"Google Drive upload failed: {resp.status_code} {resp.text}")


def _find_drive_file_id(session: requests.Session, folder_id: str, file_name: str) -> Optional[str]:
    q = f"name = '{_escape_drive_query(file_name)}' and '{folder_id}' in parents and trashed = false"
    params = {"q": q, "fields": "files(id,name)", "pageSize": 1}
    resp = session.get("https://www.googleapis.com/drive/v3/files", params=params)
    if not resp.ok:
        print(f"Google Drive query failed: {resp.status_code} {resp.text}")
        return None
    files = resp.json().get("files", [])
    if files:
        return files[0].get("id")
    return None


def _safe_filename(value: str) -> str:
    cleaned = re.sub(r"[\\/:*?\"<>|]+", "_", value).strip()
    return cleaned or "untitled"


def _escape_yaml(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _escape_drive_query(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'")


def _timestamp_to_local_time(ts) -> str:
    if ts is None:
        return ""
    if not isinstance(ts, (int, float)):
        return str(ts)
    return pendulum.from_timestamp(int(ts), tz="Asia/Shanghai").to_datetime_string()


def _is_enabled() -> bool:
    return os.getenv("OBSIDIAN_SYNC_ENABLED", "").strip().lower() in {"1", "true", "yes", "on"}


def _get_valid_drive_access_token() -> Optional[str]:
    """
    Get a usable Drive access token.
    Priority:
    1) GOOGLE_DRIVE_ACCESS_TOKEN if available.
    2) Refresh via OAuth refresh token flow.
    """
    token = os.getenv("GOOGLE_DRIVE_ACCESS_TOKEN", "").strip()
    if token:
        return token
    return _refresh_drive_access_token()


def _refresh_drive_access_token() -> Optional[str]:
    token_url = os.getenv("GOOGLE_OAUTH_TOKEN_URL", "").strip() or "https://oauth2.googleapis.com/token"
    client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "").strip()
    client_secret = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "").strip()
    refresh_token = os.getenv("GOOGLE_OAUTH_REFRESH_TOKEN", "").strip()
    scope = os.getenv("GOOGLE_OAUTH_SCOPE", "").strip()

    if not client_id or not client_secret or not refresh_token:
        return None

    payload = {
        "grant_type": "refresh_token",
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
    }
    if scope:
        payload["scope"] = scope

    resp = requests.post(token_url, data=payload)
    if not resp.ok:
        print(f"Google OAuth refresh failed: {resp.status_code} {resp.text}")
        return None

    new_token = resp.json().get("access_token")
    if not new_token:
        print("Google OAuth refresh failed: missing access_token in response")
        return None

    os.environ["GOOGLE_DRIVE_ACCESS_TOKEN"] = new_token
    _upsert_env_key("GOOGLE_DRIVE_ACCESS_TOKEN", new_token)
    return new_token


def _upsert_env_key(key: str, value: str):
    """Update or append one key in local .env for next run."""
    env_path = Path(".env")
    if not env_path.exists():
        return
    content = env_path.read_text(encoding="utf-8")
    pattern = re.compile(rf"^{re.escape(key)}=.*$", re.MULTILINE)
    escaped_value = value.replace('"', '\\"')
    new_line = f'{key}="{escaped_value}"'
    if pattern.search(content):
        content = pattern.sub(new_line, content)
    else:
        if content and not content.endswith("\n"):
            content += "\n"
        content += f"{new_line}\n"
    env_path.write_text(content, encoding="utf-8")
