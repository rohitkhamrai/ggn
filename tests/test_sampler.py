import pytest
import numpy as np
import trimesh

from catalog.generators.link import generate_round_link, generate_oval_link
from catalog.generators.clasp import generate_clasp
from catalog.generators.bead import generate_bead
from catalog.generators.connector import generate_connector
from catalog.generators.charm import generate_ball_charm
from catalog.sampler import sample_recipe, assemble_sequence

def test_round_link():
    mesh, meta = generate_round_link()
    assert mesh.is_watertight
    assert meta["units"] == "mm"
    assert len(meta["sockets"]) == 3
    socket_ids = {s["id"] for s in meta["sockets"]}
    assert socket_ids == {"entry", "exit", "drop"}

def test_oval_link():
    mesh, meta = generate_oval_link()
    assert mesh.is_watertight
    assert meta["units"] == "mm"
    assert len(meta["sockets"]) == 3
    socket_ids = {s["id"] for s in meta["sockets"]}
    assert socket_ids == {"entry", "exit", "drop"}

def test_clasp():
    mesh, meta = generate_clasp()
    assert mesh.is_watertight
    assert meta["units"] == "mm"
    assert len(meta["sockets"]) == 2
    socket_ids = {s["id"] for s in meta["sockets"]}
    assert socket_ids == {"entry", "exit"}

def test_bead_styles():
    for style in ["sphere", "barrel", "faceted"]:
        mesh, meta = generate_bead(style=style)
        assert mesh.is_watertight
        assert meta["units"] == "mm"
        assert len(meta["sockets"]) == 2
        socket_ids = {s["id"] for s in meta["sockets"]}
        assert socket_ids == {"entry", "exit"}

def test_connector():
    mesh, meta = generate_connector()
    assert mesh.is_watertight
    assert meta["units"] == "mm"
    assert len(meta["sockets"]) == 3
    socket_ids = {s["id"] for s in meta["sockets"]}
    assert socket_ids == {"entry", "exit_left", "exit_right"}

def test_charm():
    mesh, meta = generate_ball_charm()
    assert mesh.is_watertight
    assert meta["units"] == "mm"
    assert len(meta["sockets"]) == 1
    assert meta["sockets"][0]["id"] == "hanger"

def test_assemble_bracelet():
    recipe = sample_recipe("bracelet", k=6, seed=1)
    report = assemble_sequence(recipe, name="test_bracelet")
    assert report["num_parts"] >= 6
    assert report["metal_stl"] is not None
    assert report["gem_stl"] is None

def test_assemble_earring():
    recipe = sample_recipe("earring", seed=1)
    report = assemble_sequence(recipe, name="test_earring")
    assert report["num_parts"] == 4
    assert report["metal_stl"] is not None

def test_assemble_necklace():
    recipe = sample_recipe("necklace", k=6, seed=1)
    report = assemble_sequence(recipe, name="test_necklace")
    assert report["num_parts"] >= 6
    assert report["metal_stl"] is not None
    assert report["gem_stl"] is not None
    # Metal and gems must remain separate
    assert report["num_metal_parts"] > 0
    assert report["num_gem_parts"] > 0
