# Procedural Jewelry Assembly Engine: Project Spec

Spec for the Antigravity IDE. It contains the PRD, goals, approach, system design, tech stack, build phases and agent rules. Build in the phase order given. Do not skip ahead.

---

## 1. Goals

### 1.1 Primary goal
Generate valid, castable, renderable fine-jewelry designs (rings first, then pendants and earrings) from a modular parametric part catalog, with zero paid services and no pre-existing dataset.

### 1.2 Outputs
1. **Casting-ready metal STL** per design: single shell, watertight, manifold, millimetre units.
2. **Separate gem meshes** per design (never unioned with metal).
3. **Photorealistic Cycles renders**: 4K stills and turntables for the shortlisted designs only.
4. **Assembly manifest** (`assembly.json`): part IDs, parameters, 4x4 transforms, declared units.

### 1.3 Non-goals
- Not a neural 6-DoF pose predictor. Poses are derived from socket frames.
- Not a CAD editor or GUI.
- No gem-in-metal booleans. Stones are set after casting.
- No paid APIs, subscriptions or cloud dependencies required to run the core pipeline.

### 1.4 Success metrics
| Metric | Target |
|---|---|
| Assemblies passing geometry gatekeeper (of those the sampler marks as rule-valid) | >= 95% |
| Boolean crash or hang taking down the pipeline | 0 (isolated by subprocess) |
| Snap unit tests (gap, antiparallel axes, det = +1, spin invariance) | 100% pass at 1e-5 tolerance |
| Time to add a new part type | One generator function and one meta file, no edits to other parts |
| Full Cycles render per shortlisted design | Fits the local GPU time budget (see 6.4) |

---

## 2. Product Requirements (PRD)

### 2.1 Users
- **Designer or operator**: runs batches, reviews the shortlist, exports STL and renders.
- **Developer**: adds part generators, rules and compatibility entries.

### 2.2 Functional requirements

**FR-1 Parametric part catalog**
- Parts are produced by generator functions, not downloaded files.
- Each generator emits a mesh and a `part_meta.json` with sockets.
- Categories: gem, setting/collet, prong set, shank, accent gem, bail, earring post.

**FR-2 Socket-based assembly**
- Each socket has an origin, a mount axis (pointing outward from the part surface), a reference direction, a class string, a role (parent or child), an optional spin, an optional array (prong count) and an `embed_mm` value.
- Sockets mate only if their classes are compatible (class layer) and their sizes satisfy the numeric rule (size layer).

**FR-3 Gem-first constraint solving**
- Solve order: gem, then seat size, then scaled setting, then prong placement, then shank fit.
- It is a constraint graph. It is not a simple tree.

**FR-4 Geometry and casting gatekeeper**
- Boolean unions on metal bodies only.
- Output checks: watertight, single connected component, positive volume, union volume <= sum of parts, minimum wall thickness, minimum prong diameter, no self-intersection.
- Gem clearance via signed-distance or minimum-distance queries: prong tips near the girdle, no crushing, no gap. Gem vs shank clearance is a separate check.
- Emits a structured pass/fail report with measured values, so rules can be tuned from data.

**FR-5 Cheap-first filtering**
- Generate many candidates, then filter by geometry, then score with cheap proxies, then render only the top K in full Cycles.

**FR-6 Rendering**
- Headless Blender, one fresh process per job, hard timeout.
- Gem shader built in-house with node groups (not JewelCraft).
- CPU denoising (OpenImageDenoise).

**FR-7 Aesthetic ranking (late phase, optional)**
- Pairwise human labels, then a Bradley-Terry preference model. A VLM judge is allowed only if calibrated against the human sample.

### 2.3 Non-functional requirements
- Core assembly and validation run on CPU, with no Blender and no GPU required.
- Deterministic: the same seed and parameters give the same assembly.
- Idempotent jobs: content-hashed job IDs, schema version field in every JSON.
- Every module testable in isolation with `pytest`.
- Units declared and asserted as millimetres at load and at export.

### 2.4 Conventions (declare once, assert at load)
- Units: mm. Right-handed, Z-up.
- Socket `axis` points outward from the part. Mating sockets face each other.
- Mirror is an assembly-level flag. It triggers a winding and normal fix before any boolean.

---

## 3. Approach

