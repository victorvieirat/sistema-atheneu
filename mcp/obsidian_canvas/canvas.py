"""Gerenciador de I/O atômico, transações em lote e validação de arquivos Obsidian Canvas."""

import os
import sys
import json
import uuid
import re
from typing import Dict, Any, List, Optional, Tuple

from models import CanvasData, CanvasEdge, BaseNode
from layout import (
    DEFAULT_WIDTHS,
    DEFAULT_HEIGHTS,
    compute_relative_placement,
    find_non_overlapping_position,
    compute_auto_sides,
    check_aabb_overlap
)

PRIVACY_FOLDER = "98_Privado"


def _check_privacy(path_or_str: str) -> None:
    """Bloqueio estrito de referências a 98_Privado conforme AGENTS.md."""
    if PRIVACY_FOLDER in path_or_str.replace("\\", "/"):
        raise PermissionError(
            f"Violação da Barreira Estrita de Privacidade: acesso a '{PRIVACY_FOLDER}' é estritamente proibido."
        )


def _resolve_canvas_path(path: str, vault_root: Optional[str] = None) -> str:
    """Normaliza o caminho do arquivo .canvas garantindo extensão correta."""
    _check_privacy(path)
    clean_p = path.replace("\\", "/")
    if not clean_p.endswith(".canvas"):
        clean_p += ".canvas"
    
    if os.path.isabs(clean_p):
        return os.path.normpath(clean_p)
    
    if vault_root:
        return os.path.normpath(os.path.join(vault_root, clean_p))
    
    return os.path.normpath(clean_p)


def _read_json_file(file_path: str) -> Dict[str, Any]:
    """Lê arquivo JSON em UTF-8."""
    _check_privacy(file_path)
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Arquivo Canvas não encontrado: '{file_path}'")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_json_atomic(file_path: str, data: Dict[str, Any]) -> None:
    """Gravação atômica em UTF-8 com substituição via arquivo temporário."""
    _check_privacy(file_path)
    os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
    tmp_path = file_path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, file_path)


