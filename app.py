from flask import Flask, render_template, request, redirect, url_for, session, send_file, send_from_directory
import os
import pandas as pd
import re
import csv
import random
import string

# ======================== CONFIGURAÇÃO DO APP ========================


app = Flask(__name__)
app.secret_key = "28tAPZgsRJP3sBzg"  # Chave para sessão segura
UPLOAD_FOLDER = "uploads"
DATA_FOLDER = "data"
CSV_FILE = os.path.join(DATA_FOLDER, "usuarios.csv")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DATA_FOLDER, exist_ok=True)

# Credenciais do Administrador (Usuário Master)
ADMIN_LOGIN = "Admin"
ADMIN_SENHA = "SenhaForte!@#2024"


# ======================== FUNÇÕES AUXILIARES ========================


def gerar_senha():
    """Gera uma senha aleatória de 8 caracteres."""
    caracteres = string.ascii_letters + string.digits
    return ''.join(random.choice(caracteres) for _ in range(8))


def carregar_usuarios():
    """Carrega os CNPJs cadastrados no sistema a partir do CSV."""
    usuarios = []
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                usuarios.append({
                    "cnpj": row["cnpj"],
                    "nome": row["nome"],
                    "tabela": row["tabela"] if row["tabela"] else None,
                    "senha": row["senha"] if "senha" in row else gerar_senha()
                })
    return usuarios


def salvar_usuarios(usuarios):
    """Salva a lista de CNPJs no CSV."""
    with open(CSV_FILE, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["cnpj", "nome", "tabela", "senha"])
        writer.writeheader()
        for usuario in usuarios:
            writer.writerow(usuario)


# Inicializa o CSV se não existir
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["cnpj", "nome", "tabela", "senha"])
        writer.writeheader()


# ======================== ROTAS DE AUTENTICAÇÃO ========================


@app.route("/", methods=["GET", "POST"])
def login():
    """Tela de login para o sistema"""
    if request.method == "POST":
        cnpj = request.form["cnpj"]
        senha = request.form["senha"]

        if cnpj == ADMIN_LOGIN and senha == ADMIN_SENHA:
            session["usuario"] = ADMIN_LOGIN
            return redirect(url_for("admin_dashboard"))

        usuarios = carregar_usuarios()
        for usuario in usuarios:
            if usuario["cnpj"] == cnpj and usuario["senha"] == senha:
                session["usuario"] = usuario["cnpj"]
                return redirect(url_for("dashboard"))

        return render_template("index.html", erro="CNPJ ou Senha inválidos")

    return render_template("index.html", erro=None)


@app.route("/logout", methods=["POST"])
def logout():
    """Desloga o usuário e redireciona para a tela de login"""
    session.pop("usuario", None)
    return redirect(url_for("login"))


# ======================== ROTAS DO DASHBOARD ========================


@app.route("/dashboard")
def dashboard():
    if "usuario" not in session:
        return redirect(url_for("login"))

    cnpj_usuario = session["usuario"]
    usuarios = carregar_usuarios()

    # Encontrar o usuário logado e exibir apenas os processos dele
    usuario = next((user for user in usuarios if user["cnpj"] == cnpj_usuario), None)
    if not usuario:
        return "Erro: Usuário não encontrado.", 404

    # Listar apenas os arquivos do usuário logado
    pasta_cnpj = os.path.join(UPLOAD_FOLDER, cnpj_usuario)
    processos = []
    arquivos = {}  # Inicializa o dicionário de arquivos

    if os.path.exists(pasta_cnpj):
        for arquivo in os.listdir(pasta_cnpj):
            if arquivo.endswith(".xlsx"):
                processos.append(arquivo)

        # Adiciona os documentos anexados por referência
        for referencia in os.listdir(pasta_cnpj):
            pasta_referencia = os.path.join(pasta_cnpj, referencia)
            if os.path.isdir(pasta_referencia):  # Verifica se é uma pasta de referência
                arquivos[referencia] = {
                    "bl": os.path.exists(os.path.join(pasta_referencia, f"BL_{referencia}.pdf")),
                    "invoice": os.path.exists(os.path.join(pasta_referencia, f"Invoice_{referencia}.pdf")),
                    "packing_list": os.path.exists(os.path.join(pasta_referencia, f"PackingList_{referencia}.pdf")),
                    "li": os.path.exists(os.path.join(pasta_referencia, f"LI_{referencia}.pdf")),
                    "di": os.path.exists(os.path.join(pasta_referencia, f"DI_{referencia}.pdf")),
                }

    return render_template("dashboard.html", usuario=usuario, processos=processos, arquivos=arquivos)

