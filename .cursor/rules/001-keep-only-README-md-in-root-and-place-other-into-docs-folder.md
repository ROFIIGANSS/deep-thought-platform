Keep only the main `README.md` in the root directory of the project.

All other Markdown documentation files (of any name except `README.md`) must be placed inside the `docs/` folder (directly or within its subfolders).  
This includes—but is not limited to—technical reference, API docs, guides, design notes, ADRs, contributing instructions, usage docs, roadmap, protocol explanations, architecture diagrams, release instructions, etc.

Do not save or keep Markdown files (e.g., `INSTRUCTIONS.md`, `HOWTO.md`, `usage.md`, `architecture.md`, `api.md`, `ECHO.md`, etc.) in the root or any directory outside of `docs/` except for this single `README.md`.

- If you come across a Markdown file in the root besides `README.md`, move it to `docs/`.
- If you need to create new documentation or explanation in Markdown, place it in `docs/`, not root.
- The only permitted Markdown file in the root of the repository is `README.md`.

_Note: This rule does **not** apply to code comments, Python docstrings, or plaintext files. It is only for Markdown (`.md`, `.markdown`) files intended for human reading._

Summary:  
Root directory: Only allow `README.md`.  
Other docs: Always under `docs/`.
