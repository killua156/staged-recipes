"""Functional checks for the conda-forge pksuid package.

Upstream pins pybase62 ==0.4.3 and the recipe patches that to >=0.4.3 so the
package can be built against the pybase62 conda-forge ships (1.0.0). These
checks exercise the encode/decode path that pin was protecting, so any real
incompatibility fails the build instead of surfacing in a user's pipeline.

The reference ID below is taken from upstream's own test suite (which is not
included in the sdist). It was generated with pybase62 0.4.3, so parsing it and
re-encoding it byte for byte proves the on-the-wire ID format is unchanged.
"""

from datetime import datetime, timezone

from pksuid import BODY_LENGTH, PKSUID, PKSUIDParseError, PKSUIDTimestampError

REFERENCE_ID = "test_24OjYtVsP8hbCZ4difNIQmyUMf9"
REFERENCE_TIMESTAMP = 1643508577
REFERENCE_PAYLOAD = b"\x98\xec\xce\x1d\xf0\x9eok\x0cc\x18\xc9\xde\x0c%\x9f"


def test_generation():
    generated = str(PKSUID("test"))
    prefix, uid = generated.split("_")
    assert len(generated) == 32, generated
    assert prefix == "test", prefix
    assert len(uid) == 27, uid


def test_round_trip():
    original = PKSUID("usr")
    parsed = PKSUID.parse(str(original))
    assert parsed.uid == original.uid
    assert parsed.prefix == "usr"
    assert PKSUID.parse_bytes(original.bytes()) == original
    assert len(original.payload) == BODY_LENGTH


def test_reference_id_format_is_stable():
    # The check that matters for the loosened pybase62 pin.
    parsed = PKSUID.parse(REFERENCE_ID)
    assert parsed.prefix == "test", parsed.prefix
    assert parsed.get_timestamp() == REFERENCE_TIMESTAMP, parsed.get_timestamp()
    assert parsed.payload == REFERENCE_PAYLOAD, parsed.payload
    assert parsed.bytes() == REFERENCE_ID.encode(), parsed.bytes()
    assert PKSUID.parse_bytes(REFERENCE_ID.encode()) == parsed


def test_timestamp_and_datetime():
    # Compared in UTC, since get_datetime() returns local time.
    parsed = PKSUID.parse(REFERENCE_ID)
    expected = datetime(2022, 1, 30, 2, 9, 37, tzinfo=timezone.utc)
    assert parsed.get_datetime().astimezone(timezone.utc) == expected

    future = REFERENCE_TIMESTAMP + 200
    assert PKSUID("test", timestamp=future).get_timestamp() == future


def test_ordering():
    earlier = PKSUID("test", timestamp=REFERENCE_TIMESTAMP)
    later = PKSUID("test", timestamp=REFERENCE_TIMESTAMP + 5)
    assert earlier < later
    assert later > earlier
    assert earlier <= earlier and earlier >= earlier
    assert earlier != later
    assert not earlier == Exception("not a pksuid")


def test_errors():
    for bad in ("sk_//24OjYtVsP8hbCZ4difNIQmyUMf9", "sk_24OjYtVsP8hbCZ4difNIQmyUMf924"):
        try:
            PKSUID.parse(bad)
        except PKSUIDParseError:
            pass
        else:
            raise AssertionError("expected PKSUIDParseError for %r" % bad)

    try:
        PKSUID("test", timestamp=0)
    except PKSUIDTimestampError:
        pass
    else:
        raise AssertionError("expected PKSUIDTimestampError for a pre-epoch timestamp")


if __name__ == "__main__":
    for name, check in sorted(globals().items()):
        if name.startswith("test_"):
            check()
            print("ok", name)
