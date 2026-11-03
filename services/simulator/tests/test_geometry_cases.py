"""Wall-crossing geometry (B-126): crossings, corners, junctions, grazes, heights and scales.

Before B-126 a segment through a wall end used a half-open convention, so the same L corner
cost 0, 10 or 20 dB depending only on the direction each wall had been drawn in.
"""

import itertools

import pytest

from smart_environment.engines import simulate
from smart_environment.models import Building, Device, Link, Material, Point, Project, Radio, Settings, Wall

LOSS = {"m10": 10.0, "m6": 6.0}


def radio():
    return Radio(id="r", protocol="wifi", channel=1, frequency_hz=2.412e9, bandwidth_hz=20e6, tx_power_dbm=20,
                 sensitivity_dbm=-90)


def project(walls, a=(0, 0, 1), b=(8, 8, 1), shift=(0.0, 0.0)):
    sx, sy = shift
    moved = [w.model_copy(update={"start": Point(x=w.start.x + sx, y=w.start.y + sy, z=w.start.z),
                                  "end": Point(x=w.end.x + sx, y=w.end.y + sy, z=w.end.z)}) for w in walls]
    return Project(building=Building(materials=[Material(id=k, name=k, loss_db_24ghz=v, loss_db_5ghz=v)
                                                for k, v in LOSS.items()], walls=moved),
                   devices=[Device(id="a", name="A", position=Point(x=a[0] + sx, y=a[1] + sy, z=a[2]), radios=[radio()]),
                            Device(id="b", name="B", position=Point(x=b[0] + sx, y=b[1] + sy, z=b[2]), radios=[radio()])],
                   links=[Link(id="l", source_device_id="a", source_radio_id="r", target_device_id="b",
                               target_radio_id="r")],
                   settings=Settings(path_loss_exponent=2))


def wall(wall_id, start, end, material="m10"):
    return Wall(id=wall_id, start=Point(x=start[0], y=start[1]), end=Point(x=end[0], y=end[1]), material_id=material)


def crossed(walls, **kwargs):
    link = simulate(project(walls, **kwargs)).links[0]
    assert link.forward.crossed_wall_ids == link.reverse.crossed_wall_ids, "both directions see the same walls"
    assert link.forward.wall_loss_db == link.reverse.wall_loss_db
    return link.forward.crossed_wall_ids, link.forward.wall_loss_db


def both_ways(wall_id, p, q, material="m10"):
    return [wall(wall_id, p, q, material), wall(wall_id, q, p, material)]


def drawings(*segments):
    """Every combination of drawing directions for the given (id, p, q) segments."""
    return [list(combo) for combo in itertools.product(*(both_ways(*segment) for segment in segments))]


@pytest.mark.parametrize("walls", drawings(("h", (0, 4), (4, 4)), ("v", (4, 4), (4, 0))))
def test_leaving_a_corner_counts_one_wall_however_it_was_drawn(walls):
    ids, loss = crossed(walls)
    assert len(ids) == 1 and loss == 10


@pytest.mark.parametrize("walls", drawings(("h", (4, 4), (8, 4)), ("v", (4, 4), (4, 8))))
def test_touching_the_outside_of_a_corner_is_a_graze(walls):
    assert crossed(walls, a=(0, 8, 1), b=(8, 0, 1)) == ([], 0)


@pytest.mark.parametrize("walls", drawings(("tip", (4, 4), (0, 8))))
def test_touching_a_free_wall_end_is_a_graze(walls):
    assert crossed(walls) == ([], 0)


@pytest.mark.parametrize("walls", drawings(("left", (0, 4), (4, 4)), ("right", (4, 4), (8, 4))))
def test_a_straight_wall_drawn_in_two_pieces_counts_once(walls):
    ids, loss = crossed(walls)
    assert ids == ["left"] and loss == 10


@pytest.mark.parametrize("walls", drawings(("w", (0, 4), (4, 4)), ("e", (4, 4), (8, 4)),
                                           ("s", (4, 0), (4, 4)), ("n", (4, 4), (4, 8))))
def test_a_diagonal_through_a_four_way_junction_counts_two(walls):
    ids, loss = crossed(walls)
    assert len(ids) == 2 and loss == 20


@pytest.mark.parametrize("walls", drawings(("bar", (0, 4), (8, 4)), ("stem", (4, 4), (4, 0))))
def test_a_t_junction_counts_the_through_wall_only(walls):
    assert crossed(walls) == (["bar"], 10)


def test_on_a_tie_the_stronger_wall_counts():
    walls = [wall("weak", (0, 4), (4, 4), "m6"), wall("strong", (4, 4), (4, 0), "m10")]
    assert crossed(walls) == (["strong"], 10)
    assert crossed(list(reversed(walls))) == (["strong"], 10)


def test_interior_crossings_and_rays_along_a_wall():
    assert crossed([wall("x", (0, 8), (8, 0))]) == (["x"], 10)
    assert crossed([wall("along", (2, 2), (6, 6))]) == ([], 0), "a ray running along a wall is a graze"
    assert crossed([wall("parallel", (1, 0), (9, 8))]) == ([], 0)
    assert crossed([wall("short", (0, 8), (3.9, 4.1))]) == ([], 0), "ends before the ray"


@pytest.mark.parametrize("a_z, b_z, base, height, expected", [
    (1, 1, 0, 2.6, 10),       # ordinary crossing
    (2.6, 2.6, 0, 2.6, 10),   # exactly at the top edge
    (3, 3, 0, 2.6, 0),        # above the wall
    (0.5, 0.5, 1, 1.6, 0),    # below a wall that starts at 1 m (e.g. a high partition)
    (0.5, 4.5, 0, 2.6, 10),   # sloped ray: 2.5 m at the crossing, still within the wall
    (1.5, 5.5, 0, 2.6, 0),    # sloped ray: 3.5 m at the crossing, over the wall
])
def test_heights_are_checked_where_the_ray_crosses(a_z, b_z, base, height, expected):
    w = Wall(id="w", start=Point(x=0, y=8, z=base), end=Point(x=8, y=0, z=base), height_m=height, material_id="m10")
    assert crossed([w], a=(0, 0, a_z), b=(8, 8, b_z))[1] == expected


def test_a_device_on_a_wall_line_does_not_cross_it_and_is_flagged():
    link = simulate(project([wall("w", (0, 8), (8, 0))], b=(4, 4, 1))).links[0]
    assert link.forward.crossed_wall_ids == [] and link.status == "unverified"
    assert any("dentro de la pared w" in reason for reason in link.reasons)


@pytest.mark.parametrize("shift", [(9000.0, -9000.0), (-9990.0, 9990.0), (0.25, 0.125)])
def test_results_do_not_depend_on_where_the_plan_sits(shift):
    walls = [wall("h", (0, 4), (4, 4)), wall("v", (4, 4), (4, 0)), wall("x", (5, 9), (9, 5), "m6")]
    base = simulate(project(walls)).links[0].forward
    moved = simulate(project(walls, shift=shift)).links[0].forward
    assert moved.crossed_wall_ids == base.crossed_wall_ids
    assert moved.received_power_dbm == pytest.approx(base.received_power_dbm, abs=1e-6)


def test_small_walls_and_short_links():
    assert crossed([wall("tiny", (4.005, 3.995), (3.995, 4.005))]) == (["tiny"], 10), "a 1.4 cm wall still counts"
    near = simulate(project([], b=(0.3, 0.4, 1))).links[0].forward
    assert near.distance_m == pytest.approx(0.5) and near.path_loss_db == pytest.approx(
        simulate(project([], b=(0.3, 0.4, 1))).links[0].reverse.path_loss_db)