### 3.1 Why this approach
| Decision | Reason |
|---|---|
| Procedural sockets, not neural pose regression | Poses follow exactly from socket frames. Regression discards known information and fails at 0.05 mm contact tolerances. |
| Generate parts in code | Sockets come for free, outputs are manifold by construction, variety is parametric, and no dataset or licence is needed. |
| Metal and gems separate | Stones are set after casting. Unioning them is the main source of boolean failures and is not castable. |
| `manifold3d` for unions | Fast, robust, manifold output. Requires manifold inputs. |
| Deep embedding for mating parts | Avoids coplanar faces and sliver triangles. |
| Cheap filters before renders | The GPU is the bottleneck, so spend it only on survivors. |

### 3.2 Role of ML
ML is optional and late. Its only job is to score aesthetics, since rules cannot. It does not place parts. A validity classifier trained on perturbed negatives can also be added later.

### 3.3 Known limits
- Recombining parts gives a configurator unless parts are parametric. Parametric generators are therefore a requirement, not an extra.
- Non-uniform scaling distorts prong and wall thickness. Default to uniform scale and use per-part compatibility tables for stone-to-seat sizing.

---

## 4. System Design

### 4.1 Pipeline

```
[ Part Generators ] -> mesh + part_meta.json
        |
        v
[ Catalog Loader + Validator ]   (units, frames, manifold checks)
        |
        v
[ Sampler ]   grammar + params + seed -> assembly graph
        |
        v
[ Constraint Solver / Snapper ]   gem-first, scale whole part record, snap
        |
        v
[ Geometry & Casting Gatekeeper ]   metal union (manifold3d, subprocess)
        |   fail -> discard + log report
        v
[ Cheap Scorer ]   geometric features, workbench previews
        |
        v   top K
[ Headless Cycles Renderer ]   one process per job
        |
        v
[ Optional Aesthetic Ranker ]   human pairs -> Bradley-Terry
```

### 4.2 Module layout

```
jewelry-engine/
  catalog/
    generators/        # gem.py, collet.py, prongs.py, shank.py ...
    meshes/            # generated output
    meta/              # part_meta.json per part
    compat.json        # size rules per socket class
  core/
    units.py           # constants + asserts
    frames.py          # socket -> orthonormal 4x4, determinant checks
    snap.py            # snap chain, scale propagation, spin, mirror
    solver.py          # gem-first constraint ordering
    sampler.py         # grammar + seeded parameter sampling
  geometry/
    validate_mesh.py   # watertight, single shell, normals
    union.py           # manifold3d wrapper, run in subprocess with TTL
    clearance.py       # SDF / min-distance gem checks
    casting_checks.py  # wall thickness, prong diameter, volume sanity
    report.py          # structured pass/fail report
  render/
    render_job.py      # blender -b -P render_job.py -- <manifest>
    materials.py       # metal + gem node groups
  scoring/
    cheap_score.py
    rank.py            # optional
  jobs/
    queue.py           # SQLite state, content-hashed IDs
  tests/
  PROJECT_SPEC.md
```

### 4.3 Data contracts

**`part_meta.json`** (one per part)
```json
{
  "schema_version": 1,
  "part_id": "collet_round_04",
  "category": "setting",
  "mesh": "meshes/collet_round_04.obj",
  "units": "mm",
  "body": "metal",
  "symmetry": { "axis": [0, 0, 1], "order": 1 },
  "params": { "scale": { "min": 0.8, "max": 1.4, "uniform": true } },
  "dims": { "seat_diameter": 6.5, "seat_depth": 1.8, "min_wall": 0.6 },
  "sockets": [
    { "id": "base", "origin": [0, 0, -2.1], "axis": [0, 0, -1], "ref": [1, 0, 0],
      "class": "shank_crown", "role": "child",
      "spin": { "free": true, "step_deg": 90 }, "embed_mm": 0.3 },
    { "id": "seat", "origin": [0, 0, 0.4], "axis": [0, 0, 1], "ref": [1, 0, 0],
      "class": "gem_seat_round", "role": "parent", "size_key": "seat_diameter" },
    { "id": "prong_slot", "origin": [3.0, 0, 0.4], "axis": [1, 0, 0], "ref": [0, 0, 1],
      "class": "prong_mount", "role": "parent",
      "array": { "axis": [0, 0, 1], "counts": [4, 6] } }
  ]
}
```
Gems use the same schema with `"body": "gem"`, a `girdle` socket of class `gem_seat_round`, and dims `girdle_diameter`, `table_diameter`, `crown_height`, `pavilion_depth`.

