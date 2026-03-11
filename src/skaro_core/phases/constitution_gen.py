"""Generate Constitution from a short project idea description (no repo scan)."""

from __future__ import annotations

from pathlib import Path

from skaro_core.llm.base import LLMMessage
from skaro_core.phases.base import BasePhase


class ConstitutionGenPhase(BasePhase):
    """Generate a constitution document from a free-form project description."""

    phase_name = "constitution_gen"

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
