"""Tests for the recipe-authoring tools (structured ingredients, full create,
patch fields, concise output)."""


async def test_create_recipe_accepts_flat_and_structured(invoke, fetcher):
    await invoke(
        "create_recipe",
        name="Mixed",
        ingredients=[
            "200 g basmati rice",
            {
                "quantity": 2,
                "food": {"id": "f1", "name": "egg"},
                "note": "large",
                "referenceId": "a1000001-0000-4000-8000-000000000001",
            },
        ],
        instructions=[
            "Boil the rice.",
            {
                "text": "Fry the eggs.",
                "title": "Eggs",
                "ingredientReferences": [
                    {"referenceId": "a1000001-0000-4000-8000-000000000001"}
                ],
            },
        ],
    )
    body = fetcher.last("PUT", "/api/recipes/")["json"]
    ings = body["recipeIngredient"]
    steps = body["recipeInstructions"]

    assert ings[0]["note"] == "200 g basmati rice"
    assert ings[1]["quantity"] == 2
    assert ings[1]["food"] == {
        "id": "f1",
        "name": "egg",
        "description": "",
        "aliases": [],
        "householdsWithIngredientFood": [],
    }
    # already a valid UUID -> passes through unchanged
    assert ings[1]["referenceId"] == "a1000001-0000-4000-8000-000000000001"
    assert steps[0]["ingredientReferences"] == []
    assert steps[1]["title"] == "Eggs"
    assert steps[1]["ingredientReferences"] == [
        {"referenceId": "a1000001-0000-4000-8000-000000000001"}
    ]


async def test_create_recipe_full_sets_metadata_tags_tools_and_image(invoke, fetcher):
    await invoke(
        "create_recipe_full",
        name="Full",
        description="A dish",
        org_url="https://example.com/r",
        total_time="30 min",
        prep_time="10 min",
        recipe_yield="4 Portionen",
        servings=2,
        image_url="https://example.com/img.jpg",
        ingredients=["1 onion"],
        instructions=["Chop the onion."],
        tags=[{"id": "t1", "name": "Quick"}],
        tools=[{"id": "k1", "name": "Pfanne"}],
    )
    body = fetcher.last("PUT", "/api/recipes/")["json"]
    assert body["description"] == "A dish"
    assert body["orgURL"] == "https://example.com/r"
    assert body["totalTime"] == "30 min"
    assert body["recipeServings"] == 2
    assert body["recipeYield"] == "4 Portionen"
    assert body["recipeIngredient"][0]["note"] == "1 onion"
    # slug derived from the name (Mealie requires it on organizer refs)
    assert body["tags"] == [{"id": "t1", "name": "Quick", "slug": "quick"}]
    assert body["tools"][0]["id"] == "k1"
    assert body["tools"][0]["slug"] == "pfanne"
    # image is scraped server-side after the recipe content is written
    assert fetcher.last("POST", "/image") is not None


async def test_patch_recipe_maps_all_fields(invoke, fetcher):
    await invoke(
        "patch_recipe",
        slug="test-recipe",
        total_time="35 min",
        prep_time="10 min",
        cook_time="25 min",
        perform_time="20 min",
        servings=4,
        org_url="https://example.com/r",
        recipe_yield="4 Portionen",
        tags=[{"id": "t1", "name": "Quick"}],
        tools=[{"id": "k1", "name": "Pfanne"}],
    )
    body = fetcher.last("PATCH", "/api/recipes/")["json"]
    assert body == {
        "recipeYield": "4 Portionen",
        "recipeServings": 4,
        "totalTime": "35 min",
        "prepTime": "10 min",
        "cookTime": "25 min",
        "performTime": "20 min",
        "orgURL": "https://example.com/r",
        "tags": [{"id": "t1", "name": "Quick", "slug": "quick"}],
        "tools": [{"id": "k1", "name": "Pfanne", "slug": "pfanne"}],
    }


async def test_get_recipe_concise_includes_orgurl_tags_tools(invoke, fetcher):
    fetcher.recipe = {
        **fetcher.recipe,
        "orgURL": "https://example.com/r",
        "tags": [{"id": "t1", "name": "Quick", "slug": "quick"}],
        "tools": [
            {"id": "k1", "name": "Pfanne", "slug": "pfanne", "householdsWithTool": []}
        ],
    }
    out = await invoke("get_recipe_concise", slug="test-recipe")
    assert out["orgURL"] == "https://example.com/r"
    assert out["tags"] == [{"id": "t1", "name": "Quick", "slug": "quick"}]
    assert out["tools"][0]["name"] == "Pfanne"


async def test_patch_recipe_merges_settings_onto_current(invoke, fetcher):
    await invoke("patch_recipe", slug="test-recipe", settings={"showAssets": False})

    body = fetcher.last("PATCH", "/api/recipes/")["json"]
    # Mealie drops toggles omitted from a settings PATCH, so the tool reads the
    # current object and sends it whole -- locked must survive untouched.
    assert body["settings"] == {
        "public": False,
        "showNutrition": True,
        "showAssets": False,
        "landscapeView": False,
        "disableComments": False,
        "locked": True,
    }


async def test_patch_recipe_settings_reads_current_first(invoke, fetcher):
    await invoke("patch_recipe", slug="test-recipe", settings={"public": True})

    # the merge needs the existing settings, so a GET precedes the PATCH
    methods = [r["method"] for r in fetcher.requests]
    assert methods == ["GET", "PATCH"]


async def test_patch_recipe_without_settings_issues_no_extra_get(invoke, fetcher):
    await invoke("patch_recipe", slug="test-recipe", description="Just a description")

    assert [r["method"] for r in fetcher.requests] == ["PATCH"]
    assert "settings" not in fetcher.last("PATCH", "/api/recipes/")["json"]


async def test_create_recipe_full_merges_settings_onto_seeded(invoke, fetcher):
    await invoke(
        "create_recipe_full", name="Visible", settings={"showAssets": True}
    )

    body = fetcher.last("PUT", "/api/recipes/")["json"]
    assert body["settings"]["showAssets"] is True
    # the toggles Mealie seeded are preserved rather than reset to model defaults
    assert body["settings"]["locked"] is True
    assert body["settings"]["showNutrition"] is True


async def test_create_recipe_full_without_settings_preserves_seeded(invoke, fetcher):
    await invoke("create_recipe_full", name="Plain")

    body = fetcher.last("PUT", "/api/recipes/")["json"]
    assert body["settings"]["locked"] is True
    assert body["settings"]["showAssets"] is True
