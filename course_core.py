"""Shared, offline course authoring model. No UI or provider dependencies."""
from __future__ import annotations

import html
import io
import json
import os
from pathlib import Path
import re
import tempfile
import zipfile

VERSION = "0.2.0-rc.2"
MAX_FILE_BYTES = 8 * 1024 * 1024
MAX_TEXT = 180_000
MAX_OUTPUT = 400_000
SAMPLE = """Course Code: AE 201
Course Name: Aircraft Structures
Description: Introduction to aircraft structural loads, materials, and inspection.
Duration: 6 weeks
Contact Hours: 18

Learning Outcomes:
1. Explain the load paths in a basic aircraft structure.
2. Compare structural materials using relevant properties.
3. Document a basic visual inspection using supplied criteria.

Course Outline:
Week 1: Airframe components and load paths
- Wings, fuselage, and empennage
Week 2: Aircraft loads and stresses
- Tension, compression, shear, bending, and torsion
Weeks 3-4: Materials and joining methods
- Metallic and composite structures
Week 5: Inspection and damage reporting
Week 6: Case study and final assessment

References:
Instructor-supplied aircraft structural manual and approved learning materials.
"""


class CourseError(ValueError):
    """Safe, user-facing validation failure."""


def read_file(path: str | Path) -> bytes:
    with open(path, "rb") as handle:
        data = handle.read(MAX_FILE_BYTES + 1)
    if len(data) > MAX_FILE_BYTES:
        raise CourseError("Choose a file smaller than 8 MB.")
    return data


def bounded_text(value, label, limit=MAX_TEXT):
    if not isinstance(value, str) or len(value) > limit or "\x00" in value:
        raise CourseError(f"{label} must be text of at most {limit:,} characters.")
    return value


def extract_text(name: str, data: bytes) -> str:
    """Extract bounded text; PDF scans need external OCR. Never write uploads."""
    if len(data) > MAX_FILE_BYTES:
        raise CourseError("Choose a file smaller than 8 MB.")
    suffix = Path(name).suffix.lower()
    try:
        if suffix in {".txt", ".md"}:
            text = data.decode("utf-8-sig")
        elif suffix == ".docx":
            from docx import Document
            # Check expanded size before handing a ZIP-based Office file to a parser.
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                if sum(x.file_size for x in archive.infolist()) > 32 * 1024 * 1024:
                    raise CourseError("The Word document expands beyond the 32 MB limit.")
            from docx.oxml.ns import qn
            from docx.table import Table
            from docx.text.paragraph import Paragraph
            document = Document(io.BytesIO(data))
            parts = []
            for node in document.element.body:
                if node.tag == qn("w:p"):
                    parts.append(Paragraph(node, document).text)
                elif node.tag == qn("w:tbl"):
                    parts.extend(" | ".join(c.text for c in row.cells)
                                 for row in Table(node, document).rows)
            text = "\n".join(parts)
        elif suffix == ".pdf":
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(data))
            if reader.is_encrypted:
                raise CourseError("Use an unencrypted PDF or paste its text.")
            if len(reader.pages) > 100:
                raise CourseError("Use a syllabus with at most 100 PDF pages.")
            parts, length = [], 0
            for page in reader.pages:
                part = page.extract_text() or ""
                length += len(part)
                if length > MAX_TEXT:
                    raise CourseError("The extracted syllabus is too long. Import a smaller section.")
                parts.append(part)
            text = "\n".join(parts)
        else:
            raise CourseError("Import TXT, Markdown, DOCX, or a text-based PDF.")
    except CourseError:
        raise
    except Exception:
        raise CourseError("Could not read this file. Try UTF-8 text or paste the syllabus.") from None
    bounded_text(text, "Syllabus")
    if not text.strip():
        raise CourseError("No text was found. Scanned PDFs need OCR before import.")
    return text.strip()


