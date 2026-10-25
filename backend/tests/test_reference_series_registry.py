"""P10 · the reference library cites every fact it states.

A reference value is shown only with a verifiable source: a public URL, or a
document identified by its fingerprint, with the pages where it is written.
A series with nothing cited is marked as needing the manufacturer's manual."""

from catalogs.reference_views import registry


def test_every_source_is_verifiable():
    for key, source in registry()["sources"].items():
        public = bool(source.get("url")) and str(source["url"]).startswith("https://")
        document = bool(source.get("sha256")) and bool(source.get("pages_total"))
        assert public or document, key
        assert source.get("title") and source.get("holder"), key


def test_every_fact_and_article_cites_a_known_source_and_its_pages():
    data = registry()
    for series in data["series"]:
        for item in [*series.get("facts", []), *series.get("articles", [])]:
            assert item["source"] in data["sources"], (series["id"], item)
            assert item["source"] in series["sources"], (series["id"], item)
            source = data["sources"][item["source"]]
            if not source.get("url"):
                # A private document is citable only with the exact pages.
                assert item.get("pages"), (series["id"], item)


def test_seed_values_only_restate_cited_facts():
    for series in registry()["series"]:
        seed, facts = series.get("seed") or {}, {fact["label"]: fact["value"] for fact in series.get("facts", [])}
        if "depth_mm" in seed:
            assert f"{seed['depth_mm']} mm" in facts.values(), series["id"]
        if "chamber_count" in seed:
            assert seed["chamber_count"] in facts.values(), series["id"]


def test_series_without_cited_data_need_the_manufacturer_manual():
    for series in registry()["series"]:
        empty = not series.get("facts") and not series.get("articles")
        assert series["needs_manufacturer_manual"] is empty, series["id"]
        if empty:
            assert series["missing"], series["id"]
        # A reference never claims authority: prices and fabrication come from the workshop.
        assert not series["capabilities"]["quotable"] and not series["capabilities"]["manufacturable"]


def test_a_technical_sheet_cites_its_documents_and_creates_a_series_payload():
    from catalogs.series_serializers import SeriesCreateSerializer

    data = registry()
    sheets = [series for series in data["series"] if series.get("technical")]
    assert sheets, "PRO6004 carries the manufacturer's cutting facts"
    for series in sheets:
        technical = series["technical"]
        assert set(technical["sources"]) <= set(data["sources"])
        for row in technical["profiles"] + technical["glazing"] + technical["hardware"]:
            assert row["source"] in data["sources"] and row["pages"]
        strip = lambda row: {key: value for key, value in row.items() if key not in ("source", "pages")}  # noqa: E731
        payload = SeriesCreateSerializer(data={
            "template_id": "pvc-casement-60-70", "template_version": 1,
            "name": series["seed"]["name"], "code": series["seed"]["code"],
            "manufacturer": series["seed"]["manufacturer"], "rules": technical["rules"],
            "profiles": [strip(row) for row in technical["profiles"]],
            "glazing": [strip(row) for row in technical["glazing"]],
            "hardware": [strip(row) for row in technical["hardware"]],
        })
        assert payload.is_valid(), payload.errors
