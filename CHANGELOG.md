# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- `create_recipe_full` and `patch_recipe` accept a `nutrition` argument covering
  Mealie's full key set (calories, macros, cholesterol, sodium, sugars, and the
  fat breakdown). Numbers are converted to the strings Mealie stores. Mealie
  replaces the whole nutrition object on write, so `patch_recipe` clears any key
  not passed.
- `create_recipe_full` and `patch_recipe` accept a `notes` argument for Mealie's
  `{title, text}` notes. Mealie requires a title but accepts an empty one, so
  the title defaults to `""`. `patch_recipe` replaces all notes; an empty list
  clears them.
- `upload_recipe_asset_file` takes optional `name` and `icon` arguments to
  override the defaults.

### Fixed

- `upload_recipe_asset_file` failed with a 422 on every call. `POST
  /api/recipes/{slug}/assets` requires `name`, `icon`, and `extension` in the
  multipart body alongside the file, and only the file was sent. The extension
  is derived from the filename, the name defaults to the filename stem, and the
  icon defaults to `mdi-file`, matching the Mealie web UI. A filename without an
  extension is now rejected before the request rather than returning a 400.
