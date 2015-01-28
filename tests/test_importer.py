from datetime import datetime

from pytz import UTC

from watson.importers import get_importer, ICSImporter

try:
    from io import StringIO
except ImportError:
    from StringIO import StringIO  # noqa


CALENDAR = """
BEGIN:VCALENDAR
PRODID:-//Microsoft Corporation//Outlook 14.0 MIMEDIR//EN
VERSION:2.0
METHOD:PUBLISH
X-CALSTART:20141103T073000Z
X-CALEND:20141107T163000Z
X-CLIPSTART:20141102T230000Z
X-CLIPEND:20141107T230000Z
X-WR-RELCALID:{0000002E-B668-8D56-3089-3A6F8F29D511}
X-PRIMARY-CALENDAR:TRUE
X-MS-OLK-WKHRSTART;TZID="Paris, Madrid":080000
X-MS-OLK-WKHREND;TZID="Paris, Madrid":183000
X-MS-OLK-WKHRDAYS:MO,TU,WE,TH,FR
BEGIN:VTIMEZONE
TZID:Paris\, Madrid
BEGIN:STANDARD
DTSTART:16011028T030000
RRULE:FREQ=YEARLY;BYDAY=-1SU;BYMONTH=10
TZOFFSETFROM:+0200
TZOFFSETTO:+0100
END:STANDARD
BEGIN:DAYLIGHT
DTSTART:16010325T020000
RRULE:FREQ=YEARLY;BYDAY=-1SU;BYMONTH=3
TZOFFSETFROM:+0100
TZOFFSETTO:+0200
END:DAYLIGHT
END:VTIMEZONE
BEGIN:VEVENT
DTEND:20141103T113000Z
DTSTAMP:20141127T082912Z
DTSTART:20141103T073000Z
SEQUENCE:0
DESCRIPTION;LANGUAGE=fr:foo
TRANSP:OPAQUE
UID:Rd/IDEDZ40q+crttazpjtA==
X-MICROSOFT-CDO-BUSYSTATUS:BUSY
END:VEVENT
BEGIN:VEVENT
DTEND:20141103T173000Z
DTSTAMP:20141127T082912Z
DTSTART:20141103T123000Z
SEQUENCE:0
DESCRIPTION;LANGUAGE=fr:bar
TRANSP:OPAQUE
UID:EtMj7XHZFUSHLtAqkQAmOg==
X-MICROSOFT-CDO-BUSYSTATUS:BUSY
END:VEVENT
BEGIN:VEVENT
DTEND:20141104T113000Z
DTSTAMP:20141127T082912Z
DTSTART:20141104T070000Z
SEQUENCE:0
DESCRIPTION;LANGUAGE=fr:lol
TRANSP:OPAQUE
UID:nQ8CDhWzR0C+otwspfAUcQ==
X-MICROSOFT-CDO-BUSYSTATUS:BUSY
END:VEVENT
END:VCALENDAR
"""


def test_get_importer():
    assert isinstance(get_importer('ics', str), ICSImporter)
    assert isinstance(get_importer('ical', str), ICSImporter)
    assert isinstance(get_importer('.ics', str), ICSImporter)
    assert get_importer('.txt', str) is None
    assert get_importer('json', str) is None


def test_ics_importer():
    frames = []

    importer = ICSImporter(
        lambda *args, **kwargs: frames.append((args, kwargs))
    )

    importer.parse(StringIO(CALENDAR))

    assert len(frames) == 3
    assert frames[0] == (
        (
            datetime(2014, 11, 3, 7, 30, tzinfo=UTC),
            datetime(2014, 11, 3, 11, 30, tzinfo=UTC),
            'foo'
        ),
        {'uid': 'Rd/IDEDZ40q+crttazpjtA==', 'tags': None, 'message': None}
    )
    assert frames[1] == (
        (
            datetime(2014, 11, 3, 12, 30, tzinfo=UTC),
            datetime(2014, 11, 3, 17, 30, tzinfo=UTC),
            'bar'
        ),
        {'uid': 'EtMj7XHZFUSHLtAqkQAmOg==', 'tags': None, 'message': None}
    )
    assert frames[2] == (
        (
            datetime(2014, 11, 4, 7, 0, tzinfo=UTC),
            datetime(2014, 11, 4, 11, 30, tzinfo=UTC),
            'lol'
        ),
        {'uid': 'nQ8CDhWzR0C+otwspfAUcQ==', 'tags': None, 'message': None}
    )