META = {
    "course code": "code", "course name": "title", "course title": "title",
    "description": "description", "course description": "description",
    "duration": "duration", "weeks": "duration", "contact hours": "hours",
    "total hours": "hours", "hours": "hours", "prerequisite": "prerequisite",
    "pre-requisite": "prerequisite", "units": "units", "instructor": "instructor",
}
SECTION = {
    "learning outcomes": "outcomes", "course outcomes": "outcomes",
    "course learning outcomes": "outcomes", "course objectives": "outcomes",
    "objectives": "outcomes", "outcomes": "outcomes",
    "course outline": "topics", "course outline: lecture": "topics",
    "topics": "topics", "course content": "topics", "schedule": "topics",
    "references": "references", "textbooks": "references",
    "suggested textbooks and references": "references",
    "assessment": "other", "assessments": "other", "grading": "other",
    "grading system": "other", "course policies": "other",
}
WEEK = re.compile(r"^(weeks?|modules?|units?|lessons?)\s+(\d+(?:\s*[-–]\s*\d+)?)\s*[:.)-]?\s*(.*)$", re.I)


def clean_item(text):
    return re.sub(r"^\s*(?:[-*•]\s+|\d+(?:\.\d+)*[.)]\s+)", "", text).strip()


def analyze_syllabus(syllabus: str) -> dict:
    bounded_text(syllabus, "Syllabus")
    if not syllabus.strip():
        raise CourseError("Enter a syllabus first.")
    result = {"metadata": {}, "outcomes": [], "topics": [], "references": [], "warnings": []}
    section = "topics"
    pending = None
    table_headers = None
    explicit_outline = bool(re.search(r"^\s*(?:#+\s*)?(?:weeks?|modules?|units?|lessons?)\s+\d", syllabus, re.I | re.M))
    for raw in syllabus.splitlines():
        line = raw.strip().strip("# ").strip()
        if not line:
            continue
        if line.lower() in {"course syllabus", "syllabus"}:
            continue
        key, separator, value = line.partition(":")
        normalized = key.lower().strip().strip("*")
        if separator and normalized in META:
            result["metadata"][META[normalized]] = value.strip()
            pending = META[normalized] if not value.strip() else None
            section = "metadata"
            table_headers = None
            continue
        heading = line.lower().rstrip(":").strip().strip("*")
        if heading in SECTION:
            section, pending, table_headers = SECTION[heading], None, None
            continue
        if separator and normalized in SECTION:
            section, pending = SECTION[normalized], None
            if not value.strip():
                continue
            line = value.strip()
        if pending:
            result["metadata"][pending] = line
            pending = None
            continue
        if "|" in line:
            cells = [c.strip() for c in line.strip("|").split("|")]
            if cells[0].lower() in {"field", "fields"}:
                continue
            if all(re.fullmatch(r"[:\-\s]+", c) for c in cells):
                continue
            if len(cells) >= 2 and cells[0].lower() in META:
                result["metadata"][META[cells[0].lower()]] = cells[1]
                continue
            if any(c.lower() in {"topic", "topics", "content", "week", "weeks"} for c in cells):
                table_headers, section = [c.lower() for c in cells], "topics"
                continue
            if table_headers:
                row = dict(zip(table_headers, cells))
                title = next((row[k] for k in ("topic", "topics", "content") if row.get(k)), "")
                if title.lower() in {"total", "totals"}:
                    continue
                if title:
                    week = row.get("week", row.get("weeks", ""))
                    result["topics"].append({"title": title, "schedule": week, "subtopics": []})
                continue
        explicit = WEEK.match(line)
        if explicit:
            section = "topics"
            title = explicit[3].strip() or f"{explicit[1].title()} {explicit[2]}"
            schedule = explicit[2].replace(" ", "") if explicit[1].lower().startswith("week") else ""
            result["topics"].append({"title": title, "schedule": schedule, "subtopics": []})
        elif section in {"outcomes", "references"}:
            result[section].append(clean_item(line))
        elif section == "topics":
            if (raw.startswith((" ", "\t")) or re.match(r"^\d+\.\d+", line) or
                    (explicit_outline and re.match(r"^[-*•]\s", line))) and result["topics"]:
                result["topics"][-1]["subtopics"].append(clean_item(line))
            else:
                result["topics"].append({"title": clean_item(line), "schedule": "", "subtopics": []})
        elif section == "metadata" and result["metadata"].get("description"):
            result["metadata"]["description"] += " " + line
    if len(result["topics"]) > 80:
        raise CourseError("More than 80 modules detected. Simplify the outline or import a smaller section.")
    if not result["topics"]:
        result["warnings"].append("No topics detected. Add Week 1: Topic lines or a Topics section.")
    if not result["outcomes"]:
        result["warnings"].append("No course learning outcomes detected. Add them before finalizing the course.")
    if not result["metadata"].get("title"):
        result["warnings"].append("Course title is missing. Enter it in the course title field.")
    if any(not t["schedule"] for t in result["topics"]):
        result["warnings"].append("Some modules have no week assignment. Their schedule remains unassigned.")
    return result


