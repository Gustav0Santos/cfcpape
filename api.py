# Importamos o Flask, que é a framework que vai criar o nosso servidor web
from flask import Flask, request, jsonify

# Importamos a biblioteca que permite ligar ao SQL Server
import pyodbc

# Criamos a aplicacao Flask
# "app" vai ser o nosso servidor backend
app = Flask(__name__)


# ---------------------------------------------------------
# Funcao que cria uma ligacao com a base de dados
# Sempre que for preciso falar com o SQL, chamamos esta funcao
# ---------------------------------------------------------
def ligar_bd():

    # pyodbc.connect cria uma conexao ao SQL Server usando a connection string
    return pyodbc.connect(
        "Driver={ODBC Driver 17 for SQL Server};"
        "Server=GSANTINHOPC;"
        "Database=cfc_pape;"
        "Trusted_Connection=yes;"
    )


# ---------------------------------------------------------
# Funcao para verificar se uma tabela existe na base de dados
# Isto evita erros quando o utilizador tenta usar uma tabela invalida
# ---------------------------------------------------------
def tabela_existe(tabela):

    # Abrimos conexao com a base de dados
    conn = ligar_bd()

    # O cursor permite executar comandos SQL
    cursor = conn.cursor()

    # Esta query consulta o sistema do SQL Server para ver se a tabela existe
    cursor.execute("""
        SELECT TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = ?
    """, tabela)

    # fetchone() devolve uma linha se encontrar resultado
    resultado = cursor.fetchone()

    # Fechamos a conexao para libertar recursos
    conn.close()

    # Se encontrou algo, devolve True, senao False
    return resultado is not None


#---------------------------------------------------------------
# caso o ip seja só http://127.0.0.1:5000
# ao invés de mostrar uma página com a mensagem de erro
# vai mostrar isto
#---------------------------------------------------------------
@app.route("/")
def home():
    return "API a funcionar!"


# ---------------------------------------------------------
# ENDPOINT SELECT
# Devolve todos os registos de uma tabela em formato JSON
# ---------------------------------------------------------

# @app.route significa:
# estamos a criar um endereço URL que pode ser chamado pelo browser ou JavaScript
# <tabela> significa que o nome da tabela vem dinamicamente no URL
@app.route("/api/<tabela>/select", methods=["GET"])
def select(tabela):

    # Antes de fazer qualquer coisa verificamos se a tabela existe
    if not tabela_existe(tabela):
        return jsonify({"erro": "Tabela nao existe"}), 400

    conn = ligar_bd()
    cursor = conn.cursor()

    # Executamos uma query SQL dinamica para ir buscar todos os dados da tabela
    cursor.execute(f"SELECT * FROM {tabela}")

    # cursor.description contem informacao sobre as colunas devolvidas
    # Aqui extraimos apenas os nomes das colunas
    colunas = [column[0] for column in cursor.description]

    resultados = []

    # fetchall() devolve todas as linhas encontradas
    for linha in cursor.fetchall():

        # zip junta cada valor da linha com o nome da respetiva coluna
        # dict() converte isso num dicionario
        resultados.append(dict(zip(colunas, linha)))

    conn.close()

    print(resultados)

    # jsonify converte a lista de dicionarios em JSON para enviar para o frontend
    return jsonify(resultados)


# ---------------------------------------------------------
# ENDPOINT INSERT
# Permite inserir novos registos numa tabela
# ---------------------------------------------------------
@app.route("/api/<tabela>/insert", methods=["POST"])
def insert(tabela):

    if not tabela_existe(tabela):
        return jsonify({"erro": "Tabela nao existe"}), 400

    # request.json contem os dados enviados pelo frontend em formato JSON
    dados = request.json

    conn = ligar_bd()
    cursor = conn.cursor()

    # Aqui construimos dinamicamente os nomes das colunas
    # Exemplo: "nome, email, idade"
    colunas = ", ".join(dados.keys())

    # Criamos os placeholders ? para cada valor
    # Exemplo: "?, ?, ?"
    valores = ", ".join(["?"] * len(dados))

    # Construimos a query final de INSERT
    query = f"INSERT INTO {tabela} ({colunas}) VALUES ({valores})"

    # Executamos a query passando os valores reais
    cursor.execute(query, list(dados.values()))

    conn.commit()
    conn.close()

    return jsonify({"mensagem": "Registo inserido com sucesso"})


# ---------------------------------------------------------
# ENDPOINT UPDATE
# Atualiza um registo existente com base no ID
# ---------------------------------------------------------
@app.route("/api/<tabela>/update/<id>", methods=["POST"])
def update(tabela, id):

    if not tabela_existe(tabela):
        return jsonify({"erro": "Tabela nao existe"}), 400

    dados = request.json

    conn = ligar_bd()
    cursor = conn.cursor()

    # Aqui criamos dinamicamente a parte SET da query
    # Exemplo: "nome = ?, email = ?, idade = ?"
    campos = ", ".join([f"{k} = ?" for k in dados.keys()])

    # Criamos a query final de UPDATE
    query = f"UPDATE {tabela} SET {campos} WHERE id = ?"

    # Passamos os valores a atualizar + o ID no fim
    cursor.execute(query, list(dados.values()) + [id])

    conn.commit()
    conn.close()

    return jsonify({"mensagem": "Registo atualizado com sucesso"})


# ---------------------------------------------------------
# ENDPOINT DELETE
# Apaga um registo de uma tabela com base no ID
# ---------------------------------------------------------
@app.route("/api/<tabela>/delete/<id>", methods=["POST"])
def delete(tabela, id):

    if not tabela_existe(tabela):
        return jsonify({"erro": "Tabela nao existe"}), 400

    conn = ligar_bd()
    cursor = conn.cursor()

    # Query simples para apagar um registo pelo ID
    query = f"DELETE FROM {tabela} WHERE id = ?"

    cursor.execute(query, id)

    conn.commit()
    conn.close()

    return jsonify({"mensagem": "Registo apagado com sucesso"})


# ---------------------------------------------------------
# ENDPOINT CAMPOS
# Devolve apenas os nomes das colunas de uma tabela
# Isto e util para criar formularios dinamicos no site
# ---------------------------------------------------------
@app.route("/api/<tabela>/campos", methods=["GET"])
def campos(tabela):

    if not tabela_existe(tabela):
        return jsonify({"erro": "Tabela nao existe"}), 400

    conn = ligar_bd()
    cursor = conn.cursor()

    # SELECT TOP 0 devolve zero registos
    # mas permite-nos obter informacao sobre as colunas da tabela
    cursor.execute(f"SELECT TOP 0 * FROM {tabela}")

    # Extraimos apenas os nomes das colunas
    colunas = [column[0] for column in cursor.description]

    conn.close()

    return jsonify(colunas)

if __name__ == "__main__":
    app.run(debug=True)
