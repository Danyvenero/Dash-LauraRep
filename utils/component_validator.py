"""
Utilitário para validação de componentes Dash
"""
import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from typing import Any, Union, List


def validate_dash_component(component: Any, component_name: str = "component") -> Any:
    """
    Valida se um objeto é um componente Dash válido
    
    Args:
        component: Objeto a ser validado
        component_name: Nome do componente para logging
        
    Returns:
        Componente válido ou componente de erro
    """
    # Tipos válidos para children
    valid_types = (str, int, float, list, type(None))
    
    # Verificar se é None
    if component is None:
        print(f"⚠️ {component_name} é None")
        return html.Div([
            dbc.Alert(f"Erro: {component_name} não foi encontrado", color="warning")
        ])
    
    # Verificar se é um tipo básico válido
    if isinstance(component, valid_types):
        return component
    
    # Verificar se é um componente Dash válido
    if hasattr(component, '__module__') and ('dash' in component.__module__ or 'dash_bootstrap_components' in component.__module__):
        # Verificar se tem children e validá-los recursivamente
        if hasattr(component, 'children') and component.children is not None:
            validated_children = validate_children(component.children, f"{component_name}.children")
            # Se children foi modificado, criar novo componente
            if validated_children != component.children:
                # Criar nova instância com children validados
                new_props = component._props.copy() if hasattr(component, '_props') else {}
                new_props['children'] = validated_children
                return component.__class__(**new_props)
        
        return component
    
    # Se chegou aqui, não é um componente válido
    print(f"❌ {component_name} não é um componente Dash válido: {type(component)}")
    print(f"   Atributos: {dir(component)[:10]}...")  # Primeiros 10 atributos
    
    return html.Div([
        dbc.Alert(
            f"Erro: {component_name} tem tipo inválido ({type(component).__name__})", 
            color="danger"
        )
    ])


def validate_children(children: Any, parent_name: str = "parent") -> Any:
    """
    Valida recursivamente uma estrutura de children
    
    Args:
        children: Estrutura de children a ser validada
        parent_name: Nome do componente pai para logging
        
    Returns:
        Children validados
    """
    if children is None:
        return None
    
    if isinstance(children, (str, int, float)):
        return children
    
    if isinstance(children, list):
        validated_list = []
        for i, child in enumerate(children):
            validated_child = validate_dash_component(child, f"{parent_name}[{i}]")
            validated_list.append(validated_child)
        return validated_list
    
    # Se não é lista, valida como componente único
    return validate_dash_component(children, f"{parent_name}.child")


def safe_component_return(component: Any, fallback_message: str = "Erro desconhecido") -> Any:
    """
    Retorna um componente validado ou um erro seguro
    
    Args:
        component: Componente a ser validado
        fallback_message: Mensagem de erro em caso de falha
        
    Returns:
        Componente válido
    """
    try:
        validated = validate_dash_component(component, "return_component")
        return validated
    except Exception as e:
        print(f"❌ Erro na validação de componente: {e}")
        return html.Div([
            dbc.Alert(f"{fallback_message}: {str(e)}", color="danger"),
            html.P("Por favor, recarregue a página ou contate o suporte.")
        ])