def build_course_markdown(syllabus: str, title: str = "") -> str:
    plan = analyze_syllabus(syllabus)
    if not plan["topics"]:
        raise CourseError("Add a Topics section or Week 1: Topic lines before creating a local framework.")
    title = title.strip() or plan["metadata"].get("title", "Untitled Course")
    lines = [f"# {title}", "", "> Local teaching framework — add subject content and review before teaching.", ""]
    for field, value in plan["metadata"].items():
        if field != "title":
            lines += [f"**{field.replace('_', ' ').title()}:** {value}", ""]
    lines += ["## Course learning outcomes", ""]
    lines += [f"{i}. {value}" for i, value in enumerate(plan["outcomes"], 1)] or ["[Add measurable course outcomes.]"]
    lines += ["", "## Course map", "", "| Module | Week(s) | Topic |", "|---|---|---|"]
    for i, topic in enumerate(plan["topics"], 1):
        lines += [f"| {i} | {topic['schedule'] or 'Unassigned'} | {topic['title'].replace('|', '/')} |"]
    for i, topic in enumerate(plan["topics"], 1):
        subject = topic["title"]
        lines += ["", f"## Module {i}: {subject}", "", f"**Week(s):** {topic['schedule'] or 'Unassigned'}", "",
                  "### Intended learning outcomes (suggested)",
                  f"- Explain the central concepts of {subject} using an annotated example.",
                  f"- Apply {subject} to a relevant case and justify the approach.",
                  "- Identify a limitation or common error and explain how to address it.", "",
                  "**Course outcome alignment:** [Select the relevant course outcomes.]", "",
                  "### Lesson content", "[Add instructor-verified explanations, diagrams, and worked examples.]"]
        lines += [f"- {sub}" for sub in topic["subtopics"]]
        lines += ["", "### Learning sequence", "1. Recall: ask learners what they already know and check misconceptions.",
                  f"2. Explain: introduce {subject} using the supplied learning materials.",
                  "3. Model: work through one example and explain each decision.",
                  "4. Practice: learners solve a comparable case and compare approaches.",
                  "5. Reflect: use an exit ticket to identify the concept needing more practice.", "",
                  "### Activity", f"Analyze a case involving {subject}. Submit a short explanation, evidence, and a justified conclusion.", "",
                  "### Assessment prompts (instructor review required)",
                  f"1. Explain one principle of {subject} and illustrate it with an example.",
                  "2. Apply that principle to a new case. Show the reasoning and assumptions.",
                  "3. Identify a likely error in the approach and propose a correction.", "",
                  "**Answer guide:** [Add verified expected answers and acceptable alternatives.]", "",
                  "**Suggested rubric:** conceptual accuracy 40%; reasoning/evidence 40%; clarity 20%. Confirm against syllabus grading.", "",
                  "### Resources and accessibility", "[Attach verified reading links and provide text alternatives for diagrams/media.]", "",
                  "### Summary", "[Write the key takeaways after completing the lesson content.]"]
    lines += ["", "## Supplied references", ""] + ([f"- {r}" for r in plan["references"]] or ["[Add verified references.]"])
    lines += ["", "## Instructor completion checklist", "- Verify facts, examples, answers, references, and outcome alignment.",
              "- Confirm contact hours, week assignments, grading, and assessment load.",
              "- Replace all bracketed placeholders; check accessibility before sharing.", ""]
    return "\n".join(lines)


