"""
Configuração Flask para CLI
"""

import os
from webapp import server

# Configuração para Flask CLI
if __name__ == '__main__':
    # Define variáveis de ambiente para Flask
    os.environ['FLASK_APP'] = 'flask_app.py'
    os.environ['FLASK_ENV'] = 'development'
    
    # Executa aplicação Flask
    server.run(debug=True)
else:
    # Exporta app para uso com flask CLI
    app = server
