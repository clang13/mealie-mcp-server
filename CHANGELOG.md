# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- `parse_ingredient` and `parse_ingredients` wrap Mealie's server-side
  ingredient parser, resolving free text such as `"1/4 cup chopped onion"`
  against the instance's food and unit vocabulary in one request instead of
  searching `get_foods` and `get_units` per ingredient. Results are flattened to
  `{input, confidence, quantity, unit, food, note}` and can be passed straight
  to `create_recipe_full`; `verbose=True` returns Mealie's untouched response.
  Both accept Mealie's `nlp`, `brute`, and `openai` parser backends.
