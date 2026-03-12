"""Constitution endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from skaro_core.artifacts import TEMPLATES_PKG_DIR, ArtifactManager
from skaro_web.api.deps import (
    broadcast,
    get_am,
    get_project_root,
    get_ws_manager,
    llm_phase,
)
from skaro_web.api.schemas import ContentBody, GenerateFromIdeaBody

router = APIRouter(prefix="/api/constitution", tags=["constitution"])

# ── Presets directory (ships with the package) ─────
_PRESETS_DIR = TEMPLATES_PKG_DIR / "constitution-presets" if TEMPLATES_PKG_DIR else None

# Registry: id → (label, category, filename)
_PRESET_REGISTRY: list[dict[str, str]] = [
    {"id": "react", "name": "React", "category": "frontend", "file": "react.md"},
    {"id": "vue", "name": "Vue.js", "category": "frontend", "file": "vue.md"},
    {
        "id": "sveltekit",
        "name": "SvelteKit",
        "category": "frontend",
        "file": "sveltekit.md",
    },
    {"id": "nextjs", "name": "Next.js", "category": "frontend", "file": "nextjs.md"},
    {"id": "angular", "name": "Angular", "category": "frontend", "file": "angular.md"},
    {"id": "fastapi", "name": "FastAPI", "category": "backend", "file": "fastapi.md"},
    {"id": "django", "name": "Django", "category": "backend", "file": "django.md"},
    {
        "id": "python-cli",
        "name": "Python CLI",
        "category": "cli",
        "file": "python-cli.md",
    },
    {
        "id": "express",
        "name": "Express.js",
        "category": "backend",
        "file": "express.md",
    },
    {"id": "nestjs", "name": "NestJS", "category": "backend", "file": "nestjs.md"},
    {
        "id": "react-native",
        "name": "React Native",
        "category": "mobile",
        "file": "react-native.md",
    },
    {"id": "flutter", "name": "Flutter", "category": "mobile", "file": "flutter.md"},
    {
        "id": "kotlin-mp",
        "name": "Kotlin MP",
        "category": "mobile",
        "file": "kotlin-mp.md",
    },
]


@router.get("")
async def get_constitution(am: ArtifactManager = Depends(get_am)):
    return {
        "content": am.read_constitution(),
        "has_constitution": am.has_constitution,
        "validation": am.validate_constitution(),
    }


@router.post("/validate")
async def validate_constitution(am: ArtifactManager = Depends(get_am)):
    result = am.validate_constitution()
    is_valid = all(result.values()) if result else False
    if is_valid:
        am.mark_constitution_validated()
    return {"success": True, "valid": is_valid, "checks": result}


@router.put("")
async def save_constitution(
    request: Request,
    payload: ContentBody,
    am: ArtifactManager = Depends(get_am),
):
    am.write_constitution(payload.content)
    am.generate_project_gitignore(payload.content)
    await broadcast(request, {"event": "artifact:updated", "artifact": "constitution"})
    return {"success": True}


@router.get("/presets")
async def list_presets():
    """Return list of available constitution presets (metadata only)."""
    return {"presets": _PRESET_REGISTRY}


def _default_constitution_example() -> str:
    """Load example constitution for empty-input / fallback (e.g. python-cli preset)."""
    if _PRESETS_DIR is None:
        return ""
    path = _PRESETS_DIR / "python-cli.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


@router.post("/generate")
async def generate_constitution_from_idea(
    payload: GenerateFromIdeaBody,
    project_root=Depends(get_project_root),
    ws_manager=Depends(get_ws_manager),
    am: ArtifactManager = Depends(get_am),
):
    """Generate constitution from idea (or refine existing). Pass description and/or use existing constitution."""
    try:
        from skaro_core.phases.constitution_gen import ConstitutionGenPhase
    except ModuleNotFoundError as e:
        raise HTTPException(
            status_code=501,
            detail="Upgrade Skaro to a version with constitution-from-idea (install from your fork or latest main).",
        ) from e
    existing = (am.read_constitution() or "").strip()
    default_example = _default_constitution_example()
    description = (payload.description or "").strip()
    phase = ConstitutionGenPhase(project_root=project_root)
    async with llm_phase(ws_manager, "constitution-generate", phase):
        content = await phase.generate_from_description(
            description=description,
            existing_constitution=existing,
            default_example=default_example,
        )
    if not content or not content.strip():
        content = existing or default_example
        return {
            "success": bool(content),
            "message": "No new content; returning existing or example.",
            "content": content or "",
        }
    return {"success": True, "content": content}


@router.get("/presets/{preset_id}")
async def get_preset(preset_id: str):
    """Return the full markdown content for a specific preset."""
    entry = next((p for p in _PRESET_REGISTRY if p["id"] == preset_id), None)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Preset '{preset_id}' not found")
    if _PRESETS_DIR is None:
        raise HTTPException(status_code=500, detail="Templates directory not found")
    path = _PRESETS_DIR / entry["file"]
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Preset file missing: {entry['file']}")
    return {"id": preset_id, "content": path.read_text(encoding="utf-8")}
