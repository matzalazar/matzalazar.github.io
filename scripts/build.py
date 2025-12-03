#!/usr/bin/env python3
"""
Orquestador de construcción del sitio personal.
AJUSTADO: Genera exactamente la estructura de datos que pide el index.md actual.
"""

from __future__ import annotations

import datetime
import json
import os
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml


# ---------------------------------------------------------------------------
# Configuración de paths
# ---------------------------------------------------------------------------

try:
    REPO_DIR = Path(__file__).resolve().parent.parent
except NameError:
    REPO_DIR = Path(".").resolve()

# Directorio base con datos crudos del tracker (FHS prod en la Pi; override con env)
RAW_DATA_DIR = Path(os.getenv("TRACKER_RAW_DATA", "/var/lib/personal-track"))

# Directorio con notas de Obsidian que se publican en el blog (ruta en la Pi; override con env)
OBSIDIAN_NOTES_PATH = Path(
    os.getenv(
        "OBSIDIAN_NOTES_PATH",
        "/home/matzalazar/dropbox_montado/Aplicaciones/remotely-save/Notas/blog notes",
    )
)

# Destinos dentro del repo Jekyll
DATA_DEST_DIR = REPO_DIR / "_data"
LOGS_DEST_DIR = REPO_DIR / "_logs"
CV_DEST_FILE = REPO_DIR / "about.md"


# ---------------------------------------------------------------------------
# Utilidades generales
# ---------------------------------------------------------------------------


def slugify(text: str, max_length: int = 80) -> str:
    text = text.strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-{2,}", "-", text)
    text = text.strip("-")
    if max_length and len(text) > max_length:
        text = text[:max_length].rstrip("-")
    return text or "nota-sin-titulo"


def safe_mkdir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def safe_write_text(content: str, dest: Path) -> None:
    safe_mkdir(dest.parent)
    dest.write_text(content, encoding="utf-8")


def safe_write_yaml(data: Any, dest: Path) -> None:
    safe_mkdir(dest.parent)
    with dest.open("w", encoding="utf-8") as f:
        yaml.safe_dump(
            data,
            f,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
        )


def find_latest_json(prefix: str) -> Optional[Path]:
    if not RAW_DATA_DIR.exists():
        print(f"[WARN] RAW_DATA_DIR no existe: {RAW_DATA_DIR}")
        return None

    candidates = list(RAW_DATA_DIR.rglob(f"{prefix}*.json"))
    
    if not candidates:
        print(f"[INFO] No se encontraron JSON para prefijo '{prefix}' en {RAW_DATA_DIR}")
        return None

    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0]


def load_json(prefix: str) -> Optional[Any]:
    path = find_latest_json(prefix)
    if path is None:
        return None

    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"[OK] JSON cargado para '{prefix}': {path.relative_to(RAW_DATA_DIR)}")
        return data
    except Exception as e:
        print(f"[ERROR] No se pudo leer/parsing JSON '{path}': {e}")
        return None


def clean_markdown_text(text: str) -> str:
    text = re.sub(r"\]*\]", "", text)
    text = re.sub(r"\[cite_start\]", "", text)
    text = re.sub(r"\[cite_end\]", "", text)
    text = re.sub(r"^[ \t]*•[ \t]+", "- ", text, flags=re.MULTILINE)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def parse_front_matter(content: str) -> Tuple[Optional[Dict[str, Any]], str]:
    if not content.startswith("---"):
        return None, content
    parts = content.split("\n")
    try:
        end_idx = next(
            i for i, line in enumerate(parts[1:], start=1) if line.strip() == "---"
        )
    except StopIteration:
        return None, content

    fm_lines = parts[1:end_idx]
    body_lines = parts[end_idx + 1 :]
    fm_text = "\n".join(fm_lines)
    body = "\n".join(body_lines)

    try:
        fm = yaml.safe_load(fm_text) or {}
        if not isinstance(fm, dict):
            fm = {}
    except Exception as e:
        print(f"[WARN] No se pudo parsear front matter YAML: {e}")
        fm = {}

    return fm, body


def build_front_matter(fm: Dict[str, Any]) -> str:
    safe_fm = dict(fm)
    text = yaml.safe_dump(
        safe_fm,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
    )
    return f"---\n{text}---\n"


