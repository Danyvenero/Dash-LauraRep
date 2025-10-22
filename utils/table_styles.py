"""
Shared Dash DataTable style dictionaries to keep a consistent look & feel
across Products and Clients tables.
"""

# Header: blue background with white text, bold, centered
TABLE_STYLE_HEADER_PRIMARY = {
    "backgroundColor": "#0d6efd",
    "color": "white",
    "fontWeight": "bold",
    "textAlign": "center",
}

# Cells: left aligned, comfortable padding, consistent font
TABLE_STYLE_CELL_DEFAULT = {
    "textAlign": "left",
    "padding": "10px",
    "fontFamily": "Arial, sans-serif",
    "fontSize": 12,
}

# Table container: horizontal scroll and full width
TABLE_STYLE_TABLE_FULL_WIDTH = {
    "overflowX": "auto",
    "minWidth": "100%",
}
