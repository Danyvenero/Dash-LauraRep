import pandas as pd
from utils.data_loader_fixed import DataLoaderFixed


def test_normalize_produtos_cotados_material_string_safe():
    dl = DataLoaderFixed()
    df = pd.DataFrame({
        'cotacao': ['C1', 'C2', 'C3', 'C4', 'C5', 'C6'],
        'cod_cliente': ['1', '2', '3', '4', '5', '6'],
        'material': [12345.0, '001234', 'abc-001', ' 12345 ', 'nan', None],
        'quantidade': [1, 1, 1, 1, 1, 1],
        'preco_liquido_unitario': [0, 0, 0, 0, 0, 0],
        'preco_liquido_total': [0, 0, 0, 0, 0, 0]
    })
    out = dl.normalize_produtos_cotados_data(df)
    mats = out['material'].tolist()
    # Linhas com material ausente são removidas pelo dropna(require material)
    assert len(mats) == 4
    assert mats[0] == '12345'
    assert mats[1] == '001234'
    assert mats[2] == 'ABC-001'
    assert mats[3] == '12345'


def test_normalize_vendas_material_string_safe():
    dl = DataLoaderFixed()
    df = pd.DataFrame({
        'cod_cliente': ['10'],
        'material': ['000789'],
        'produto': ['X'],
        'data': ['2025-01-01'],
        'vlr_rol': [100]
    })
    out = dl.normalize_vendas_data(df)
    assert out.loc[0, 'material'] == '000789'
