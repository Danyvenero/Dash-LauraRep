"""
Comandos CLI personalizados para o sistema Dashboard WEG
"""

import click
from flask.cli import with_appcontext
from utils.db import init_db, get_dataset_statistics
import sqlite3
import os

def init_app(app):
    """Registra comandos CLI no app Flask"""
    app.cli.add_command(init_db_command)
    app.cli.add_command(stats_command)
    app.cli.add_command(reset_db_command)
    app.cli.add_command(check_db_command)

@click.command('init-db')
@with_appcontext
def init_db_command():
    """Inicializa o banco de dados criando todas as tabelas."""
    try:
        init_db()
        click.echo('✅ Banco de dados inicializado com sucesso!')
    except Exception as e:
        click.echo(f'❌ Erro ao inicializar banco: {str(e)}')

@click.command('db-stats')
@with_appcontext
def stats_command():
    """Mostra estatísticas do banco de dados."""
    try:
        stats = get_dataset_statistics()
        click.echo('📊 ESTATÍSTICAS DO BANCO DE DADOS')
        click.echo('=' * 40)
        click.echo(f'Total de datasets: {stats["total_datasets"]}')
        click.echo(f'Total de vendas: {stats["total_vendas"]}')
        click.echo(f'Total de cotações: {stats["total_cotacoes"]}')
        click.echo(f'Total de produtos cotados: {stats["total_produtos_cotados"]}')
        click.echo()
        
        if stats['recent_datasets']:
            click.echo('📋 DATASETS RECENTES:')
            for ds in stats['recent_datasets']:
                click.echo(f"  • {ds['name']} - {ds['uploaded_at']}")
                click.echo(f"    Vendas: {ds['tem_vendas']} | Cotações: {ds['tem_cotacoes']} | Produtos: {ds['tem_produtos']}")
        else:
            click.echo('📋 Nenhum dataset encontrado.')
            
    except Exception as e:
        click.echo(f'❌ Erro ao obter estatísticas: {str(e)}')

@click.command('reset-db')
@click.option('--confirm', is_flag=True, help='Confirma a operação sem perguntar.')
@with_appcontext
def reset_db_command(confirm):
    """Remove e recria completamente o banco de dados."""
    if not confirm:
        click.confirm('⚠️  Esta operação irá APAGAR TODOS OS DADOS! Continuar?', abort=True)
    
    try:
        # Remove banco existente
        db_path = 'instance/database.sqlite'
        if os.path.exists(db_path):
            os.remove(db_path)
            click.echo('🗑️  Banco de dados anterior removido.')
        
        # Recria banco
        init_db()
        click.echo('✅ Banco de dados recriado com sucesso!')
        
    except Exception as e:
        click.echo(f'❌ Erro ao resetar banco: {str(e)}')

@click.command('check-db')
@with_appcontext
def check_db_command():
    """Verifica a integridade e estrutura do banco de dados."""
    try:
        conn = sqlite3.connect('instance/database.sqlite')
        cursor = conn.cursor()
        
        click.echo('🔍 VERIFICAÇÃO DO BANCO DE DADOS')
        click.echo('=' * 40)
        
        # Lista todas as tabelas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        click.echo(f'📋 Tabelas encontradas: {len(tables)}')
        for table in tables:
            table_name = table[0]
            
            # Conta registros em cada tabela
            count = cursor.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            
            # Verifica estrutura da tabela
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            click.echo(f"  • {table_name}: {count} registros, {len(columns)} colunas")
        
        # Verifica índices
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index';")
        indexes = cursor.fetchall()
        click.echo(f'📊 Índices encontrados: {len(indexes)}')
        
        # Verifica integridade
        cursor.execute("PRAGMA integrity_check;")
        integrity = cursor.fetchone()
        
        if integrity[0] == 'ok':
            click.echo('✅ Integridade do banco: OK')
        else:
            click.echo(f'❌ Problema de integridade: {integrity[0]}')
        
        conn.close()
        
    except Exception as e:
        click.echo(f'❌ Erro ao verificar banco: {str(e)}')
