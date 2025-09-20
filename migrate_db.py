"""
Database migration script to add numero_revisao column to cotacoes table
"""
import sqlite3
from pathlib import Path

def migrate_database():
    """Add missing columns to existing database - otimizado para startup"""
    
    DB_PATH = Path('instance/database.sqlite')
    
    if not DB_PATH.exists():
        print("❌ Database does not exist. Run init-db first.")
        return False
    
    # Otimização: Verifica se migração é necessária antes de abrir conexão
    needs_migration = False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Verificação rápida se colunas existem
        cursor.execute('PRAGMA table_info(cotacoes)')
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        # Verifica se alguma migração é necessária
        required_columns = ['numero_revisao', 'linhas_cotacao', 'status_cotacao']
        missing_columns = [col for col in required_columns if col not in column_names]
        has_old_schema = 'material' in column_names or 'quantidade' in column_names
        
        if not missing_columns and not has_old_schema:
            print("✅ Database schema is up to date - no migration needed")
            conn.close()
            return True
        
        print("📋 Current cotacoes columns:", column_names)
        
        # Adiciona colunas faltantes
        for column in missing_columns:
            print(f"🔧 Adding {column} column...")
            cursor.execute(f'ALTER TABLE cotacoes ADD COLUMN {column} TEXT')
            print(f"✅ Added {column} column")
        
        # Trata schema antigo se necessário
        if has_old_schema:
            print("🔧 Old schema detected. Recreating cotacoes table...")
            
            # Backup apenas se há dados
            cursor.execute('SELECT COUNT(*) FROM cotacoes')
            count = cursor.fetchone()[0]
            
            if count > 0:
                print(f"⚠️  Found {count} existing records. Creating backup...")
                cursor.execute('CREATE TABLE cotacoes_backup AS SELECT * FROM cotacoes')
            
            # Drop and recreate table
            cursor.execute('DROP TABLE cotacoes')
            cursor.execute('''
                CREATE TABLE cotacoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dataset_id INTEGER,
                    numero_cotacao TEXT,
                    numero_revisao TEXT,
                    linhas_cotacao TEXT,
                    status_cotacao TEXT,
                    cod_cliente TEXT,
                    cliente TEXT,
                    data DATE,
                    FOREIGN KEY (dataset_id) REFERENCES datasets (id)
                )
            ''')
            
            # Recreate indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_cotacoes_cliente_data ON cotacoes(cod_cliente, data, numero_cotacao)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_cotacoes_numero ON cotacoes(numero_cotacao)')
            
            print("✅ Cotacoes table recreated with correct schema")
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        conn.rollback()
        conn.close()
        return False

if __name__ == "__main__":
    migrate_database()
