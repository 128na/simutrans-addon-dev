# Addons

Create each new addon in its own directory, for example `addons/<addon-name>/`. Keep its source, assets, documentation, and build configuration together so it can be developed and validated independently.

Each addon should provide a README describing, as applicable:

- Purpose and included content
- Supported Simutrans version and pakset
- License and attribution for code and assets
- Required tools and setup
- Build, installation, and in-game validation steps

Makeobj is available on `PATH` and can be invoked as `makeobj`. Document the pak size and any addon-specific build command or prerequisites.

Use the smallest structure that fits the addon. Add shared tooling at the repository root only when multiple addons need it; document any shared commands here or in the root README.
