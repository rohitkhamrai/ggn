import json

def solve_assembly_scales(assembly_def, compat_path="catalog/compat.json", catalog_meta_dir="catalog/meta"):
    """
    assembly_def is a list of node definitions.
    Mutates assembly_def in place to set correct uniform scales according to compat.json rules.
    """
    with open(compat_path, 'r') as f:
        compat = json.load(f)
        
    metas = {}
    for node in assembly_def:
        with open(f"{catalog_meta_dir}/{node['part_id']}.json", 'r') as f:
            metas[node['id']] = json.load(f)
            
    for node in assembly_def:
        if node.get("parent") is None:
            continue
            
        parent_node = next(n for n in assembly_def if n["id"] == node["parent"])
        child_sock_id, parent_sock_id = node["socket_pair"]
        
        child_meta = metas[node["id"]]
        parent_meta = metas[parent_node["id"]]
        
        child_sock = next(s for s in child_meta["sockets"] if s["id"] == child_sock_id)
        
        rule = compat.get(child_sock["class"])
        if not rule:
            continue
            
        if rule["solve"] == "scale_setting_to_gem":
            a_key = rule["match"]["a"]
            b_key = rule["match"]["b"]
            
            a_val = parent_meta["dims"][a_key]
            b_val = child_meta["dims"][b_key]
            
            scale_req = (b_val * node.get("scale", 1.0)) / a_val
            parent_node["scale"] = scale_req

    return assembly_def
