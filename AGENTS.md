# Repository instructions

## Scope and layout

- This repository is the active monorepo for new Simutrans addons.
- Add each new addon as an independent project under `addons/<addon-name>/`.
- Keep addon-specific source, assets, documentation, build configuration, and tests within that addon's directory unless a tool is genuinely shared.
- Do not impose a repository-wide language, package manager, or build system. Follow the selected addon's existing conventions.
- The sibling repositories `../iss`, `../rtx`, and `../rtg` are archived projects. Treat them as read-only references unless the user explicitly requests work there.

## Addon development

- Before editing, read the target addon's README and relevant local instructions. Prefer instructions closest to the files being changed.
- Preserve existing addon behavior and formats. Validate generated Simutrans data with the addon's documented tools when available.
- Do not assume compatibility across Simutrans versions or paksets; record and follow the target addon's stated compatibility.
- Makeobj is available on `PATH`; invoke it as `makeobj` rather than hard-coding a machine-specific executable path. Use the pak size matching the target pakset.
- Keep generated files out of source control unless the addon explicitly treats them as deliverables. Use addon-local ignore rules for addon-specific build outputs.
- Check the license for the addon and for any reused code, documentation, or assets. The repository-level license does not automatically replace an addon's own license.
- When adding an addon, document its purpose, supported Simutrans version and pakset (if known), license, prerequisites, and build or validation steps.

## Working with archived projects

- Use archived repositories to understand prior formats and workflows, not as the default destination for new work.
- Do not copy archived code or assets without checking their original license and attribution requirements.
- Do not change archived repositories as a side effect of work in this monorepo.

## Validation

- Use the target addon's documented build, lint, and test commands.
- If an addon has no automated checks, validate the specific output or behavior affected and report what could not be checked.
- Avoid running unrelated addon tooling when a change is scoped to one addon.
