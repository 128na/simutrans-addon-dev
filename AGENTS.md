# Repository Guidelines

## Project Structure & Module Organization

This repository is a monorepo for Simutrans addons. Develop new addons as independent projects under `addons/<addon-name>/`; keep each addon's source, assets, documentation, configuration, and tests together. Shared tooling belongs at the root only when multiple addons use it. The sibling repositories `../iss`, `../rtx`, and `../rtg` are archived references, not part of this repository's normal change scope.

## Build, Test, and Development Commands

There is no repository-wide build system. Follow the target addon's README and scripts. For addons built from `.dat` definitions, Makeobj is available on `PATH`; from the addon's directory, use `makeobj pak128 .\dist\example.pak .\src\example.dat` (replace `pak128` with the target pakset size). Keep generated output in an addon's documented build directory.

## Coding Style & Naming Conventions

Follow the language, formatter, and naming style already used by the target addon; do not impose a monorepo-wide toolchain. Use clear, lowercase, hyphen-separated addon directory names (for example, `addons/urban-bridges/`). Keep addon-specific config and dependencies local to that project.

## Testing Guidelines

Run only the build, lint, and test commands documented for the addon you change. Validate generated pak files or other affected outputs with the addon's intended tools and pakset. If no automated checks exist, perform a focused manual validation and report what remains unchecked.

## Commit & Pull Request Guidelines

The available Git history does not establish a commit-message convention; use concise, imperative summaries that name the addon or change, such as `Add urban bridge set`. Pull requests should explain the user-visible change, identify the affected addon, link related issues when applicable, and include screenshots for visual or in-game asset changes. Note build or validation commands and their results.

## Addon Documentation & Licensing

Each addon README should state its purpose, supported Simutrans version and pakset when known, license, prerequisites, and build or validation steps. Check licenses and attribution before reusing archived code or assets; the root license does not automatically cover an addon's contents.
