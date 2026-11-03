from rekit.catalog.matcher import ApplicationMatcher
from rekit.models.application import Application, ApplicationSource


def make_application(
    name: str,
    source: ApplicationSource,
    version: str | None = None,
    publisher: str | None = None,
    package_id: str | None = None,
    install_location: str | None = None,
) -> Application:
    return Application(
        name=name,
        source=source,
        version=version,
        publisher=publisher,
        package_id=package_id,
        install_location=install_location,
    )


def test_merges_registry_and_winget_records_by_normalized_name() -> None:
    registry = make_application(
        name="Google Chrome",
        source=ApplicationSource.REGISTRY,
        version="130.0",
        publisher="Google LLC",
        install_location=r"C:\Program Files\Google\Chrome",
    )
    winget = make_application(
        name="Google.Chrome",
        source=ApplicationSource.WINGET,
        version="130.0",
        package_id="Google.Chrome",
    )

    result = ApplicationMatcher().merge([registry, winget])

    assert len(result) == 1
    assert result[0].name == "Google Chrome"
    assert result[0].publisher == "Google LLC"
    assert result[0].package_id == "Google.Chrome"
    assert result[0].install_location == r"C:\Program Files\Google\Chrome"
    assert result[0].source is ApplicationSource.REGISTRY


def test_matches_package_identifier_with_publisher_prefix() -> None:
    registry = make_application(
        name="Visual Studio Code",
        source=ApplicationSource.REGISTRY,
        version="1.95.0",
        publisher="Microsoft Corporation",
    )
    winget = make_application(
        name="Microsoft.VisualStudioCode",
        source=ApplicationSource.WINGET,
        version="1.95.0",
        package_id="Microsoft.VisualStudioCode",
    )

    result = ApplicationMatcher().merge([registry, winget])

    assert len(result) == 1
    assert result[0].name == "Visual Studio Code"
    assert result[0].package_id == "Microsoft.VisualStudioCode"


def test_deduplicates_registry_entries_from_multiple_views() -> None:
    first = make_application(
        name="Example App",
        source=ApplicationSource.REGISTRY,
        version="2.0",
        publisher="Example Publisher",
        install_location=r"C:\Program Files\Example",
    )
    second = make_application(
        name="Example-App",
        source=ApplicationSource.REGISTRY,
        version="2.0",
        publisher="Example Publisher",
        install_location=r"C:\Program Files\Example",
    )

    result = ApplicationMatcher().merge([first, second])

    assert len(result) == 1
    assert result[0].name == "Example App"


def test_keeps_records_with_conflicting_versions_separate() -> None:
    first = make_application(
        name="Example App",
        source=ApplicationSource.REGISTRY,
        version="1.0",
    )
    second = make_application(
        name="Example App",
        source=ApplicationSource.WINGET,
        version="2.0",
        package_id="Example.App",
    )

    result = ApplicationMatcher().merge([first, second])

    assert len(result) == 2


def test_keeps_records_with_conflicting_publishers_separate() -> None:
    first = make_application(
        name="Example App",
        source=ApplicationSource.REGISTRY,
        publisher="Publisher One",
    )
    second = make_application(
        name="Example-App",
        source=ApplicationSource.WINGET,
        publisher="Publisher Two",
        package_id="Example.App",
    )

    result = ApplicationMatcher().merge([first, second])

    assert len(result) == 2


def test_keeps_records_with_different_install_locations_separate() -> None:
    first = make_application(
        name="Example App",
        source=ApplicationSource.REGISTRY,
        install_location=r"C:\Apps\Example",
    )
    second = make_application(
        name="Example App",
        source=ApplicationSource.REGISTRY,
        install_location=r"D:\Apps\Example",
    )

    result = ApplicationMatcher().merge([first, second])

    assert len(result) == 2


def test_does_not_automatically_merge_manual_entries() -> None:
    manual = make_application(
        name="Example App",
        source=ApplicationSource.MANUAL,
        version="1.0",
    )
    registry = make_application(
        name="Example App",
        source=ApplicationSource.REGISTRY,
        version="1.0",
    )

    result = ApplicationMatcher().merge([manual, registry])

    assert len(result) == 2
    assert result[0] is manual
    assert result[1] is registry


def test_keeps_transitive_matches_separate_when_group_members_conflict() -> None:
    first = make_application(
        name="Example App",
        source=ApplicationSource.REGISTRY,
        version="1.0",
        publisher="Publisher One",
    )
    bridge = make_application(
        name="Example App",
        source=ApplicationSource.WINGET,
        version="1.0",
    )
    conflicting = make_application(
        name="Example App",
        source=ApplicationSource.REGISTRY,
        version="1.0",
        publisher="Publisher Two",
    )

    result = ApplicationMatcher().merge([first, bridge, conflicting])

    assert len(result) == 2