def ensure_date(value: Any, fallback: datetime.date) -> datetime.date:
    if isinstance(value, datetime.date):
        return value
    if isinstance(value, datetime.datetime):
        return value.date()
    if isinstance(value, str):
        try:
            return datetime.datetime.fromisoformat(value).date()
        except Exception:
            try:
                return datetime.datetime.strptime(value[:10], "%Y-%m-%d").date()
            except Exception:
                return fallback
    return fallback


# ---------------------------------------------------------------------------
# Tarea 1: Lecturas actuales (Goodreads) -> _data/reading.yml
# ---------------------------------------------------------------------------


def extract_book_title(book: Dict[str, Any]) -> str:
    for key in ("title", "book_title", "name"):
        value = book.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return "Título desconocido"


def extract_book_author(book: Dict[str, Any]) -> str:
    if "author" in book and isinstance(book["author"], str):
        return book["author"].strip()
    authors = book.get("authors")
    if isinstance(authors, list) and authors:
        first = authors[0]
        if isinstance(first, str):
            return first.strip()
        if isinstance(first, dict):
            name = first.get("name") or first.get("full_name")
            if isinstance(name, str):
                return name.strip()
    if isinstance(authors, str):
        return authors.strip()
    return "Autor desconocido"


def extract_book_progress(book: Dict[str, Any]) -> Optional[str]:
    pct = book.get("percent") or book.get("progress") or book.get("percent_complete") or book.get("progress_percent")
    if isinstance(pct, (int, float)):
        return str(int(pct)) # Devolvemos solo el número como string, el template agrega el %
    if isinstance(pct, str) and pct.strip():
        return pct.strip().replace("%", "") # Limpiamos por si acaso

    current = book.get("current_page") or book.get("page_read") or book.get("pages_read")
    total = book.get("total_pages") or book.get("pages") or book.get("page_count") or book.get("pages_total")
    if isinstance(current, (int, float)) and isinstance(total, (int, float)) and total:
        # Si es paginas 100/200, calculamos porcentaje para mantener consistencia con template que espera {{ b.progress }}%
        return str(int((current / total) * 100))
    return None


def update_reading() -> None:
    print("\n--- Tarea 1: Leyendo Goodreads para _data/reading.yml ---")
    data = load_json("goodreads")
    if data is None:
        return

    if isinstance(data, list):
        books = data
    elif isinstance(data, dict):
        if isinstance(data.get("books"), list):
            books = data["books"]
        elif isinstance(data.get("reading"), list):
            books = data["reading"]
        elif isinstance(data.get("currently_reading"), list):
            books = data["currently_reading"]
        else:
            books = list(data.values())
    else:
        print("[WARN] Formato de datos de Goodreads no reconocido.")
        return

    normalized: List[Dict[str, Any]] = []
    for book in books:
        if not isinstance(book, dict):
            continue
        
        title = extract_book_title(book)
        author = extract_book_author(book)
        progress = extract_book_progress(book)
        
        # Ajuste para template: usar claves 'titulo', 'author', 'progress'
        entry: Dict[str, Any] = {
            "titulo": title,
            "author": author,
        }
        if progress:
            entry["progress"] = progress
            
        normalized.append(entry)

    # Ajuste: Escribimos la lista directamente, sin clave raiz 'reading'
    safe_write_yaml(normalized, DATA_DEST_DIR / "reading.yml")
    print(f"[OK] _data/reading.yml generado con {len(normalized)} libros.")


# ---------------------------------------------------------------------------
# Tarea 2: Estudios (Coursera + UPSO) -> _data/studies.yml
# ---------------------------------------------------------------------------


