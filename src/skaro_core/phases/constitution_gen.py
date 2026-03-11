"""Generate Constitution from a short project idea description (no repo scan)."""

from __future__ import annotations

from skaro_core.llm.base import LLMMessage
from skaro_core.phases.base import BasePhase, PhaseResult


def _default_example_constitution() -> str:
    """Load a generic example constitution (e.g. python-cli preset) for empty-input fallback."""
    try:
        from skaro_core.artifacts import TEMPLATES_PKG_DIR
        if TEMPLATES_PKG_DIR:
            preset = TEMPLATES_PKG_DIR / "constitution-presets" / "python-cli.md"
            if preset.exists():
                return preset.read_text(encoding="utf-8")
    except Exception:
        pass
    return """# Constitution: Project

## Stack
- Language: (specify)
- Framework: (specify or N/A)
- Database: N/A
- Infrastructure: (specify)

## Coding Standards
- Linter: (infer)
- Formatter: (infer)
- Naming: (conventions)
- Max function length: 50 lines
- Max nesting depth: 4

## Testing
- Minimum coverage: 70%
- Framework: pytest
- Required: for core logic

## Constraints
- (list constraints)

## Security
- Authorization: (approach)
- Input validation: (approach)
- Secrets: env vars, never in code

## LLM Rules
- Do not leave stubs without explicit TODO
- Do not duplicate code
- If unsure, ask
- Always generate AI_NOTES.md per template
"""


class ConstitutionGenPhase(BasePhase):
    """Generate a constitution document from a free-form project description."""

    phase_name = "constitution_gen"

    async def run(self, task: str | None = None, **kwargs) -> PhaseResult:
        """Run constitution generation. Uses description and/or existing_constitution."""
        description = (task or "").strip() or (kwargs.get("description") or "").strip()
        existing = (kwargs.get("existing_constitution") or "").strip()
        default_example = (kwargs.get("default_example") or "").strip() or _default_example_constitution()
        content = await self.generate_from_description(
            description=description,
            existing_constitution=existing,
            default_example=default_example,
        )
        if not content or not content.strip():
            fallback = existing if existing else default_example
            return PhaseResult(
                success=bool(fallback),
                message="LLM returned no content; using existing or example." if fallback else "No content available.",
                data={"content": fallback},
            )
        return PhaseResult(success=True, message="", data={"content": content})

    async def generate_from_description(
        self,
        description: str,
        existing_constitution: str = "",
        default_example: str = "",
    ) -> str:
        """Generate or refine constitution. Pass existing + user message, or use default example when empty."""
        prompt_template = self._load_prompt_template("constitution-from-idea")
        if not prompt_template:
            return existing_constitution or default_example

        system = f"# LANGUAGE\n\n{self._lang_instruction()}\n\n---\n\n{prompt_template}"
        example = default_example or _default_example_constitution()

        if existing_constitution.strip():
            user = f"Current constitution:\n\n{existing_constitution}\n\n"
            if description:
                user += f"User request: {description}\n\nReturn ONLY the updated constitution document (no code fence, no preamble)."
            else:
                user += "Refine and improve this constitution following best practices. Return ONLY the constitution document."
        elif description.strip():
            user = description.strip()
        else:
            user = (
                "The user provided no description. Generate a general-purpose project Constitution "
                "using the structure below as reference. Adapt it for a generic software project.\n\n"
                f"Structure reference:\n\n{example}\n\nReturn ONLY the constitution document."
            )

        if self.config.lang != "en":
            user += f"\n\n---\nReminder: {self._lang_instruction()}"

        messages = [
            LLMMessage(role="system", content=system),
            LLMMessage(role="user", content=user),
        ]
        response = await self._stream_collect(messages, min_tokens=4096)
        from skaro_core.phases._import_parser import _unwrap_fenced
        raw = _unwrap_fenced(response.strip()) if response else ""
        if raw and raw.strip():
            return raw
        return existing_constitution or example
