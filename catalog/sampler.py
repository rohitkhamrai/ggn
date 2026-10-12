import os
import json
import random
import numpy as np
import trimesh

from core.snap import snap_part
from catalog.generators.link import generate_round_link, generate_oval_link
from catalog.generators.clasp import generate_clasp
from catalog.generators.charm import generate_ball_charm
from catalog.generators.bead import generate_bead
from catalog.generators.connector import generate_connector
from catalog.generators.collet import generate_round_collet
from catalog.generators.gem import generate_round_gem
from catalog.generators.shank import generate_simple_shank

CATALOG = {
    "clasp": generate_clasp,
    "link_round": generate_round_link,
    "link_oval": generate_oval_link,
    "bead": generate_bead,
    "connector": generate_connector,
    "charm": generate_ball_charm,
    "collet": generate_round_collet,
    "gem": generate_round_gem,
    "shank": generate_simple_shank
}

def assemble_sequence(recipe, output_dir="jobs/output", name="jewelry"):
    """
    Takes a structured sequence recipe and chains parts socket-to-socket.
    
    Each item in recipe is a dict:
      {
        "id": "node_0",
        "category": "clasp" | "link_round" | "bead" | ...,
        "kwargs": {},
        "parent_id": None | "node_prev",
        "parent_socket_id": "exit" | "drop" | "exit_left" | ...,
        "child_socket_id": "entry" | "hanger" | "pavilion" | ...
      }
    """
    os.makedirs(output_dir, exist_ok=True)
    
    transforms = {}
    node_metas = {}
    metal_meshes = []
    gem_meshes = []
    assembly_manifest = []
    
    for item in recipe:
        node_id = item["id"]
        cat = item["category"]
        kwargs = item.get("kwargs", {})
        gen_fn = CATALOG[cat]
        
        mesh, meta = gen_fn(part_id=node_id, **kwargs)
        node_metas[node_id] = meta
        
        parent_id = item.get("parent_id")
        if parent_id is None:
            # First item sits at world origin
            T = np.eye(4)
        else:
            p_meta = node_metas[parent_id]
            p_tf = transforms[parent_id]
            p_sock_id = item.get("parent_socket_id", "exit")
            c_sock_id = item.get("child_socket_id", "entry")
            
            p_socket = next(s for s in p_meta["sockets"] if s["id"] == p_sock_id)
            c_socket = next(s for s in meta["sockets"] if s["id"] == c_sock_id)
            
            # Assert socket compatibility
            if p_socket["class"] != c_socket["class"]:
                raise ValueError(
                    f"Socket class mismatch between {parent_id}.{p_sock_id} ({p_socket['class']}) "
                    f"and {node_id}.{c_sock_id} ({c_socket['class']})"
                )
                
            spin = item.get("spin_deg", 0.0)
            T = snap_part(p_socket, c_socket, p_tf, spin_deg=spin)
            
        transforms[node_id] = T
        
        # Apply transform to mesh copy
        inst_mesh = mesh.copy()
        inst_mesh.apply_transform(T)
        
        is_gem = meta.get("body") == "gem"
        if is_gem:
            gem_meshes.append(inst_mesh)
        else:
            metal_meshes.append(inst_mesh)
            
        assembly_manifest.append({
            "id": node_id,
            "category": cat,
            "body": meta.get("body", "metal"),
            "transform": T.tolist()
        })

    # Combine separate metal and gem meshes (Rule: never union gems with metal)
    combined_metal = trimesh.util.concatenate(metal_meshes) if metal_meshes else trimesh.Trimesh()
    combined_gems = trimesh.util.concatenate(gem_meshes) if gem_meshes else trimesh.Trimesh()
    
    metal_path = os.path.join(output_dir, f"{name}_metal.stl")
    gem_path = os.path.join(output_dir, f"{name}_gem.stl")
    manifest_path = os.path.join(output_dir, f"{name}_manifest.json")
    
    if len(combined_metal.vertices) > 0:
        combined_metal.export(metal_path)
    if len(combined_gems.vertices) > 0:
        combined_gems.export(gem_path)
        
    report = {
        "name": name,
        "units": "mm",
        "num_parts": len(recipe),
        "num_metal_parts": len(metal_meshes),
        "num_gem_parts": len(gem_meshes),
        "metal_stl": metal_path if len(combined_metal.vertices) > 0 else None,
        "gem_stl": gem_path if len(combined_gems.vertices) > 0 else None,
        "assembly": assembly_manifest
    }
    
    with open(manifest_path, "w") as f:
        json.dump(report, f, indent=2)
        
    return report