def update_studies() -> None:
    print("\n--- Tarea 2: Leyendo datos de estudios para _data/studies.yml ---")

    # --- Coursera ---
    coursera_data = load_json("coursera")
    coursera_list = [] # Template espera una lista simple en studies.coursera

    if coursera_data:
        if isinstance(coursera_data, list):
            courses = coursera_data
        elif isinstance(coursera_data, dict):
            courses = coursera_data.get("courses") or list(coursera_data.values())
        else:
            courses = []

        for course in courses:
            if not isinstance(course, dict):
                continue
            
            # Filtro: Solo queremos los activos para mostrar en el home? 
            # El template itera todo studies.coursera. Asumimos que el JSON trae lo relevante.
            
            name = (course.get("name") or course.get("title") or course.get("course_name") or "Curso sin nombre")
            pct = course.get("percent") or course.get("progress") or 0
            
            # Ajuste para template: claves 'title', 'percent'
            item = {
                "title": str(name),
                "percent": int(pct) if pct else 0
            }
            coursera_list.append(item)

    # --- UPSO ---
    upso_data = load_json("upso")
    upso_en_curso = [] # Template espera studies.upso.en_curso

    if upso_data:
        if isinstance(upso_data, list):
            materias = upso_data
        elif isinstance(upso_data, dict):
            materias = upso_data.get("materias") or upso_data.get("subjects") or list(upso_data.values())
        else:
            materias = []

        for mat in materias:
            if not isinstance(mat, dict):
                continue
            
            estado = str(mat.get("estado") or mat.get("status") or "").strip()
            # Filtramos para 'en_curso'
            if any(x in estado.lower() for x in ["en curso", "cursando", "ongoing", "progreso"]):
                name = (mat.get("nombre") or mat.get("name") or mat.get("subject") or "Materia sin nombre")
                
                # Ajuste para template: claves 'nombre', 'estado'
                item = {
                    "nombre": str(name).strip(),
                    "estado": estado
                }
                upso_en_curso.append(item)

    yml_data = {
        "coursera": coursera_list,
        "upso": {
            "en_curso": upso_en_curso
        }
    }
    safe_write_yaml(yml_data, DATA_DEST_DIR / "studies.yml")
    print("[OK] _data/studies.yml generado.")


# ---------------------------------------------------------------------------
# Tarea 3: Actividad de trabajo (GitHub) -> _data/work.yml
# ---------------------------------------------------------------------------


def update_work_activity() -> None:
    print("\n--- Tarea 3: Leyendo actividad GitHub para _data/work.yml ---")
    github_data = load_json("github_daily")
    if github_data is None:
        return

    if isinstance(github_data, dict):
        events = github_data.get("events") or github_data.get("activity") or list(github_data.values())
    elif isinstance(github_data, list):
        events = github_data
    else:
        print("[WARN] Formato de github_daily no reconocido.")
        return

    repo_counter: Counter[str] = Counter()

    for ev in events:
        if not isinstance(ev, dict):
            continue
        repo_name = (ev.get("repo") or ev.get("repository") or ev.get("repo_name") or ev.get("name"))
        if repo_name and isinstance(repo_name, str):
            commits = ev.get("commits") or ev.get("count") or 1
            repo_counter[repo_name.strip()] += int(commits)

    total_commits = sum(repo_counter.values())
    distinct_repos = len(repo_counter)
    
    # Ajuste para template: claves 'commits', 'repos' en la raiz del archivo work.yml
    yml_data = {
        "commits": int(total_commits),
        "repos": int(distinct_repos)
    }
    
    safe_write_yaml(yml_data, DATA_DEST_DIR / "work.yml")
    print(f"[OK] _data/work.yml generado. Commits: {total_commits}, Repos: {distinct_repos}.")


# ---------------------------------------------------------------------------
# Tarea 4: CV / Sobre mí (LinkedIn) -> about.md
# ---------------------------------------------------------------------------


def update_cv_markdown() -> None:
    print("\n--- Tarea 4: Leyendo datos de LinkedIn para about.md ---")
    linkedin_data = load_json("linkedin")
    if linkedin_data is None:
        return

    if not isinstance(linkedin_data, dict):
        return

    headline = linkedin_data.get("headline") or linkedin_data.get("title") or ""
    summary = (linkedin_data.get("summary") or linkedin_data.get("about") or linkedin_data.get("description") or "")
    summary = clean_markdown_text(str(summary))
    positions = linkedin_data.get("positions") or linkedin_data.get("experience") or []
    if not isinstance(positions, list):
        positions = []

    lines: List[str] = []
    fm = {
        "layout": "page",
        "title": "Sobre mí",
        "permalink": "/about/",
    }
    lines.append(build_front_matter(fm).rstrip("\n"))
    lines.append("# Sobre mí\n")

    if headline:
        lines.append(f"**{headline}**\n")

    if summary:
        lines.append(summary)
        lines.append("")

    if positions:
        lines.append("## Experiencia reciente\n")
        for pos in positions[:6]:
            if not isinstance(pos, dict):
                continue
            title = (pos.get("title") or pos.get("position") or pos.get("role") or "Rol sin título")
            company = pos.get("company") or pos.get("organization") or ""
            start = pos.get("start_date") or pos.get("from")
            end = pos.get("end_date") or pos.get("to") or "Actualidad"
            desc = pos.get("description") or ""
            desc = clean_markdown_text(str(desc))

            header_parts = [str(title)]
            if company:
                header_parts.append(f"en {company}")
            header = " - ".join(header_parts)
            if start:
                header += f" ({start} - {end})"

            lines.append(f"- **{header}**")
            if desc:
                lines.append(f"  {desc}")
        lines.append("")

    content = "\n".join(lines).rstrip() + "\n"
    safe_write_text(content, CV_DEST_FILE)
    print(f"[OK] about.md generado en {CV_DEST_FILE}.")


