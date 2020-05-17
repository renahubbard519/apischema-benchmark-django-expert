from _pytest.python_api import raises

from apischema.data import build_data


def test_build_data():
    lines = {
        "key1.0": "v0",
        "key1.2": "v2",
        "key2":   42,
    }
    assert build_data(lines.items()) == {"key1": ["v0", None, "v2"],
                                         "key2": 42}
    with raises(ValueError):
        build_data({"": ...}.items())
    with raises(ValueError):
        build_data({**lines, "key1.key3": ...}.items())
    with raises(ValueError):
        build_data({**lines, "0": ...}.items())