@app.route("/admin_dashboard")
def admin_dashboard():
    """Painel administrativo onde o Admin pode gerenciar os CNPJs"""
    if "usuario" not in session or session["usuario"] != ADMIN_LOGIN:
        return redirect(url_for("login"))

    return render_template("admin_dashboard.html", usuarios=carregar_usuarios())


# ======================== GERENCIAMENTO DE CNPJs ========================


@app.route("/add_cnpj", methods=["POST"])
def add_cnpj():
    """Adiciona um novo CNPJ ao sistema e gera uma senha aleatória"""
    if "usuario" not in session or session["usuario"] != ADMIN_LOGIN:
        return redirect(url_for("login"))

    cnpj = request.form.get("cnpj")
    nome = request.form.get("nome")

    if not cnpj or not re.match(r"^\d{14}$", cnpj):
        return "Erro: CNPJ inválido. Deve conter exatamente 14 dígitos numéricos.", 400

    usuarios = carregar_usuarios()

    if any(usuario["cnpj"] == cnpj for usuario in usuarios):
        return "Erro: CNPJ já cadastrado.", 400

    senha_gerada = gerar_senha()

    # Adiciona o novo usuário com a senha gerada
    usuarios.append({"cnpj": cnpj, "nome": nome, "tabela": None, "senha": senha_gerada})
    salvar_usuarios(usuarios)

    return redirect(url_for("admin_dashboard"))


@app.route("/delete_cnpj/<cnpj>", methods=["POST"])
def delete_cnpj(cnpj):
    """Exclui um CNPJ do sistema"""
    if "usuario" not in session or session["usuario"] != ADMIN_LOGIN:
        return redirect(url_for("login"))

    usuarios = [usuario for usuario in carregar_usuarios() if usuario["cnpj"] != cnpj]
    salvar_usuarios(usuarios)

    return redirect(url_for("admin_dashboard"))


# ======================== GERENCIAMENTO DE PLANILHAS ========================


@app.route("/upload/<cnpj>", methods=["POST"])
def upload_file(cnpj):
    """Faz o upload de uma planilha para um CNPJ"""
    if "usuario" not in session or session["usuario"] != ADMIN_LOGIN:
        return redirect(url_for("login"))

    file = request.files.get("file")
    if not file or file.filename == "":
        return redirect(url_for("admin_dashboard"))

    file_path = os.path.join(UPLOAD_FOLDER, f"{cnpj}.xlsx")
    file.save(file_path)

    usuarios = carregar_usuarios()
    for usuario in usuarios:
        if usuario["cnpj"] == cnpj:
            usuario["tabela"] = file_path

    salvar_usuarios(usuarios)
    return redirect(url_for("admin_dashboard"))


@app.route("/delete_table/<cnpj>", methods=["POST"])
def delete_table(cnpj):
    """Exclui a planilha de um CNPJ"""
    if "usuario" not in session or session["usuario"] != ADMIN_LOGIN:
        return redirect(url_for("login"))

    usuarios = carregar_usuarios()
    for usuario in usuarios:
        if usuario["cnpj"] == cnpj and usuario["tabela"]:
            os.remove(usuario["tabela"])
            usuario["tabela"] = None

    salvar_usuarios(usuarios)
    return redirect(url_for("admin_dashboard"))


