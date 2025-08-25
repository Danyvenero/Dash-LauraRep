# app.py

# Importa a aplicação já configurada do nosso pacote 'webapp'
from webapp import app, server

# Ponto de Entrada para Execução
if __name__ == '__main__':
    app.run(debug=True)