"""
Database migration script to add numero_revisao column to cotacoes table
"""
import sqlite3
from pathlib import Path

def migrate_database():
    """Add missing columns to existing database"""
    
    DB_PATH = Path('instance/database.sqlite')
    
    if not DB_PATH.exists():
        print("❌ Database does not exist. Run init-db first.")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if numero_revisao column exists
        cursor.execute('PRAGMA table_info(cotacoes)')
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        print("📋 Current cotacoes columns:", column_names)
        
        if 'numero_revisao' not in column_names:
            print("🔧 Adding numero_revisao column...")
            cursor.execute('ALTER TABLE cotacoes ADD COLUMN numero_revisao TEXT')
            print("✅ Added numero_revisao column")
        else:
            print("✅ numero_revisao column already exists")
            
        if 'linhas_cotacao' not in column_names:
            print("🔧 Adding linhas_cotacao column...")
            cursor.execute('ALTER TABLE cotacoes ADD COLUMN linhas_cotacao TEXT')
            print("✅ Added linhas_cotacao column")
        else:
            print("✅ linhas_cotacao column already exists")
            
        if 'status_cotacao' not in column_names:
            print("🔧 Adding status_cotacao column...")
            cursor.execute('ALTER TABLE cotacoes ADD COLUMN status_cotacao TEXT')
            print("✅ Added status_cotacao column")
        else:
            print("✅ status_cotacao column already exists")
        
        # Remove old columns that don't match schema
        if 'material' in column_names or 'quantidade' in column_names:
            print("🔧 Old schema detected. Recreating cotacoes table...")
            
            # Backup existing data if any
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
        
        # Final verification
        cursor.execute('PRAGMA table_info(cotacoes)')
        final_columns = cursor.fetchall()
        print("\n📋 Final cotacoes table structure:")
        for col in final_columns:
            print(f"  - {col[1]} ({col[2]})")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        conn.rollback()
        conn.close()
        return False

if __name__ == "__main__":
    migrate_database()
