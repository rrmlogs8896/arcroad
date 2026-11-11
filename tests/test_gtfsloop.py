"""Buses through the loop area, from a small GTFS feed built by hand."""
import zipfile

from pipeline.gtfsloop import against, patterns, read

GATES = [{"name": "A", "lon": 78.0, "lat": 17.0}, {"name": "B", "lon": 78.01, "lat": 17.0},
         {"name": "C", "lon": 78.01, "lat": 17.01}]


def feed(tmp_path, calendar=True):
    files = {
        "stops.txt": "stop_id,stop_lat,stop_lon\ns1,17.0,78.0005\ns2,17.0,78.0102\ns3,17.0101,78.01\nfar,17.2,78.2\n",
        "routes.txt": "route_id,route_short_name\nr1,10H\nr2,218\n",
        "trips.txt": "route_id,service_id,trip_id\nr1,WK,t1\nr1,WK,t2\nr2,WK,t3\nr2,SUN,t4\n",
        "stop_times.txt": ("trip_id,stop_id,stop_sequence\n"
                           "t1,s1,1\nt1,s2,2\nt1,s3,3\n"
                           "t2,s1,1\nt2,s2,2\nt2,s3,3\n"
                           "t3,s3,1\nt3,s2,2\nt3,far,3\n"
                           "t4,s1,1\nt4,s2,2\n"),
    }
    if calendar:
        files["calendar.txt"] = ("service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday\n"
                                 "WK,1,1,1,1,1,0,0\nSUN,0,0,0,0,0,0,1\n")
    p = tmp_path / "gtfs.zip"
    with zipfile.ZipFile(p, "w") as z:
        for n, t in files.items():
            z.writestr(n, t)
    return p


def test_trips_are_counted_by_pattern_on_a_weekday_only(tmp_path):
    r = patterns(read(feed(tmp_path)), GATES)
    assert r["patterns"][("10H", ("A", "B", "C"))] == 2
    assert r["patterns"][("218", ("C", "B"))] == 1
    assert r["trips_counted"] == 3 and r["stops_in_area"] == 3 and not r["calendar_missing"]


def test_a_feed_without_a_calendar_counts_every_trip_and_says_so(tmp_path):
    r = patterns(read(feed(tmp_path, calendar=False)), GATES)
    assert r["calendar_missing"] and r["trips_counted"] == 4


def test_against_the_loop_is_every_step_that_does_not_follow_its_order():
    assert against(("A", "B", "C"), ["A", "B", "C"]) == []
    assert against(("C", "B"), ["A", "B", "C"]) == [("C", "B")]
    assert against(("C", "A"), ["A", "B", "C"]) == []  # C to A closes the ring: with the loop
