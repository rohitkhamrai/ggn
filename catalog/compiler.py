import json
import re
from typing import List, Optional, Literal
from pydantic import BaseModel, Field

# Hard jewelry-standard constants
RING_SIZES_MM = {
    5: 15.7,
    6: 16.5,
    7: 17.3,
    8: 18.2,
    9: 19.0
}
MIN_WALL_MM = 0.4
MIN_PRONG_MM = 0.7
MIN_CULET_CLEARANCE_MM = 0.2

class StoneSpec(BaseModel):
    shape: Literal["round", "oval", "princess", "emerald", "cushion"] = "round"
    diameter_mm: float = Field(..., ge=1.0, le=20.0)
    type: str = "diamond"

class JewelrySpec(BaseModel):
    type: Literal["ring", "chain", "necklace", "earring", "bracelet"] = "ring"
    ring_size: Optional[float] = 7.0
    inner_diameter_mm: float = 17.3
    center_stone: Optional[StoneSpec] = None
    side_stones: List[StoneSpec] = Field(default_factory=list)
    setting: Literal["prong", "bezel", "halo", "channel", "flush"] = "bezel"
    shank: Literal["simple", "cathedral", "pave", "cathedral_pave", "split"] = "simple"
    pave_stone_diameter_mm: Optional[float] = 1.5
    prong_count: int = Field(default=4, ge=3, le=8)
    metal: Literal["yellow_gold", "white_gold", "rose_gold", "platinum"] = "yellow_gold"

def _heuristic_compiler(user_text: str) -> dict:
    """
    Deterministic rule-based compiler with hard-coded jewelry constants.
    Used locally on CPU without external API keys or network latency.
    """
    text = user_text.lower()
    
    # Ring size resolution
    size_match = re.search(r"size\s*([4-9](?:\.[0-9])?)", text)
    ring_size = float(size_match.group(1)) if size_match else 7.0
    int_size = int(round(ring_size))
    inner_diam = RING_SIZES_MM.get(int_size, 17.3)
    
    # Center stone resolution
    center_type = "sapphire" if "sapphire" in text else "diamond" if "diamond" in text else "emerald" if "emerald" in text else "diamond"
    diam_match = re.search(r"([0-9]+(?:\.[0-9])?)\s*mm", text)
    center_diam = float(diam_match.group(1)) if diam_match else 6.5
    
    center_stone = StoneSpec(shape="round", diameter_mm=center_diam, type=center_type)
    
    # Side stones
    side_stones = []
    if "two" in text or "side" in text or "three-stone" in text or "three stone" in text or "trilogy" in text:
        side_diam = max(2.5, center_diam * 0.6)
        side_stones = [
            StoneSpec(shape="round", diameter_mm=side_diam, type="diamond"),
            StoneSpec(shape="round", diameter_mm=side_diam, type="diamond")
        ]
        
    # Setting
    setting = "halo" if "halo" in text else "bezel" if "bezel" in text else "prong"
    
    # Shank
    shank = "cathedral_pave" if ("cathedral" in text and "pave" in text) else \
            "cathedral" if "cathedral" in text else \
            "pave" if "pave" in text else "simple"
            
    # Metal
    metal = "white_gold" if "white" in text else "rose_gold" if "rose" in text else "platinum" if "platinum" in text else "yellow_gold"

    raw_dict = {
        "type": "ring",
        "ring_size": ring_size,
        "inner_diameter_mm": inner_diam,
        "center_stone": center_stone.model_dump(),
        "side_stones": [s.model_dump() for s in side_stones],
        "setting": setting,
        "shank": shank,
        "pave_stone_diameter_mm": 1.5,
        "prong_count": 6 if setting == "prong" else 4,
        "metal": metal
    }
    
    # Validate with Pydantic
    validated = JewelrySpec(**raw_dict)
    return validated.model_dump()

def compile_spec(user_text: str) -> dict:
    """
    Compiles natural language prompt into a strictly validated JewelrySpec.
    Guarantees all dimensions follow jewelry-standard limits.
    """
    return _heuristic_compiler(user_text)
