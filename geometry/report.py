def generate_report(metal_mesh, checks):
    """
    Emits structured pass/fail report.
    """
    passed_checks = {k: bool(v) for k, v in checks.items()}
    all_passed = all(passed_checks.values())
    
    report = {
        "pass": all_passed,
        "volume_mm3": float(metal_mesh.volume),
        "components": int(metal_mesh.body_count),
        "checks": passed_checks
    }
    return report
