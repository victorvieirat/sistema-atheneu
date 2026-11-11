"""Motor de cálculo espacial, geometria AABB e posicionamento relativo para Obsidian Canvas."""

from typing import Tuple, List, Dict, Any, Optional

DEFAULT_WIDTHS = {
    "text": 360,
    "file": 420,
    "link": 320,
    "group": 680,
}

DEFAULT_HEIGHTS = {
    "text": 220,
    "file": 240,
    "link": 180,
    "group": 440,
}


def check_aabb_overlap(
    x1: int, y1: int, w1: int, h1: int,
    x2: int, y2: int, w2: int, h2: int
) -> bool:
    """Verifica se duas caixas delimitadoras 2D se sobrepõem."""
    return (x1 < x2 + w2) and (x2 < x1 + w1) and (y1 < y2 + h2) and (y2 < y1 + h1)


def find_non_overlapping_position(
    target_x: int,
    target_y: int,
    width: int,
    height: int,
    existing_nodes: List[Dict[str, Any]],
    direction: str = "below",
    gap: int = 60,
    is_group: bool = False
) -> Tuple[int, int]:
    """Ajusta as coordenadas target_x, target_y caso haja colisão com cartões existentes.
    
    Nota: Nós do tipo 'group' podem englobar cartões normais, mas nós normais não
    devem se sobrepor a outros nós normais.
    """
    if is_group:
        # Grupos não sofrem restrição estrita contra cartões internos,
        # mas evitamos colisão direta com outros grupos idênticos.
        colliding_groups = [
            n for n in existing_nodes
            if n.get("type") == "group" and check_aabb_overlap(
                target_x, target_y, width, height,
                n.get("x", 0), n.get("y", 0), n.get("width", 100), n.get("height", 100)
            )
        ]
        if not colliding_groups:
            return target_x, target_y

    # Para nós normais, verificamos colisão com outros nós normais
    curr_x, curr_y = target_x, target_y
    max_attempts = 100
    attempt = 0

    while attempt < max_attempts:
        has_collision = False
        for node in existing_nodes:
            if not is_group and node.get("type") == "group":
                continue  # Grupos podem conter cartões
            nx, ny = node.get("x", 0), node.get("y", 0)
            nw, nh = node.get("width", 100), node.get("height", 100)
            
            if check_aabb_overlap(curr_x, curr_y, width, height, nx, ny, nw, nh):
                has_collision = True
                if direction in ("right_of", "right"):
                    curr_x = nx + nw + gap
                else:
                    curr_y = ny + nh + gap
                break
        
        if not has_collision:
            return curr_x, curr_y
        attempt += 1

    return curr_x, curr_y


def compute_relative_placement(
    ref_node: Dict[str, Any],
    width: int,
    height: int,
    placement: str,
    gap: int = 60
) -> Tuple[int, int]:
    """Calcula coordenadas iniciais relativas a um nó de referência."""
    rx = ref_node.get("x", 0)
    ry = ref_node.get("y", 0)
    rw = ref_node.get("width", 300)
    rh = ref_node.get("height", 200)

    p = placement.lower()
    if p in ("right_of", "right"):
        return rx + rw + gap, ry
    elif p in ("left_of", "left"):
        return rx - width - gap, ry
    elif p in ("below", "down", "bottom"):
        return rx, ry + rh + gap
    elif p in ("above", "up", "top"):
        return rx, ry - height - gap
    else:
        return rx + rw + gap, ry


def compute_auto_sides(
    node_a: Dict[str, Any],
    node_b: Dict[str, Any]
) -> Tuple[str, str]:
    """Determina automaticamente os lados mais naturais de saída e entrada entre dois nós."""
    xa, ya = node_a.get("x", 0), node_a.get("y", 0)
    wa, ha = node_a.get("width", 200), node_a.get("height", 100)
    center_a_x, center_a_y = xa + wa / 2.0, ya + ha / 2.0

    xb, yb = node_b.get("x", 0), node_b.get("y", 0)
    wb, hb = node_b.get("width", 200), node_b.get("height", 100)
    center_b_x, center_b_y = xb + wb / 2.0, yb + hb / 2.0

    dx = center_b_x - center_a_x
    dy = center_b_y - center_a_y

    if abs(dx) >= abs(dy):
        if dx > 0:
            return "right", "left"
        else:
            return "left", "right"
    else:
        if dy > 0:
            return "bottom", "top"
        else:
            return "top", "bottom"