**`compat.json`** (numeric size rules, separate from parts)
```json
{
  "gem_seat_round": {
    "match": { "a": "seat_diameter", "b": "girdle_diameter" },
    "tolerance_mm": [-0.05, 0.15],
    "solve": "scale_setting_to_gem"
  },
  "shank_crown": { "match": null, "solve": "fixed" }
}
```

**`assembly.json`** (output manifest)
```json
{
  "schema_version": 1,
  "units": "mm",
  "seed": 12345,
  "mirror": false,
  "parts": [
    { "part_id": "gem_round_01", "instance": 0, "scale": 1.0,
      "spin_deg": 0, "transform": [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]] }
  ],
  "report": { "pass": true, "min_wall_mm": 0.62, "components": 1, "volume_mm3": 412.7 }
}
```
This is a custom schema. Do not target the Fusion 360 assembly format.

### 4.4 Snap mathematics

Scale the whole part record first (mesh and every socket origin about the part origin). Then snap:

```
T_W_B = T_W_A · T_S_A · R_theta · R_flip · T_S_B^-1
```

- `T_S_*`: orthonormal frame built from `axis` (Z), `ref` (X), and `Y = Z x X`. Normalize, assert det = +1.
- `R_flip`: fixed 180 deg about the socket X axis, applied in code only.
- `R_theta`: spin about the mounting axis, a multiple of `step_deg`, limited by `symmetry.order`.
- Scale is uniform by default.
- Mirror (negative determinant): flip face winding and recompute normals before any boolean.
- The sign convention of spin is unimportant as long as the tests lock it.

### 4.5 Geometry and boolean hardening
1. Validate catalog inputs once: watertight, consistent normals, no degenerate faces, one shell.
2. Embed mating metal parts by `embed_mm` (a few tenths of a mm, proportional to feature size). Never rely on touching faces.
3. Union with `manifold3d` inside a subprocess with a timeout. On failure, retry with a small deterministic offset.
4. Fallback chain: `manifold3d`, then Blender Exact boolean, then sparse SDF/VDB union plus marching cubes (last resort; re-validate because it rounds prong tips).
5. Validate output (all FR-4 checks), then export STL with declared mm.
6. Replace `python-fcl` for penetration. Use boolean intersection volume or SDF queries.

### 4.6 Rendering design
- `blender -b --factory-startup -E CYCLES -P render_job.py -- <manifest>` with a hard timeout, one process per job.
- Light paths: transmission 16 to 32, diffuse 2 to 3, glossy 4 to 8, clamping on.
- Gem material: refraction mixed with transparent BSDF on `Is Shadow Ray`. Check the Blender version for dispersion support.
- Lighting: high-contrast 2K HDRI or softbox rig (this drives gem brilliance more than any setting).
- Denoise: OpenImageDenoise with albedo and normal passes (CPU, no VRAM).
- Sampling: adaptive threshold about 0.01, 256 to 1024 samples, tile 256 to 512 if memory-limited.
- Turntable: 1080p by default, persistent data on, rotate the camera or an empty. 4K is for final stills on the shortlist.
- Do not use JewelCraft headless. Do not use EEVEE (poor refraction, needs a GL context). LuxCore is an option only if Cycles fails.

### 4.7 Orchestration
- The whole core runs locally on CPU. No Colab is needed for generation.
- If a remote batch ranking step is later wanted, transport through a **private Hugging Face Hub dataset repo** (free, versioned, token auth). The local machine polls and nothing is exposed inbound.
- Jobs: content-hashed IDs, upload to a temp name then write a `DONE` marker last, state in SQLite, polling by systemd timer.

---

## 5. Tech Stack (all free)

| Layer | Choice |
|---|---|
| Language | Python 3.10+ |
| Math | `numpy`, optionally `scipy.spatial.transform` (not `mathutils`, which only exists inside Blender) |
| Mesh I/O and checks | `trimesh` |
| Metal booleans | `manifold3d` |
| Parametric metal parts | `build123d` or `cadquery` (OpenCASCADE) |
| Gems | `numpy` + `trimesh` (rings of vertices, convex hull, facet angles as params) |
| SDF fallback | OpenVDB (sparse) or `mesh_to_sdf` |
| Tests | `pytest` |
| Job state | SQLite |
| Rendering | Blender (Cycles, headless) |
| Optional ranking | Bradley-Terry in `numpy`/`scikit-learn`; VLM only if calibrated |
| Optional transport | `huggingface_hub` private dataset repo |