@app.route("/view_table/<cnpj>", methods=["GET", "POST"])
def view_table(cnpj):
    """Exibe apenas a linha correspondente à referência pesquisada"""
    if "usuario" not in session:
        return redirect(url_for("login"))

    usuario_atual = session["usuario"]

    # Permite que apenas o ADMIN visualize todas as tabelas
    if usuario_atual != "Admin" and usuario_atual != cnpj:
        return "Acesso negado: você só pode visualizar os seus próprios processos."

    file_path = os.path.join(UPLOAD_FOLDER, f"{cnpj}.xlsx")
    if not os.path.exists(file_path):
        return "Erro: Planilha não encontrada", 404

    df = pd.read_excel(file_path, dtype=str, skiprows=6)

    df.columns = df.iloc[0]  # Usa a primeira linha após o cabeçalho real
    df = df[1:].reset_index(drop=True)  # Remove a linha extra do cabeçalho

    df = df.dropna(how="all", axis=1)
    df.columns = [str(col).strip() for col in df.columns]

    referencia_pesquisada = request.form.get("referencia", "").strip().upper() if request.method == "POST" else ""

    if referencia_pesquisada:
        df_filtrado = df[df.iloc[:, 0] == referencia_pesquisada]  # Filtra a referência na 1ª coluna
    else:
        df_filtrado = df.head(0)  # Caso nada seja pesquisado, não exibe nada

    arquivos = {}
    pasta_cnpj = os.path.join(UPLOAD_FOLDER, cnpj)

    if os.path.exists(pasta_cnpj):
        for referencia in df_filtrado.iloc[:, 0]:  # Assume que a 1ª coluna é a referência
            pasta_referencia = os.path.join(pasta_cnpj, referencia)
            if os.path.exists(pasta_referencia):
                arquivos[referencia] = {
                    "bl": os.path.exists(os.path.join(pasta_referencia, f"BL_{referencia}.pdf")),
                    "invoice": os.path.exists(os.path.join(pasta_referencia, f"Invoice_{referencia}.pdf")),
                    "packing_list": os.path.exists(os.path.join(pasta_referencia, f"PackingList_{referencia}.pdf")),
                    "li": os.path.exists(os.path.join(pasta_referencia, f"LI_{referencia}.pdf")),
                    "di": os.path.exists(os.path.join(pasta_referencia, f"DI_{referencia}.pdf")),
                }
            else:
                arquivos[referencia] = {"bl": False, "invoice": False, "packing_list": False, "li": False, "di": False}

    return render_template("view_table.html", cnpj=cnpj, headers=df_filtrado.columns, rows=df_filtrado.values if not df_filtrado.empty else None, arquivos=arquivos)


@app.route("/delete_document/<cnpj>/<referencia>/<doc_type>", methods=["POST"])
def delete_document(cnpj, referencia, doc_type):
    """Remove um documento específico anexado a uma referência"""
    pasta_referencia = os.path.join(UPLOAD_FOLDER, cnpj, referencia)
    nome_arquivo = f"{doc_type.upper()}_{referencia}.pdf"
    caminho_arquivo = os.path.join(pasta_referencia, nome_arquivo)

    if os.path.exists(caminho_arquivo):
        os.remove(caminho_arquivo)

        # Verifica se a pasta está vazia e remove a referência se não houver mais arquivos
        if not any(os.listdir(pasta_referencia)):  
            os.rmdir(pasta_referencia)  # Remove a pasta vazia

        return redirect(url_for('dashboard'))
    else:
        return "Erro: Documento não encontrado", 404


@app.route("/download_document/<cnpj>/<referencia>/<doc_type>")
def download_document(cnpj, referencia, doc_type):
    """Permite o download de um documento específico para uma referência"""
    pasta_referencia = os.path.join(UPLOAD_FOLDER, cnpj, referencia)
    nome_arquivo = f"{doc_type.upper()}_{referencia}.pdf"  # Exemplo: BL_DS24770.pdf
    caminho_arquivo = os.path.join(pasta_referencia, nome_arquivo)

    if os.path.exists(caminho_arquivo):
        return send_from_directory(pasta_referencia, nome_arquivo, as_attachment=True)
    else:
        return "Erro: Documento não encontrado", 404


@app.route("/download_table/<cnpj>")
def download_table(cnpj):
    """Permite que um usuário baixe sua própria planilha"""
    if "usuario" not in session:
        return redirect(url_for("login"))

    usuarios = carregar_usuarios()
    for usuario in usuarios:
        if usuario["cnpj"] == session["usuario"] and usuario["tabela"]:
            return send_file(usuario["tabela"], as_attachment=True)

    return "Erro: Arquivo não encontrado", 404


