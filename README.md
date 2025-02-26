> [!NOTE]
> Ao baixar o projeto, se não existente, criar um pasta chamada "uploads"
>

# **📌 Sistema de Gerenciamento de Processos Aduaneiros**

Um sistema web desenvolvido em **Flask** para gerenciar processos de importação/exportação, permitindo o upload, consulta e gerenciamento de planilhas e documentos anexados por CNPJ.

---

## **📢 Funcionalidades**
✅ **Login Seguro** – Acesso para administradores e clientes via CNPJ e senha.  
✅ **Painel do Administrador** – Gerenciar empresas, anexar/excluir planilhas e visualizar todas as informações.  
✅ **Painel do Cliente** – Acesso restrito apenas às informações do próprio CNPJ.  
✅ **Upload & Download** – Anexação e download de documentos como **BL, Invoice, Packing List, LI e DI**.  
✅ **Pesquisa de Referências** – Localizar processos específicos por **número de referência**.  
✅ **Gerenciamento de Arquivos** – Remover documentos anexados, mantendo o sistema organizado.  
✅ **Interface Responsiva** – Layout otimizado para **computadores e dispositivos móveis**.  

---

## **🛠️ Tecnologias Utilizadas**
- **Python (Flask)** – Framework web principal  
- **Pandas** – Manipulação de dados das planilhas Excel  
- **Jinja2** – Template Engine para renderização dinâmica  
- **Bootstrap & CSS** – Interface responsiva e estilizada  
- **SQLite / CSV** – Armazenamento dos usuários e credenciais  

---

## **🚀 Instalação e Execução**
### **1️⃣ Clone o Repositório**
```bash
git clone https://github.com/seu-usuario/seu-repositorio.git
cd seu-repositorio
```

### **2️⃣ Criação de um Virtual Environment (Recomendado)**
```bash
python -m venv venv
source venv/bin/activate  # No Windows use: venv\Scripts\activate
```

### **3️⃣ Instale as Dependências**
```bash
pip install -r requirements.txt
```

### **4️⃣ Execute a Aplicação**
```bash
python app.py
```
Agora, acesse **http://127.0.0.1:5000/** no navegador. 🚀

---

## **👤 Acesso ao Sistema**
- **Administrador**  
  - **Usuário:** `Admin`  
  - **Senha:** `SenhaForte!@#2024`  
- **Clientes**  
  - Criados pelo administrador no painel, com CNPJ e senha gerada automaticamente.

---

## **📂 Estrutura do Projeto**
```
/seu-projeto
│── /static             # Arquivos CSS e JS
│── /templates          # Arquivos HTML (Views)
│── /uploads            # Diretório para armazenar planilhas e documentos anexados
│── app.py              # Código principal da aplicação
│── requirements.txt    # Dependências do projeto
│── README.md           # Este arquivo!
│── usuarios.csv        # Armazena os dados dos usuários e CNPJs cadastrados
```

---

## **📝 Como Contribuir**
Contribuições são sempre bem-vindas! Siga os passos abaixo para colaborar:
1. **Faça um Fork** do repositório.
2. **Crie um branch** com a feature desejada:
   ```bash
   git checkout -b minha-feature
   ```
3. **Realize as alterações** e **faça commit**:
   ```bash
   git commit -m "Minha nova funcionalidade"
   ```
4. **Envie para o repositório remoto**:
   ```bash
   git push origin minha-feature
   ```
5. **Abra um Pull Request** e aguarde a revisão. 🎉

---

## **📌 Possiveis Melhorias Futuras**
🚀 **Dashboard interativo com gráficos**  
🔍 **Filtro avançado para referências**  
📧 **Notificações por e-mail para novos processos**  
📊 **Relatórios gerenciais automáticos**  

---

## **📜 Licença**
Este projeto é propriedade exclusiva do autor e não pode ser modificado, distribuído ou utilizado para fins comerciais sem permissão explícita.
Todos os direitos são reservados. Para solicitar permissões, entre em contato com giovanni.sguiconde@gmail.com

📌 Licença: All Rights Reserved © 2025 Giovanni Sguizzardi Conde