Hardware notes:
- Local box: Ubuntu, Quadro M4000 8GB (Maxwell, sm_52, no RT cores). VRAM is rarely the limit. Gem light-path depth is.
- Check `torch.cuda.get_arch_list()` before assuming sm_52 is unsupported. Core pipeline needs no PyTorch.

---

## 6. Build Phases

Do each phase fully, with tests green, before starting the next.

### Phase 1: Foundations (no Blender, no ML)
1. Create the repo structure above.
2. `units.py`, `frames.py`: orthonormal frame builder with asserts.
3. Parametric generators: round brilliant gem, 4 to 6 prong collet, simple shank. Each emits mesh and `part_meta.json`.
4. Loader and validator for meta and meshes.
5. `snap.py` with scale propagation, flip, spin and mirror.
6. Tests (below).

**Tests to write first**
- Loader rejects: non-unit axis, `ref` parallel to `axis`, unknown class, units not mm.
- Snap: socket origins coincide, axes antiparallel (`dot == -1`), determinant +1, tolerance 1e-5.
- Spin invariance: rotating by `360/order` gives identical volume and bounding box (1e-5).
- Scale: scaled socket positions equal scaled originals, for all sockets, not just the base.
- Mirror: normals consistent after the winding fix.

### Phase 2: Solver and gatekeeper
1. Gem-first solver and `compat.json` handling.
2. `union.py` in a subprocess with timeout.
3. Clearance via SDF or min-distance. Casting checks. Structured report.
4. Sampler with seeds. Generate hundreds of assemblies and measure the pass rate.

### Phase 3: Rendering
1. `render_job.py`, metal and gem node groups, HDRI rig, CPU denoise.
2. Render a few dozen assemblies end to end. Record the time per frame.
3. Add the cheap scorer, then render only the top K.

### Phase 4: Expansion and ranking
1. Add part types (bails, posts, accent gems, more shanks) with no pipeline edits.
2. Collect pairwise human labels, fit Bradley-Terry, optionally calibrate a VLM.
3. Optional validity classifier from perturbed negatives.

---

## 7. Rules for the Antigravity Agent

1. Follow phase order. Do not touch rendering or ML before Phase 1 and 2 tests pass.
2. Never union gem meshes with metal.
3. Assert millimetres at every load and export.
4. Scale the whole part record (mesh and sockets) before snapping.
5. Run every boolean in a subprocess with a timeout.
6. Every geometry decision must emit measured values into the structured report.
7. Add a unit test for each new function. Use tolerance 1e-5 for float comparisons.
8. Adding a part must never require editing other parts' files. Size rules go in `compat.json`.
9. Keep the core runnable without Blender and without a GPU.
10. Ask before adding any paid dependency.

---

## 8. Risks

| Risk | Mitigation |
|---|---|
| Boolean failures on bad inputs | Validate catalog once, deep embedding, `manifold3d`, fallback chain, subprocess isolation |
| Low variety from a fixed catalog | Parametric generators, growing part set |
| Unvalidated aesthetic judge | Calibrate any VLM against human pairs, or skip it |
| Render cost on a Maxwell GPU | Cheap-first filtering, 1080p turntables, adaptive sampling, CPU denoise |
| Casting rules not met by geometry | Casting checks in the gatekeeper, minimum wall and prong diameter, report-driven tuning |
| Float drift in tests | Fixed 1e-5 tolerance |


## Phase 5: The Sequence/Graph Sampler (Chains & Necklaces)

**Goal:** Move from fixed topology (ring = gem + collet + shank) to a flexible sequence/graph (clasp ? link ? link ? charm ? link ? pendant ? link ? clasp).

**What changes:**
- Grammar becomes a **sequence sampler**: pick N components, chain them socket-to-socket.
- Components need **two sockets**: \entry\ and \exit\ (like a linked list node).
- Topology can branch for pendants, charms, earring drops.

**New generators needed:**
- \link.py\ ? chain link, oval/round/cable
- \clasp.py\ ? lobster, toggle, box
- \charm.py\ ? small pendant hanging off a link
- \connector.py\ ? joins two chains (Y-split for necklace)
- \ead.py\ ? round/faceted bead with through-hole

**What stays the same:**
- Socket system (entry/exit sockets)
- Gatekeeper (mesh collision detection)
- Renderer (Blender headless pipeline)