class CanvasManager:
    """Fachada para manipulação segura e validação de arquivos Obsidian Canvas."""

    def __init__(self, vault_root: Optional[str] = None):
        if vault_root:
            self.vault_root = os.path.abspath(vault_root)
        else:
            # Detecta a raiz do repositório a partir da localização deste script (mcp/obsidian_canvas/..)
            repo_candidate = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            if os.path.isdir(os.path.join(repo_candidate, "atheneu")):
                self.vault_root = repo_candidate
            else:
                self.vault_root = os.getcwd()

    def resolve_path(self, path: str) -> str:
        return _resolve_canvas_path(path, self.vault_root)

    def read_canvas(
        self,
        file_path: str,
        detail: str = "summary",
        search_text: Optional[str] = None
    ) -> Dict[str, Any]:
        p = self.resolve_path(file_path)
        data = _read_json_file(p)
        nodes = data.get("nodes", [])
        edges = data.get("edges", [])

        # Se houver busca textual, filtra nós e arestas relacionadas
        if search_text:
            st = search_text.lower()
            filtered_nodes = []
            matching_ids = set()
            for n in nodes:
                text_content = n.get("text", "") or n.get("file", "") or n.get("label", "") or n.get("url", "")
                if st in str(text_content).lower() or st in str(n.get("id", "")).lower():
                    filtered_nodes.append(n)
                    matching_ids.add(n.get("id"))
            
            filtered_edges = [
                e for e in edges
                if e.get("fromNode") in matching_ids or e.get("toNode") in matching_ids
            ]
            return {
                "file_path": p,
                "detail": "search_result",
                "query": search_text,
                "matches_count": len(filtered_nodes),
                "nodes": filtered_nodes,
                "edges": filtered_edges
            }

        if detail == "full":
            return {
                "file_path": p,
                "detail": "full",
                "nodes": nodes,
                "edges": edges
            }
        elif detail == "nodes":
            return {
                "file_path": p,
                "detail": "nodes",
                "count": len(nodes),
                "nodes": nodes
            }
        elif detail == "edges":
            return {
                "file_path": p,
                "detail": "edges",
                "count": len(edges),
                "edges": edges
            }

        # Padrão: "summary"
        groups = [n for n in nodes if n.get("type") == "group"]
        min_x = min((n.get("x", 0) for n in nodes), default=0)
        max_x = max((n.get("x", 0) + n.get("width", 0) for n in nodes), default=0)
        min_y = min((n.get("y", 0) for n in nodes), default=0)
        max_y = max((n.get("y", 0) + n.get("height", 0) for n in nodes), default=0)

        nodes_summary = []
        for n in nodes:
            ntype = n.get("type")
            preview = ""
            if ntype == "text":
                txt = n.get("text", "").strip()
                preview = txt[:80] + ("..." if len(txt) > 80 else "")
            elif ntype == "file":
                preview = n.get("file", "")
            elif ntype == "group":
                preview = n.get("label", "Grupo sem nome")
            elif ntype == "link":
                preview = n.get("url", "")

            nodes_summary.append({
                "id": n.get("id"),
                "type": ntype,
                "preview": preview,
                "x": n.get("x"),
                "y": n.get("y"),
                "width": n.get("width"),
                "height": n.get("height"),
                "color": n.get("color")
            })

        return {
            "file_path": p,
            "detail": "summary",
            "node_count": len(nodes),
            "edge_count": len(edges),
            "group_count": len(groups),
            "bounds": {"min_x": min_x, "max_x": max_x, "min_y": min_y, "max_y": max_y},
            "nodes": nodes_summary,
            "edges": [
                {
                    "id": e.get("id"),
                    "from": e.get("fromNode"),
                    "to": e.get("toNode"),
                    "label": e.get("label"),
                    "color": e.get("color")
                }
                for e in edges
            ]
        }

    def create_canvas(self, file_path: str, overwrite: bool = False) -> Dict[str, Any]:
        p = self.resolve_path(file_path)
        if os.path.exists(p) and not overwrite:
            raise FileExistsError(f"Arquivo Canvas já existe: '{p}'. Use overwrite=True para substituir.")
        
        initial_data = {
            "nodes": [],
            "edges": []
        }
        _write_json_atomic(p, initial_data)
        return {
            "success": True,
            "file_path": p,
            "message": f"Canvas em branco criado com sucesso em '{p}'."
        }

    def add_node(
        self,
        file_path: str,
        node_type: str,
        content: str,
        node_id: Optional[str] = None,
        color: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        x: Optional[int] = None,
        y: Optional[int] = None,
        placement: Optional[str] = None,
        relative_to: Optional[str] = None,
        gap: int = 60
    ) -> Dict[str, Any]:
        p = self.resolve_path(file_path)
        data = _read_json_file(p)
        nodes = data.get("nodes", [])

        nid = node_id or f"node-{uuid.uuid4().hex[:8]}"
        if any(n.get("id") == nid for n in nodes):
            raise ValueError(f"ID de nó já existente no canvas: '{nid}'")

        w = width or DEFAULT_WIDTHS.get(node_type, 300)
        h = height or DEFAULT_HEIGHTS.get(node_type, 200)

        # Determinar coordenadas
        if x is not None and y is not None:
            pos_x, pos_y = x, y
        elif placement and relative_to:
            ref_node = next((n for n in nodes if n.get("id") == relative_to), None)
            if not ref_node:
                raise ValueError(f"Nó de referência '{relative_to}' não encontrado no canvas.")
            target_x, target_y = compute_relative_placement(ref_node, w, h, placement, gap)
            pos_x, pos_y = find_non_overlapping_position(
                target_x, target_y, w, h, nodes, direction=placement, gap=gap, is_group=(node_type == "group")
            )
        elif placement == "auto" or (x is None and y is None):
            if nodes:
                # Alocar abaixo do nó mais baixo ou ao lado do nó mais à direita
                max_y = max(n.get("y", 0) + n.get("height", 0) for n in nodes)
                first_x = nodes[0].get("x", 0)
                pos_x, pos_y = find_non_overlapping_position(
                    first_x, max_y + gap, w, h, nodes, direction="below", gap=gap, is_group=(node_type == "group")
                )
            else:
                pos_x, pos_y = 0, 0
        else:
            pos_x, pos_y = x or 0, y or 0

        # Montagem do nó conforme o tipo
        new_node: Dict[str, Any] = {
            "id": nid,
            "type": node_type,
            "x": int(pos_x),
            "y": int(pos_y),
            "width": int(w),
            "height": int(h),
        }
        if color:
            new_node["color"] = str(color)

        if node_type == "text":
            new_node["text"] = content
        elif node_type == "file":
            _check_privacy(content)
            new_node["file"] = content.replace("\\", "/")
        elif node_type == "link":
            new_node["url"] = content
        elif node_type == "group":
            new_node["label"] = content
        else:
            raise ValueError(f"Tipo de nó não suportado: '{node_type}'. Esperado: text, file, link, group.")

        nodes.append(new_node)
        data["nodes"] = nodes
        _write_json_atomic(p, data)

        return {
            "success": True,
            "node_id": nid,
            "node": new_node,
            "file_path": p
        }

    def update_node(
        self,
        file_path: str,
        node_id: str,
        content: Optional[str] = None,
        color: Optional[str] = None,
        x: Optional[int] = None,
        y: Optional[int] = None,
        width: Optional[int] = None,
        height: Optional[int] = None
    ) -> Dict[str, Any]:
        p = self.resolve_path(file_path)
        data = _read_json_file(p)
        nodes = data.get("nodes", [])

        node = next((n for n in nodes if n.get("id") == node_id), None)
        if not node:
            raise ValueError(f"Nó '{node_id}' não encontrado em '{p}'.")

        if content is not None:
            ntype = node.get("type")
            if ntype == "text":
                node["text"] = content
            elif ntype == "file":
                _check_privacy(content)
                node["file"] = content.replace("\\", "/")
            elif ntype == "link":
                node["url"] = content
            elif ntype == "group":
                node["label"] = content

        if color is not None:
            node["color"] = str(color)
        if x is not None:
            node["x"] = int(x)
        if y is not None:
            node["y"] = int(y)
        if width is not None:
            node["width"] = int(width)
        if height is not None:
            node["height"] = int(height)

        _write_json_atomic(p, data)
        return {
            "success": True,
            "node_id": node_id,
            "node": node,
            "file_path": p
        }

    def delete_node(
        self,
        file_path: str,
        node_id: str,
        cascade_edges: bool = True
    ) -> Dict[str, Any]:
        p = self.resolve_path(file_path)
        data = _read_json_file(p)
        nodes = data.get("nodes", [])
        edges = data.get("edges", [])

        initial_node_count = len(nodes)
        nodes = [n for n in nodes if n.get("id") != node_id]
        if len(nodes) == initial_node_count:
            raise ValueError(f"Nó '{node_id}' não encontrado para exclusão em '{p}'.")

        removed_edges_count = 0
        if cascade_edges:
            initial_edge_count = len(edges)
            edges = [e for e in edges if e.get("fromNode") != node_id and e.get("toNode") != node_id]
            removed_edges_count = initial_edge_count - len(edges)

        data["nodes"] = nodes
        data["edges"] = edges
        _write_json_atomic(p, data)

        return {
            "success": True,
            "deleted_node_id": node_id,
            "removed_edges_count": removed_edges_count,
            "file_path": p
        }

    def add_edge(
        self,
        file_path: str,
        from_node: str,
        to_node: str,
        edge_id: Optional[str] = None,
        from_side: Optional[str] = None,
        to_side: Optional[str] = None,
        from_end: str = "none",
        to_end: str = "arrow",
        color: Optional[str] = None,
        label: Optional[str] = None
    ) -> Dict[str, Any]:
        p = self.resolve_path(file_path)
        data = _read_json_file(p)
        nodes = data.get("nodes", [])
        edges = data.get("edges", [])

        node_a = next((n for n in nodes if n.get("id") == from_node), None)
        node_b = next((n for n in nodes if n.get("id") == to_node), None)
        if not node_a:
            raise ValueError(f"Nó de origem '{from_node}' não encontrado no canvas.")
        if not node_b:
            raise ValueError(f"Nó de destino '{to_node}' não encontrado no canvas.")

        eid = edge_id or f"edge-{uuid.uuid4().hex[:8]}"
        if any(e.get("id") == eid for e in edges):
            raise ValueError(f"ID de aresta já existente: '{eid}'")

        # Auto sides se não especificado
        f_side = from_side
        t_side = to_side
        if not f_side or not t_side or f_side == "auto" or t_side == "auto":
            auto_f, auto_t = compute_auto_sides(node_a, node_b)
            f_side = f_side if (f_side and f_side != "auto") else auto_f
            t_side = t_side if (t_side and t_side != "auto") else auto_t

        new_edge: Dict[str, Any] = {
            "id": eid,
            "fromNode": from_node,
            "fromSide": f_side,
            "toNode": to_node,
            "toSide": t_side,
            "fromEnd": from_end,
            "toEnd": to_end,
        }
        if color:
            new_edge["color"] = str(color)
        if label:
            new_edge["label"] = str(label)

        edges.append(new_edge)
        data["edges"] = edges
        _write_json_atomic(p, data)

        return {
            "success": True,
            "edge_id": eid,
            "edge": new_edge,
            "file_path": p
        }

    def delete_edge(
        self,
        file_path: str,
        edge_id: Optional[str] = None,
        from_node: Optional[str] = None,
        to_node: Optional[str] = None
    ) -> Dict[str, Any]:
        p = self.resolve_path(file_path)
        data = _read_json_file(p)
        edges = data.get("edges", [])

        initial_count = len(edges)
        if edge_id:
            edges = [e for e in edges if e.get("id") != edge_id]
        elif from_node and to_node:
            edges = [e for e in edges if not (e.get("fromNode") == from_node and e.get("toNode") == to_node)]
        else:
            raise ValueError("Especifique 'edge_id' ou ambos ('from_node', 'to_node') para exclusão.")

        if len(edges) == initial_count:
            raise ValueError(f"Nenhuma aresta correspondente encontrada para exclusão.")

        data["edges"] = edges
        _write_json_atomic(p, data)
        return {
            "success": True,
            "deleted_count": initial_count - len(edges),
            "file_path": p
        }

    def batch_edit(
        self,
        file_path: str,
        operations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Aplica uma lista de operações atômicas em memória e grava apenas uma vez."""
        p = self.resolve_path(file_path)
        data = _read_json_file(p)
        nodes = list(data.get("nodes", []))
        edges = list(data.get("edges", []))

        executed = 0
        for idx, op in enumerate(operations, 1):
            action = op.get("action")
            if not action:
                raise ValueError(f"Operação #{idx} sem atributo 'action'.")

            if action == "add_node":
                ntype = op.get("type", "text")
                nid = op.get("id") or f"node-{uuid.uuid4().hex[:8]}"
                if any(n.get("id") == nid for n in nodes):
                    raise ValueError(f"Op #{idx}: ID duplicado '{nid}'")
                w = op.get("width") or DEFAULT_WIDTHS.get(ntype, 300)
                h = op.get("height") or DEFAULT_HEIGHTS.get(ntype, 200)

                x = op.get("x")
                y = op.get("y")
                placement = op.get("placement")
                rel_to = op.get("relative_to")
                gap = op.get("gap", 60)

                if x is not None and y is not None:
                    pos_x, pos_y = x, y
                elif placement and rel_to:
                    ref_node = next((n for n in nodes if n.get("id") == rel_to), None)
                    if not ref_node:
                        raise ValueError(f"Op #{idx}: Nó de referência '{rel_to}' não encontrado.")
                    tx, ty = compute_relative_placement(ref_node, w, h, placement, gap)
                    pos_x, pos_y = find_non_overlapping_position(
                        tx, ty, w, h, nodes, direction=placement, gap=gap, is_group=(ntype == "group")
                    )
                else:
                    pos_x, pos_y = x or 0, y or 0

                n_dict: Dict[str, Any] = {
                    "id": nid,
                    "type": ntype,
                    "x": int(pos_x),
                    "y": int(pos_y),
                    "width": int(w),
                    "height": int(h),
                }
                if op.get("color"):
                    n_dict["color"] = str(op["color"])
                content = op.get("content", "")
                if ntype == "text":
                    n_dict["text"] = content
                elif ntype == "file":
                    _check_privacy(content)
                    n_dict["file"] = content.replace("\\", "/")
                elif ntype == "link":
                    n_dict["url"] = content
                elif ntype == "group":
                    n_dict["label"] = content
                nodes.append(n_dict)

            elif action == "update_node":
                nid = op.get("id")
                node = next((n for n in nodes if n.get("id") == nid), None)
                if not node:
                    raise ValueError(f"Op #{idx}: Nó '{nid}' não encontrado.")
                if "content" in op:
                    c = op["content"]
                    ntype = node.get("type")
                    if ntype == "text":
                        node["text"] = c
                    elif ntype == "file":
                        _check_privacy(c)
                        node["file"] = c.replace("\\", "/")
                    elif ntype == "link":
                        node["url"] = c
                    elif ntype == "group":
                        node["label"] = c
                for k in ("color", "x", "y", "width", "height"):
                    if k in op:
                        node[k] = op[k]

            elif action == "delete_node":
                nid = op.get("id")
                cascade = op.get("cascade_edges", True)
                nodes = [n for n in nodes if n.get("id") != nid]
                if cascade:
                    edges = [e for e in edges if e.get("fromNode") != nid and e.get("toNode") != nid]

            elif action == "add_edge":
                fn = op.get("from_node")
                tn = op.get("to_node")
                na = next((n for n in nodes if n.get("id") == fn), None)
                nb = next((n for n in nodes if n.get("id") == tn), None)
                if not na or not nb:
                    raise ValueError(f"Op #{idx}: nós '{fn}' ou '{tn}' não encontrados para criar aresta.")
                eid = op.get("id") or f"edge-{uuid.uuid4().hex[:8]}"
                auto_f, auto_t = compute_auto_sides(na, nb)
                edges.append({
                    "id": eid,
                    "fromNode": fn,
                    "fromSide": op.get("from_side") or auto_f,
                    "toNode": tn,
                    "toSide": op.get("to_side") or auto_t,
                    "fromEnd": op.get("from_end", "none"),
                    "toEnd": op.get("to_end", "arrow"),
                    **({"color": str(op["color"])} if op.get("color") else {}),
                    **({"label": str(op["label"])} if op.get("label") else {})
                })

            elif action == "delete_edge":
                eid = op.get("id")
                if eid:
                    edges = [e for e in edges if e.get("id") != eid]
                else:
                    fn, tn = op.get("from_node"), op.get("to_node")
                    edges = [e for e in edges if not (e.get("fromNode") == fn and e.get("toNode") == tn)]

            else:
                raise ValueError(f"Op #{idx}: ação desconhecida '{action}'")

            executed += 1

        data["nodes"] = nodes
        data["edges"] = edges
        _write_json_atomic(p, data)
        return {
            "success": True,
            "executed_operations": executed,
            "nodes_count": len(nodes),
            "edges_count": len(edges),
            "file_path": p
        }

    def validate_canvas(self, file_path: str) -> Dict[str, Any]:
        p = self.resolve_path(file_path)
        data = _read_json_file(p)
        nodes = data.get("nodes", [])
        edges = data.get("edges", [])

        errors = []
        warnings = []

        node_ids = set()
        for idx, n in enumerate(nodes):
            nid = n.get("id")
            if not nid:
                errors.append(f"Nó #{idx} sem ID.")
                continue
            if nid in node_ids:
                errors.append(f"ID duplicado de nó: '{nid}'")
            node_ids.add(nid)

            ntype = n.get("type")
            if ntype not in {"text", "file", "link", "group"}:
                errors.append(f"Nó '{nid}': tipo inválido '{ntype}'.")

            if ntype == "file":
                f_target = n.get("file", "")
                if PRIVACY_FOLDER in f_target:
                    errors.append(f"Nó '{nid}': violação de privacidade apontando para '{f_target}'.")
                else:
                    resolved = os.path.join(self.vault_root, f_target)
                    if not os.path.exists(resolved) and not os.path.exists(f_target):
                        warnings.append(f"Nó '{nid}' (file): arquivo alvo não localizado: '{f_target}'.")

        edge_ids = set()
        for idx, e in enumerate(edges):
            eid = e.get("id")
            if not eid:
                errors.append(f"Aresta #{idx} sem ID.")
                continue
            if eid in edge_ids:
                errors.append(f"ID duplicado de aresta: '{eid}'")
            edge_ids.add(eid)

            fn = e.get("fromNode")
            tn = e.get("toNode")
            if fn not in node_ids:
                errors.append(f"Aresta '{eid}': nó de origem '{fn}' inexistente.")
            if tn not in node_ids:
                errors.append(f"Aresta '{eid}': nó de destino '{tn}' inexistente.")

        # Checagem de colisões AABB entre cartões que não sejam grupos
        cards = [n for n in nodes if n.get("type") != "group"]
        for i in range(len(cards)):
            for j in range(i + 1, len(cards)):
                c1, c2 = cards[i], cards[j]
                if check_aabb_overlap(
                    c1.get("x", 0), c1.get("y", 0), c1.get("width", 0), c1.get("height", 0),
                    c2.get("x", 0), c2.get("y", 0), c2.get("width", 0), c2.get("height", 0)
                ):
                    warnings.append(f"Sobreposição espacial detectada entre '{c1.get('id')}' e '{c2.get('id')}'.")

        return {
            "file_path": p,
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "nodes_count": len(nodes),
            "edges_count": len(edges)
        }