# ---------------------------------------------------------------------------
# Tarea 5: Sincronizar logs desde Obsidian -> _logs/*.md
# ---------------------------------------------------------------------------


def update_logs_from_obsidian() -> None:
    print("\n--- Tarea 5: Sincronizando notas de Obsidian hacia _logs/ ---")
    if not OBSIDIAN_NOTES_PATH.exists():
        print(f"[INFO] OBSIDIAN_NOTES_PATH no existe: {OBSIDIAN_NOTES_PATH}")
        return

    safe_mkdir(LOGS_DEST_DIR)
    published_dest_files: set[Path] = set()

    for note_path in OBSIDIAN_NOTES_PATH.rglob("*.md"):
        if not note_path.is_file():
            continue
        try:
            content = note_path.read_text(encoding="utf-8")
        except Exception as e:
            print(f"[WARN] No se pudo leer nota {note_path}: {e}")
            continue

        fm, body = parse_front_matter(content)
        if fm is None:
            continue
        status = str(fm.get("status") or fm.get("estado") or "").strip().lower()
        if status != "publicar":
            continue

        title = (fm.get("title") or fm.get("nombre") or fm.get("titulo") or note_path.stem)
        slug = fm.get("slug") or slugify(str(title))
        stat = note_path.stat()
        fallback_date = datetime.date.fromtimestamp(stat.st_mtime)
        date_value = (fm.get("date") or fm.get("fecha") or fm.get("created") or fm.get("created_at"))
        note_date = ensure_date(date_value, fallback=fallback_date)
        date_str = note_date.strftime("%Y-%m-%d")

        fm_out = dict(fm)
        fm_out.pop("status", None)
        fm_out.setdefault("date", date_str)
        fm_out.setdefault("slug", slug)
        fm_out.setdefault("layout", "post")

        final_content = build_front_matter(fm_out) + body.lstrip("\n")
        dest_filename = f"{date_str}-{slug}.md"
        dest_path = LOGS_DEST_DIR / dest_filename
        safe_write_text(final_content, dest_path)
        published_dest_files.add(dest_path)
        print(f"[OK] Nota publicada: {note_path.name} -> {dest_filename}")

    existing_logs = {p for p in LOGS_DEST_DIR.glob("*.md") if p.is_file()}
    orphan_logs = existing_logs - published_dest_files
    for orphan in sorted(orphan_logs):
        try:
            orphan.unlink()
            print(f"[CLEANUP] Log huérfano eliminado: {orphan.name}")
        except Exception as e:
            print(f"[WARN] No se pudo eliminar log huérfano {orphan}: {e}")

    print(f"[OK] Logs completos. Publicados: {len(published_dest_files)}.")


# ---------------------------------------------------------------------------
# Orquestador principal
# ---------------------------------------------------------------------------


def main() -> None:
    print("--- Iniciando Orquestador build.py (MATCH-TEMPLATE-VERSION) ---")
    print(f"Repositorio:           {REPO_DIR}")
    print(f"Datos crudos:          {RAW_DATA_DIR}")
    
    safe_mkdir(DATA_DEST_DIR)
    safe_mkdir(LOGS_DEST_DIR)

    update_reading()
    update_studies()
    update_work_activity()
    update_cv_markdown()
    update_logs_from_obsidian()

    print("\n--- Generando metadatos del sitio (_data/meta.yml) ---")
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    safe_write_yaml({"last_update": now}, DATA_DEST_DIR / "meta.yml")
    print("[OK] _data/meta.yml generado.")
    print("\n--- Orquestador finalizado con éxito ---")


if __name__ == "__main__":
    import sys
    if not RAW_DATA_DIR.exists():
        print(f"[ERROR] El directorio de datos crudos no existe: {RAW_DATA_DIR}")
        sys.exit(1)
    try:
        main()
    except Exception as e:
        print(f"[ERROR] Falló la construcción del sitio: {e}")
        sys.exit(1)
