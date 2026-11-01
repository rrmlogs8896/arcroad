import io
import json
import zipfile

from pipeline import fieldkit as fk


def _loop_track():
    """Side A at lat 17.5000, side B 30 m north across a median; the drive goes 1 km east, U-turns, comes back."""
    pts, t = [], 1_793_500_000.0
    a_lat, b_lat, lon0 = 17.5000, 17.50027, 78.3000
    for k in range(0, 101):            # out along A's side, ~10 m steps
        pts.append((t, a_lat, lon0 + k * 0.0000943))
        t += 1
    for _ in range(20):                # waiting at the U-turn gap
        pts.append((t, a_lat + 0.00013, lon0 + 100 * 0.0000943))
        t += 1
    for k in range(100, -1, -1):       # back along B's side
        pts.append((t, b_lat, lon0 + k * 0.0000943))
        t += 1
    return pts, {"id": "SX", "a": [lon0, a_lat], "b": [lon0, b_lat]}


def test_scene_measures_the_detour_turnaround_and_wait():
    track, spot = _loop_track()
    sc = fk.scene(spot, track, [], [], network_m=2000)
    d = sc["driven"]
    assert d is not None
    assert 1800 < d["metres"] < 2300
    assert 900 < d["turnaround"]["from_a_m"] < 1100
    assert any(w["seconds"] >= 15 for w in d["waits"])
    assert d["path_1hz"][0][0] == 0.0


def test_photo_far_from_the_spot_is_not_attached():
    _, spot = _loop_track()
    near = {"file": "a.heic", "t": 1, "lat": 17.5001, "lon": 78.3001}
    far = {"file": "b.heic", "t": 2, "lat": 17.52, "lon": 78.33}
    nogps = {"file": "c.heic", "t": 3, "lat": None, "lon": None}
    got = fk.photos_for_spot([near, far, nogps], spot)
    assert [p["file"] for p in got] == ["a.heic"]


def test_handling_spike_is_flagged_not_counted_as_a_pothole():
    track, _ = _loop_track()
    t0 = track[10][0]
    accel = [(t0 + i * 0.01, 0.0, 0.0, 0.05) for i in range(3000)]
    accel[500] = (accel[500][0], 0.0, 0.0, 6.0)      # road jolt
    accel[1500] = (accel[1500][0], 0.0, 0.0, 6.0)    # handling jolt
    gravity = [(t, 0.0, 0.0, -9.8) for t, *_ in accel]
    gyro = [(t, 0.0, 0.0, 0.0) for t, *_ in accel]
    gyro[1500] = (gyro[1500][0], 3.0, 0.0, 0.0)
    ev = fk.jolts({"accel": accel, "gravity": gravity, "gyro": gyro}, track)
    assert [e["status"] for e in ev] == ["candidate", "handling?"]


def test_slow_spike_below_speed_floor_is_ignored():
    track, _ = _loop_track()
    t_wait = track[110][0]                           # inside the U-turn wait (speed ~0)
    accel = [(t_wait + i * 0.01, 0.0, 0.0, 0.05) for i in range(500)]
    accel[100] = (accel[100][0], 0.0, 0.0, 8.0)
    assert fk.jolts({"accel": accel}, track) == []


def test_sensor_logger_zip_reads_nanosecond_times():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("Location.csv", "time,seconds_elapsed,latitude,longitude,altitude,speed,bearing,horizontalAccuracy\n"
                                   "1793500000000000000,0,17.5,78.3,574,10,90,3\n")
        z.writestr("Accelerometer.csv", "time,seconds_elapsed,z,y,x\n1793500000010000000,0.01,0.1,0.2,0.3\n")
    p = "/tmp/_sl_test.zip"
    with open(p, "wb") as fh:
        fh.write(buf.getvalue())
    s = fk.read_sensor_logger(p)
    assert s["location"][0][:3] == (1793500000.0, 17.5, 78.3)
    assert s["accel"][0] == (1793500000.01, 0.3, 0.2, 0.1)
    json.dumps(s)


def test_hard_brake_from_speed_is_caught_and_gentle_slowdown_is_not():
    t, lat, pts = 1_793_500_000.0, 17.5, []
    lon = 78.3
    for v in [50, 50, 50, 30, 30, 28, 26, 24]:       # km/h each second; 50 -> 30 is ~5.6 m/s^2
        lon += v / 3.6 / 106_000
        pts.append((t, lat, lon))
        t += 1
    ev = fk.hard_brakes(pts)
    assert len(ev) == 1 and ev[0]["from_kmh"] >= 45


def test_short_jink_at_speed_is_a_swerve_but_a_slow_long_turn_is_not():
    track, _ = _loop_track()                           # ~34 km/h on the out leg
    t0 = track[20][0]
    grav = [(t0 + i * 0.01, 0.0, 0.0, -9.8) for i in range(1000)]
    gyro = [(t, 0.0, 0.0, 0.0) for t, *_ in grav]
    for i in range(100, 160):                          # 0.6 s jink
        gyro[i] = (gyro[i][0], 0.0, 0.0, 1.0)
    for i in range(400, 900):                          # 5 s steady turn: not a swerve
        gyro[i] = (gyro[i][0], 0.0, 0.0, 0.8)
    ev = fk.swerves({"gyro": gyro, "gravity": grav}, track)
    assert len(ev) == 1 and ev[0]["seconds"] < 1
