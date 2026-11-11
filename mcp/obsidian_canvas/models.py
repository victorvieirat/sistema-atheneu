"""Modelos de dados Pydantic para a especificação JSON Canvas 1.0.

Referência: https://jsoncanvas.org/spec/1.0/
"""

from typing import Literal, Optional, Union, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
import re

CanvasColor = str  # Preset "1".."6" ou "#RRGGBB"
NodeSide = Literal["top", "right", "bottom", "left"]
EdgeEnd = Literal["none", "arrow"]
NodeType = Literal["text", "file", "link", "group"]


class BaseNode(BaseModel):
    id: str = Field(..., description="Identificador único do nó")
    type: NodeType = Field(..., description="Tipo do nó: text, file, link ou group")
    x: int = Field(..., description="Posição horizontal X em pixels")
    y: int = Field(..., description="Posição vertical Y em pixels")
    width: int = Field(..., description="Largura do nó em pixels")
    height: int = Field(..., description="Altura do nó em pixels")
    color: Optional[CanvasColor] = Field(None, description="Cor predefinida ('1'..'6') ou hex '#RRGGBB'")

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = str(v).strip()
        if v in {"1", "2", "3", "4", "5", "6"}:
            return v
        if re.match(r"^#(?:[0-9a-fA-F]{3}){1,2}$", v):
            return v
        raise ValueError(f"Cor inválida '{v}'. Esperado '1'..'6' ou '#RRGGBB'.")


class TextNode(BaseNode):
    type: Literal["text"] = "text"
    text: str = Field(..., description="Conteúdo em texto/markdown do cartão")


class FileNode(BaseNode):
    type: Literal["file"] = "file"
    file: str = Field(..., description="Caminho relativo da nota ou anexo dentro do cofre")
    subpath: Optional[str] = Field(None, description="Subcaminho opcional (#heading ou #^block)")


class LinkNode(BaseNode):
    type: Literal["link"] = "link"
    url: str = Field(..., description="URL externa HTTP/HTTPS")


class GroupNode(BaseNode):
    type: Literal["group"] = "group"
    label: Optional[str] = Field(None, description="Título/rótulo do grupo de cartões")
    background: Optional[str] = Field(None, description="Caminho de imagem de fundo")
    backgroundStyle: Optional[Literal["cover", "ratio", "repeat"]] = Field(None, description="Estilo de repetição/escala do fundo")


CanvasNode = Union[TextNode, FileNode, LinkNode, GroupNode]


class CanvasEdge(BaseModel):
    id: str = Field(..., description="Identificador único da aresta")
    fromNode: str = Field(..., description="ID do nó de origem")
    fromSide: Optional[NodeSide] = Field(None, description="Lado de saída da conexão")
    fromEnd: Optional[EdgeEnd] = Field("none", description="Terminação na origem ('none' ou 'arrow')")
    toNode: str = Field(..., description="ID do nó de destino")
    toSide: Optional[NodeSide] = Field(None, description="Lado de entrada da conexão")
    toEnd: Optional[EdgeEnd] = Field("arrow", description="Terminação no destino ('none' ou 'arrow')")
    color: Optional[CanvasColor] = Field(None, description="Cor da linha")
    label: Optional[str] = Field(None, description="Texto descritivo exibido sobre a aresta")


class CanvasData(BaseModel):
    nodes: List[Dict[str, Any]] = Field(default_factory=list, description="Lista de nós do canvas")
    edges: List[CanvasEdge] = Field(default_factory=list, description="Lista de conexões entre nós")
