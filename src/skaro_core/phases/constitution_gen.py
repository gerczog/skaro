"""Generate Constitution from a short project idea description (no repo scan)."""

from __future__ import annotations

from skaro_core.llm.base import LLMMessage
from skaro_core.phases.base import BasePhase, PhaseResult


class ConstitutionGenPhase(BasePhase):
    """Generate a constitution document from a free-form project description."""

    phase_name = "constitution_gen"

    async def run(self, task: str | None = None, **kwargs) -> PhaseResult:
        """Run constitution generation. Uses task or description kwarg as the idea."""
        description = (task or "").strip() or (kwargs.get("description") or "").strip()
        if not description:
            return PhaseResult(
                success=False,
                message="Description is required for constitution generation.",
                data={},
            )
        content = await self.generate_from_description(description)
        if not content or not content.strip():
            return PhaseResult(
                success=False,
                message="LLM returned empty content.",
                data={"content": ""},
            )
        return PhaseResult(
            success=True,
            message="",
            data={"content": content},
        )

    async def generate_from_description(self, description: str) -> str:
        """Call LLM to generate constitution text from user description. Returns raw markdown."""
        prompt_template = self._load_prompt_template("constitution-from-idea")
        if not prompt_template:
            return ""

        system = f"# LANGUAGE\n\n{self._lang_instruction()}\n\n---\n\n{prompt_template}"
        user = description.strip()
        if self.config.lang != "en":
            user += f"\n\n---\nReminder: {self._lang_instruction()}"

        messages = [
            LLMMessage(role="system", content=system),
            LLMMessage(role="user", content=user),
        ]
        response = await self._stream_collect(messages, min_tokens=4096)

        from skaro_core.phases._import_parser import _unwrap_fenced
        return _unwrap_fenced(response.strip())