def validate_pending(value):
    """Allow-list a resumable draft, never provider credentials or endpoints."""
    if value is None:
        return None
    if not isinstance(value, dict):
        raise CourseError("Invalid draft checkpoint.")
    source = bounded_text(value.get("syllabus"), "Draft syllabus")
    plan = analyze_syllabus(source)
    indices, completed = value.get("indices"), value.get("completed")
    if (not isinstance(indices, list) or not indices or len(indices) > 80 or
            any(type(i) is not int or i < 0 or i >= len(plan["topics"]) for i in indices) or
            indices != sorted(set(indices))):
        raise CourseError("Invalid draft module selection.")
    if not isinstance(completed, list) or len(completed) > len(indices):
        raise CourseError("Invalid completed modules.")
    parts = [bounded_text(t, "Draft module", MAX_OUTPUT) for t in completed]
    if any(not t.strip() for t in parts) or sum(map(len, parts)) > MAX_OUTPUT:
        raise CourseError("Draft modules are empty or exceed the course limit.")
    profile = value.get("profile")
    if not isinstance(profile, str) or not re.fullmatch(r"[0-9a-f]{64}", profile):
        raise CourseError("Invalid draft engine profile.")
    return {"syllabus": source, "title": bounded_text(value.get("title"), "Draft title", 300),
            "provider": bounded_text(value.get("provider"), "Draft provider", 200),
            "model": bounded_text(value.get("model"), "Draft model", 200),
            "profile": profile, "indices": list(indices), "completed": parts}


def make_project(syllabus: str, title: str, content: str, engine: str = "Local template", *,
                 model: str = "", pending=None, accepted_syllabus=None) -> dict:
    return validate_project({"schema_version": 2, "title": title or "Untitled Course", "syllabus": syllabus,
                             "content": content, "engine": engine, "model": model, "pending": pending,
                             "accepted_syllabus": syllabus if accepted_syllabus is None else accepted_syllabus})


def validate_project(value) -> dict:
    if (not isinstance(value, dict) or type(value.get("schema_version")) is not int or
            value["schema_version"] not in {1, 2}):
        raise CourseError("Unsupported project format. Open a Course Framework version 1 or 2 JSON project.")
    return {"schema_version": 2,
            "title": bounded_text(value.get("title"), "Course title", 300),
            "syllabus": bounded_text(value.get("syllabus"), "Syllabus"),
            "content": bounded_text(value.get("content"), "Course material", MAX_OUTPUT),
            "engine": bounded_text(value.get("engine", "Imported"), "Engine", 200),
            "model": bounded_text(value.get("model", ""), "Model", 200),
            "accepted_syllabus": bounded_text(value.get("accepted_syllabus", value.get("syllabus")), "Accepted syllabus"),
            "pending": validate_pending(value.get("pending")) if value["schema_version"] == 2 else None}


def project_bytes(project: dict) -> bytes:
    return json.dumps(validate_project(project), ensure_ascii=False, indent=2).encode("utf-8")


def load_project(data: bytes) -> dict:
    if len(data) > MAX_FILE_BYTES:
        raise CourseError("Project exceeds the 8 MB file limit.")
    try:
        return validate_project(json.loads(data.decode("utf-8-sig")))
    except (UnicodeError, json.JSONDecodeError, RecursionError):
        raise CourseError("This is not a valid UTF-8 JSON course project.") from None


def atomic_write(path: str | Path, data: bytes):
    """Replace a saved project only after a complete, flushed write succeeds."""
    path = Path(path)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".course-", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary and temporary.exists():
            temporary.unlink()


def export_html(title: str, content: str) -> bytes:
    # Escape every character before embedding. Preview never executes course HTML/scripts.
    document = f"""<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title><style>
body{{font:16px/1.65 system-ui,sans-serif;max-width:960px;margin:40px auto;padding:0 24px;color:#18253b}}
pre{{white-space:pre-wrap;overflow-wrap:anywhere;font:inherit}}@media print{{body{{margin:0}}}}
</style><h1>{html.escape(title)}</h1><pre>{html.escape(content)}</pre></html>"""
    return document.encode("utf-8")


def export_bundle(project: dict) -> bytes:
    project = validate_project(project)
    project = validate_project({**project, "syllabus": project["accepted_syllabus"], "pending": None})
    target = io.BytesIO()
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("course.md", project["content"])
        archive.writestr("course.html", export_html(project["title"], project["content"]))
        archive.writestr("project.json", project_bytes(project))
        archive.writestr("syllabus.txt", project["syllabus"])
        archive.writestr("README.txt", "Edit project.json with Course Framework. HTML is a safe, printable text view of the Markdown source.\nReview all content and answer keys before teaching. API credentials are not included.\n")
    return target.getvalue()
