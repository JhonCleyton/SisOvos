# 🥚 SisOvos - Sistema de Gerenciamento de Vendas de Ovos

Sistema web completo para gestão de vendas de ovos, desenvolvido com Flask, oferecendo controle total sobre estoque, vendas, clientes e equipe através de uma interface intuitiva e responsiva.

## ✨ Recursos Principais

### 📊 Dashboard Inteligente
- Visão geral em tempo real do negócio
- Gráficos interativos de desempenho
- Métricas de vendas e estoque
- Últimas transações e atividades recentes

### 📦 Gestão de Estoque Avançada
- Controle preciso de entrada e saída de produtos
- Categorização de produtos
- Alertas automáticos de estoque baixo
- Histórico completo de movimentações
- Controle de lotes e validade

### 💰 Módulo de Vendas Completo
- Registro rápido de vendas
- Diferentes formas de pagamento
- Emissão de comprovantes
- Cancelamento e estorno de vendas
- Histórico detalhado

### 👥 Gestão de Clientes
- Cadastro completo de clientes
- Histórico de compras
- Análise de perfil de consumo
- Controle de contatos e endereços

### 📦 Controle de Expedição
- Gerenciamento de pedidos
- Acompanhamento de status
- Rastreamento de entregas
- Relatórios de logística

### 👥 Gestão de Usuários
- Múltiplos níveis de acesso
- Controle de permissões granular
- Auditoria de atividades
- Gerenciamento de senhas

### 📈 Relatórios Poderosos
- Financeiros detalhados
- Análise de vendas
- Controle de estoque
- Desempenho por período
- Exportação para múltiplos formatos

## 🛠️ Tecnologias Utilizadas

- **Backend**: Python com Flask
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Banco de Dados**: SQLite (desenvolvimento) / PostgreSQL (produção)
- **Outras Bibliotecas**: SQLAlchemy, WTForms, Chart.js

## 📝 Pré-requisitos

- Python 3.8+
- pip (gerenciador de pacotes do Python)
- Virtualenv (recomendado)
- Git (opcional)

## 🚀 Instalação

1. **Clonar o repositório**
   ```bash
   git clone https://github.com/JhonCleyton/SisOvos.git
   cd SisOvos
   ```

2. **Criar e ativar ambiente virtual**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate
   
   # Linux/MacOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Instalar dependências**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variáveis de ambiente**
   Crie um arquivo `.env` na raiz do projeto com as configurações necessárias:
   ```
   FLASK_APP=run.py
   FLASK_ENV=development
   SECRET_KEY=sua_chave_secreta_aqui
   DATABASE_URL=sqlite:///sisovos.db
   ```

5. **Iniciar o aplicativo**
   ```bash
   flask run
   ```

6. **Acessar o sistema**
   Abra o navegador e acesse: http://localhost:5000

## 📄 Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## ✉️ Suporte

Em caso de dúvidas ou sugestões, entre em contato:

- **Desenvolvedor**: Jhon Cleyton
- **Empresa**: JC Byte - Soluções em Tecnologia
- **E-mail**: [tecnologiajvbyte@gmail.com](mailto:tecnologiajvbyte@gmail.com)
- **WhatsApp**: [(73) 99854-7885](https://wa.me/5573998547885)
- **LinkedIn**: [jhon-freire](https://linkedin.com/in/jhon-freire)
- **GitHub**: [JhonCleyton](https://github.com/JhonCleyton)

## 🤝 Contribuições

Contribuições são sempre bem-vindas! Sinta-se à vontade para abrir issues e enviar pull requests.

## 📊 Status do Projeto

🚧 Em desenvolvimento ativo - Novos recursos e melhorias sendo implementados regularmente.

## Instalação

1. Clone o repositório:
   ```
   git clone [URL_DO_REPOSITORIO]
   cd SisOvos
   ```

2. Crie um ambiente virtual (recomendado):
   ```
   python -m venv venv
   venv\Scripts\activate  # No Windows
   ```

3. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```

4. Inicialize o banco de dados:
   ```
   python init_db.py
   ```

5. Execute o aplicativo:
   ```
   python app.py
   ```

6. Acesse no navegador:
   ```
   http://localhost:5000
   ```

## Login Inicial

- **Email:** admin@sisovos.com
- **Senha:** admin123

## Tecnologias Utilizadas

- Python 3.8+
- Flask
- SQLAlchemy
- SQLite
- Bootstrap 5
- JavaScript (jQuery)

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.
