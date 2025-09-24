import pandas as pd
from utils.data_loader_fixed import DataLoaderFixed


def test_cod_material_variants_are_mapped():
    dl = DataLoaderFixed()
    df = pd.DataFrame({
        'cotacao': ['C1', 'C2', 'C3', 'C4'],
        'cod_cliente': ['1','2','3','4'],
        'Cod Material': ['001234', ' 12345 ', 'ABC-9', '12345.0'],
        'quantidade': [1,1,1,1],
        'preco_liquido_unitario': [0,0,0,0],
        'preco_liquido_total': [0,0,0,0]
    })
    out = dl.normalize_produtos_cotados_data(df)
    assert 'material' in out.columns
    assert out.loc[0, 'material'] == '001234'
    assert out.loc[1, 'material'] == '12345'
    assert out.loc[2, 'material'] == 'ABC-9'
    assert out.loc[3, 'material'] == '12345'
