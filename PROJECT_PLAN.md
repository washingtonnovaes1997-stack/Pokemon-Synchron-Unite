# Pokemon Synchron Unite — Project Foundation

This repository is the custom game layer. The upstream battle/game engine is fetched automatically from `rh-hideout/pokeemerald-expansion` during CI builds.

## Goal

Build a GBA Pokemon fangame with original regions, maps, tilesets, protagonists, rivals, enemy team, gyms, story, encounters, NPCs, interiors and progression while using pokeemerald-expansion only as the underlying engine.

## Automation model

1. GitHub Actions checks out this repository.
2. CI downloads a pinned pokeemerald-expansion revision.
3. Files under `overlay/` are copied over the engine checkout.
4. Scripts under `tools/` validate the project.
5. The engine is compiled with the ARM toolchain.
6. The resulting `.gba` is uploaded as a GitHub Actions artifact.

## Repository folders

- `game/` — high-level definitions for regions, maps, gyms, characters and story.
- `overlay/` — files that directly replace/add files in pokeemerald-expansion.
- `assets/` — original/custom graphics, tilesets and other source assets.
- `tools/` — generators and validators.
- `.github/workflows/` — automatic build pipeline.

## Important

The project intentionally does not treat Hoenn maps as the game world. New maps and visual assets will be created as original content and connected to the engine.
