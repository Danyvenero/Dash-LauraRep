"""Utilities for building Dash AG Grid components with sensible defaults.

Provides helpers to build column definitions from a DataFrame
and a default gridOptions with visual filters, sorting, and column drag.
"""
from __future__ import annotations

from typing import List, Dict, Any, Optional, Iterable


def default_col_def() -> Dict[str, Any]:
    """Default column definition applied to all columns."""
    return {
        "sortable": True,
        "resizable": True,
        "filter": True,  # agTextColumnFilter or inferred by cellDataType
        "floatingFilter": True,
        "enableRowGroup": False,
        "menuTabs": ["filterMenuTab", "generalMenuTab", "columnsMenuTab"],
    }


def _value_formatter(kind: Optional[str], decimals: Optional[int] = None) -> Optional[Dict[str, str]]:
    """Return a valueFormatter object for AG Grid given a kind.

    kind: 'currency' | 'percent' | 'int' | 'float' | None
    """
    if not kind:
        return None
    if kind == "currency":
        return {"function": "d => (d.value == null ? '' : d.value.toLocaleString('pt-BR', {style:'currency', currency:'BRL'}))"}
    if kind == "percent":
        # Show N with % sign
        return {"function": "d => (d.value == null ? '' : `${Number(d.value).toLocaleString('pt-BR', {minimumFractionDigits: 0, maximumFractionDigits: 2})}%`)"}
    if kind == "int":
        return {"function": "d => (d.value == null ? '' : Number(d.value).toLocaleString('pt-BR', {maximumFractionDigits: 0}))"}
    if kind == "float":
        digits = 2 if decimals is None else max(0, int(decimals))
        return {"function": f"d => (d.value == null ? '' : Number(d.value).toLocaleString('pt-BR', {{minimumFractionDigits: {digits}, maximumFractionDigits: {digits}}}))"}
    return None


def build_column_defs(
    columns: Iterable[str],
    numeric_cols: Optional[Iterable[str]] = None,
    formats: Optional[Dict[str, str]] = None,
    display_names: Optional[Dict[str, str]] = None,
) -> List[Dict[str, Any]]:
    """Build columnDefs with optional numeric detection, formats, and custom headers.

    - numeric_cols: fields treated as numeric (right aligned, numeric filter)
    - formats: mapping field -> 'currency'|'percent'|'int'|'float' for valueFormatter
    - display_names: mapping field -> headerName
    """
    numeric = set(numeric_cols or [])
    fmts = formats or {}
    names = display_names or {}
    col_defs: List[Dict[str, Any]] = []
    for field in columns:
        is_num = field in numeric
        kind = fmts.get(field)
        header = names.get(field, field)
        col_def: Dict[str, Any] = {
            "headerName": header,
            "field": field,
            "filter": "agNumberColumnFilter" if is_num else "agTextColumnFilter",
        }
        # Style/typing
        if is_num:
            col_def["type"] = "numericColumn"
            col_def["cellStyle"] = {"textAlign": "right"}
        # Formatting
        fmt = _value_formatter(kind)
        if fmt:
            col_def["valueFormatter"] = fmt
        col_defs.append(col_def)
    return col_defs


def build_coldefs_from_datatable(columns_dt: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert dash_table-like column specs to AG Grid columnDefs.

    columns_dt items expect keys: id (field), name (header), type ('numeric'|'text'),
    optionally format specifier ignored here.
    """
    result: List[Dict[str, Any]] = []
    for col in columns_dt:
        field = col.get("id") or col.get("name")
        header = col.get("name") or field
        is_num = (col.get("type") == "numeric")
        # Heuristic formatting by header
        kind: Optional[str] = None
        if isinstance(header, str):
            if header.endswith('(%)'):
                kind = 'percent'
            elif header in {"Faturamento Total", "Valor Médio", "Ticket Médio (Cotação Ano)"}:
                kind = 'currency'
            elif is_num:
                kind = 'float'
        col_def: Dict[str, Any] = {
            "headerName": header,
            "field": field,
            "filter": "agNumberColumnFilter" if is_num else "agTextColumnFilter",
        }
        if is_num:
            col_def["type"] = "numericColumn"
            col_def["cellStyle"] = {"textAlign": "right"}
        fmt = _value_formatter(kind)
        if fmt:
            col_def["valueFormatter"] = fmt
        result.append(col_def)
    return result


def default_grid_options(paginationPageSize: Optional[int] = None) -> Dict[str, Any]:
    """Default gridOptions for a nice UX out of the box.

    Includes native pagination page-size selector for convenience.
    """
    opts = {
        "animateRows": True,
        "suppressRowClickSelection": False,
        "rowSelection": "multiple",
        "pagination": True,
        # paginationPageSize set per-grid
        "enableRangeSelection": True,
        "domLayout": "autoHeight",  # grows with content unless constrained by style
        "ensureDomOrder": True,
        # Exibir seletor nativo de tamanho de página (quando suportado)
        "paginationPageSizeSelector": [10, 25, 50, 100],
    }
    if paginationPageSize is not None:
        opts["paginationPageSize"] = int(paginationPageSize)
    return opts