def sample_recipe(jewelry_type="necklace", k=10, seed=42):
    """
    Generates a valid chaining recipe for arbitrary jewelry types.
    """
    random.seed(seed)
    recipe = []
    
    if jewelry_type == "bracelet":
        # Clasp -> interlocking links & beads with charms -> clasp
        recipe.append({"id": "clasp_start", "category": "clasp", "parent_id": None})
        last_id = "clasp_start"
        link_count = 0
        
        for i in range(1, k):
            node_id = f"part_{i}"
            # Interlocking chain with periodic accent beads
            cat = "bead" if (i % 5 == 0) else "link_round"
            spin = 0.0
            if "link" in cat:
                spin = 90.0 if (link_count % 2 == 1) else 0.0
                link_count += 1
                
            recipe.append({
                "id": node_id,
                "category": cat,
                "parent_id": last_id,
                "parent_socket_id": "exit",
                "child_socket_id": "entry",
                "spin_deg": spin
            })
            
            # Add hanging charm drops at intervals
            if cat == "link_round" and (i % 4 == 2):
                charm_id = f"charm_{i}"
                recipe.append({
                    "id": charm_id,
                    "category": "charm",
                    "parent_id": node_id,
                    "parent_socket_id": "drop",
                    "child_socket_id": "hanger"
                })
            last_id = node_id
            
    elif jewelry_type == "earring":
        # Earring hook/link -> connector -> 2 drops
        recipe.append({"id": "top_link", "category": "link_oval", "parent_id": None})
        recipe.append({
            "id": "y_connector",
            "category": "connector",
            "parent_id": "top_link",
            "parent_socket_id": "exit",
            "child_socket_id": "entry"
        })
        # Left drop: bead -> charm
        recipe.append({
            "id": "bead_left",
            "category": "bead",
            "parent_id": "y_connector",
            "parent_socket_id": "exit_left",
            "child_socket_id": "entry"
        })
        recipe.append({
            "id": "bead_right",
            "category": "bead",
            "parent_id": "y_connector",
            "parent_socket_id": "exit_right",
            "child_socket_id": "entry"
        })
        
    elif jewelry_type == "ring":
        recipe.append({"id": "shank_base", "category": "shank", "parent_id": None})
        recipe.append({
            "id": "ring_collet",
            "category": "collet",
            "kwargs": {"seat_diameter": 5.0},
            "parent_id": "shank_base",
            "parent_socket_id": "crown",
            "child_socket_id": "base"
        })
        recipe.append({
            "id": "ring_gem",
            "category": "gem",
            "kwargs": {"girdle_diameter": 5.0},
            "parent_id": "ring_collet",
            "parent_socket_id": "seat",
            "child_socket_id": "girdle"
        })
        
    else: # necklace or general chain
        recipe.append({"id": "start_clasp", "category": "clasp", "parent_id": None})
        last_id = "start_clasp"
        link_count = 0
        
        mid = k // 2
        for i in range(1, k):
            node_id = f"link_{i}"
            if i == mid:
                # Center pendant: collet + gem
                recipe.append({
                    "id": node_id,
                    "category": "link_round",
                    "parent_id": last_id,
                    "parent_socket_id": "exit",
                    "child_socket_id": "entry",
                    "spin_deg": 90.0 if (link_count % 2 == 1) else 0.0
                })
                link_count += 1
                collet_id = "center_pendant"
                gem_id = "center_stone"
                recipe.append({
                    "id": collet_id,
                    "category": "collet",
                    "kwargs": {"seat_diameter": 6.0},
                    "parent_id": node_id,
                    "parent_socket_id": "drop",
                    "child_socket_id": "hanger"
                })
                recipe.append({
                    "id": gem_id,
                    "category": "gem",
                    "kwargs": {"girdle_diameter": 6.0},
                    "parent_id": collet_id,
                    "parent_socket_id": "seat",
                    "child_socket_id": "girdle"
                })
            else:
                cat = "bead" if (i % 5 == 0) else "link_round"
                spin = 0.0
                if "link" in cat:
                    spin = 90.0 if (link_count % 2 == 1) else 0.0
                    link_count += 1
                recipe.append({
                    "id": node_id,
                    "category": cat,
                    "parent_id": last_id,
                    "parent_socket_id": "exit",
                    "child_socket_id": "entry",
                    "spin_deg": spin
                })
            last_id = node_id
            
    return recipe
