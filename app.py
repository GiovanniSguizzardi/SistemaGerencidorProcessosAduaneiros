from flask import Flask, render_template, request, redirect, url_for, session, send_file
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
    """Painel individual para cada usuário (somente pode visualizar sua planilha)"""
    if "usuario" not in session:
        return redirect(url_for("login"))

    cnpj_usuario = session["usuario"]

    if cnpj_usuario == ADMIN_LOGIN:
        return redirect(url_for("admin_dashboard"))

    usuarios = carregar_usuarios()
    for usuario in usuarios:
        if usuario["cnpj"] == cnpj_usuario:
            return render_template("dashboard.html", usuario=usuario)

    return "Erro: Usuário não encontrado.", 404


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


@app.route("/view_table/<cnpj>")
def view_table(cnpj):
    if "usuario" not in session:
        return redirect(url_for("login"))

    usuarios = carregar_usuarios()
    for usuario in usuarios:
        if usuario["cnpj"] == cnpj and usuario["tabela"]:
            df = pd.read_excel(usuario["tabela"], skiprows=7)
            return render_template("view_table.html", cnpj=cnpj, headers=df.columns, rows=df.values)

    return "Erro: Planilha não encontrada", 404


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


# ======================== EXECUÇÃO ========================
if __name__ == "__main__":
    app.run(debug=True)