@app.route("/upload_file_row/<cnpj>/<referencia>", methods=["POST"])
def upload_file_row(cnpj, referencia):
    """Faz upload de arquivos PDF para uma linha específica (referência) dentro da planilha de um CNPJ."""
    if "usuario" not in session:
        return redirect(url_for("login"))

    files = {
        "bl": request.files.get("bl"),
        "invoice": request.files.get("invoice"),
        "packing_list": request.files.get("packing_list"),
        "li": request.files.get("li"),
        "di": request.files.get("di"),
    }

    pasta_referencia = os.path.join(UPLOAD_FOLDER, cnpj, referencia)
    os.makedirs(pasta_referencia, exist_ok=True)

    for key, file in files.items():
        if file and file.filename:
            file_path = os.path.join(pasta_referencia, f"{key.upper()}_{referencia}.pdf")
            file.save(file_path)

    return redirect(url_for("view_table", cnpj=cnpj))


@app.route("/search", methods=["GET", "POST"])
def search():
    """Pesquisa um processo pelo número de referência (Exemplo: DS24770)."""
    if "usuario" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        referencia = request.form["referencia"]
        usuarios = carregar_usuarios()

        # Se for admin, mostrar qualquer processo que corresponda à referência
        if session["usuario"] == ADMIN_LOGIN:
            for usuario in usuarios:
                if referencia in usuario["tabela"]:
                    return render_template("processo.html", usuario=usuario)
        
        # Se for um usuário normal, mostrar apenas seus próprios processos
        for usuario in usuarios:
            if usuario["cnpj"] == session["usuario"] and referencia in usuario["tabela"]:
                return render_template("processo.html", usuario=usuario)

        return "Processo não encontrado", 404

    return render_template("search.html")


@app.route("/upload_document/<cnpj>", methods=["POST"])
def upload_document(cnpj):
    """Recebe e salva os arquivos anexados à linha específica."""
    if "usuario" not in session:
        return redirect(url_for("login"))

    referencia = request.form.get("referencia")
    if not referencia:
        return "Erro: Referência não informada.", 400

    # Diretório para armazenar os arquivos do CNPJ e referência específica
    pasta_cnpj = os.path.join(UPLOAD_FOLDER, cnpj)
    pasta_referencia = os.path.join(pasta_cnpj, referencia)
    os.makedirs(pasta_referencia, exist_ok=True)

    arquivos_permitidos = {
        "bl": f"BL_{referencia}.pdf",
        "invoice": f"Invoice_{referencia}.pdf",
        "packing_list": f"PackingList_{referencia}.pdf",
        "li": f"LI_{referencia}.pdf",
        "di": f"DI_{referencia}.pdf",
    }

    for campo, nome_arquivo in arquivos_permitidos.items():
        if campo in request.files:
            file = request.files[campo]
            if file.filename:
                file_path = os.path.join(pasta_referencia, nome_arquivo)
                file.save(file_path)

    return redirect(url_for("view_table", cnpj=cnpj))


@app.route("/upload_docs/<cnpj>/<referencia>", methods=["POST"])
def upload_docs(cnpj, referencia):
    """Faz upload dos 5 arquivos PDF para uma linha específica dentro da planilha de um CNPJ."""
    if "usuario" not in session:
        return redirect(url_for("login"))

    # Verifica se algum arquivo foi enviado
    files = {
        "bl": request.files.get("bl"),
        "invoice": request.files.get("invoice"),
        "packing_list": request.files.get("packing_list"),
        "li": request.files.get("li"),
        "di": request.files.get("di"),
    }

    # Criar a pasta do CNPJ se não existir
    pasta_cnpj = os.path.join(UPLOAD_FOLDER, cnpj)
    os.makedirs(pasta_cnpj, exist_ok=True)

    # Criar a pasta da referência (linha específica)
    pasta_referencia = os.path.join(pasta_cnpj, referencia)
    os.makedirs(pasta_referencia, exist_ok=True)

    # Salvar os arquivos
    file_paths = {}
    for key, file in files.items():
        if file and file.filename:
            file_path = os.path.join(pasta_referencia, f"{key.upper()}_{referencia}.pdf")
            file.save(file_path)
            file_paths[key] = file_path  # Salva o caminho do arquivo para exibição posterior

    return redirect(url_for("view_table", cnpj=cnpj))


@app.route("/download_file/<referencia>/<filename>")
def download_file(referencia, filename):
    """Baixa um arquivo PDF de um processo específico."""
    if "usuario" not in session:
        return redirect(url_for("login"))

    file_path = os.path.join(UPLOAD_FOLDER, referencia, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    
    return "Erro: Arquivo não encontrado", 404


# ======================== EXECUÇÃO ========================


if __name__ == "__main__":
    app.run(debug=True)