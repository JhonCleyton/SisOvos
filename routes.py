from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, timedelta

from models import db, Usuario, Cliente, Produto, Venda, ItemVenda, EstoqueDiario
from forms import LoginForm, ProdutoForm, VendaForm, UsuarioForm, BuscarUsuarioForm

bp = Blueprint('main', __name__)

# Decorator para verificar permissões
def permissao_necessaria(funcao_requerida):
    def decorator(f):
        @wraps(f)
        def funcao_decorada(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('main.login', next=request.url))
            if not current_user.tem_permissao(funcao_requerida):
                flash('Você não tem permissão para acessar esta página.', 'danger')
                return redirect(url_for('main.dashboard'))
            return f(*args, **kwargs)
        return funcao_decorada
    return decorator

# Rotas de Autenticação
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    form = LoginForm()
    
    if form.validate_on_submit():
        # Verifica se é email ou username
        user = Usuario.query.filter(
            (Usuario.email == form.username.data) | (Usuario.username == form.username.data)
        ).first()
        
        if user and check_password_hash(user.senha, form.password.data):
            if not user.ativo:
                flash('Este usuário está desativado. Entre em contato com o administrador.', 'warning')
                return redirect(url_for('main.login'))
                
            login_user(user, remember=True)
            next_page = request.args.get('next')
            flash(f'Bem-vindo(a) de volta, {user.nome}!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
        else:
            flash('Login ou senha inválidos', 'danger')
    
    return render_template('login.html', form=form)

@bp.route('/logout')
@login_required
def logout():
    user_name = current_user.nome
    logout_user()
    flash(f'Até mais, {user_name}! Você saiu do sistema.', 'info')
    return redirect(url_for('main.login'))

# Rotas Principais
@bp.route('/')
@bp.route('/dashboard')
@login_required
def dashboard():
    # Obtém o produto (ovos)
    produto = Produto.query.first()
    if not produto:
        produto = Produto(
            codigo='OVO001',
            nome='Ovos', 
            preco_compra=10.0,
            preco_venda=15.0, 
            estoque_atual=0,
            estoque_minimo=0,
            unidade_medida='dz',
            ativo=True
        )
        db.session.add(produto)
        db.session.commit()
    
    # Obtém a data de hoje
    hoje = datetime.utcnow().date()
    
    # Obtém o registro de estoque de hoje
    estoque_hoje = EstoqueDiario.query.filter_by(data=hoje).first()
    
    # Se não existe registro para hoje, cria um com base no estoque do produto
    if not estoque_hoje:
        # Calcula o valor total do estoque (quantidade * preço de compra)
        valor_estoque = produto.estoque_atual * produto.preco_compra
        
        # Cria o registro de estoque para hoje
        estoque_hoje = EstoqueDiario(
            data=hoje,
            produto_id=produto.id,
            quantidade=produto.estoque_atual,
            valor_estoque=valor_estoque
        )
        db.session.add(estoque_hoje)
        db.session.commit()
    
    # Calcula as estatísticas de vendas do mês
    primeiro_dia_mes = hoje.replace(day=1)
    
    # Verifica se estamos em dezembro para ajustar o mês seguinte
    if primeiro_dia_mes.month == 12:
        primeiro_dia_prox_mes = primeiro_dia_mes.replace(year=primeiro_dia_mes.year + 1, month=1, day=1)
    else:
        primeiro_dia_prox_mes = primeiro_dia_mes.replace(month=primeiro_dia_mes.month + 1, day=1)
    
    vendas_mes = Venda.query.filter(
        Venda.data_venda >= primeiro_dia_mes,
        Venda.data_venda < primeiro_dia_prox_mes
    ).all()
    
    total_vendas_mes = sum(v.valor_total for v in vendas_mes)
    total_duzias_mes = sum(
        sum(item.quantidade for item in v.itens) 
        for v in vendas_mes
    )
    
    # Calcula as estatísticas de vendas de hoje
    vendas_hoje = Venda.query.filter(
        db.func.date(Venda.data_venda) == hoje
    ).all()
    
    total_vendas_hoje = sum(v.valor_total for v in vendas_hoje)
    total_duzias_hoje = sum(
        sum(item.quantidade for item in v.itens) 
        for v in vendas_hoje
    )
    
    # Últimas vendas
    ultimas_vendas = Venda.query.order_by(Venda.data_venda.desc()).limit(5).all()
    
    # Prepara os dados para o gráfico de vendas dos últimos 7 dias
    data_atual = hoje
    dados_grafico = []
    
    for i in range(6, -1, -1):
        data = data_atual - timedelta(days=i)
        vendas_dia = Venda.query.filter(db.func.date(Venda.data_venda) == data).all()
        total_dia = sum(v.valor_total for v in vendas_dia)
        
        dados_grafico.append({
            'data': data.strftime('%d/%m'),
            'total': float(total_dia)
        })
    
    return render_template('dashboard.html',
                         produto=produto,
                         estoque_hoje=estoque_hoje,
                         total_vendas_mes=total_vendas_mes,
                         total_duzias_mes=total_duzias_mes,
                         total_vendas_hoje=total_vendas_hoje,
                         total_duzias_hoje=total_duzias_hoje,
                         ultimas_vendas=ultimas_vendas,
                         dados_grafico=dados_grafico,
                         hoje=hoje.strftime('%d/%m/%Y'))

# Rotas de Gerenciamento de Usuários
@bp.route('/usuarios')
@login_required
@permissao_necessaria('ADMIN')
def listar_usuarios():
    """Lista todos os usuários com paginação e filtros"""
    page = request.args.get('page', 1, type=int)
    busca = request.args.get('busca', '').strip()
    funcao = request.args.get('funcao', '')
    status = request.args.get('status', '')
    
    query = Usuario.query
    
    # Aplicar filtros
    if busca:
        busca = f"%{busca}%"
        query = query.filter(
            (Usuario.nome.ilike(busca)) | 
            (Usuario.username.ilike(busca)) | 
            (Usuario.email.ilike(busca))
        )
    
    if funcao:
        query = query.filter(Usuario.funcao == funcao)
    
    if status == 'ativo':
        query = query.filter(Usuario.ativo == True)
    elif status == 'inativo':
        query = query.filter(Usuario.ativo == False)
    
    # Ordenar por nome
    query = query.order_by(Usuario.nome)
    
    # Paginação
    per_page = 10
    usuarios = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Formulário de busca
    form = BuscarUsuarioForm()
    form.funcao.choices = [('', 'Todas as funções')] + Usuario.FUNCOES
    form.funcao.data = funcao
    form.status.data = status
    form.busca.data = request.args.get('busca', '')
    
    return render_template('usuarios/listar.html', usuarios=usuarios, form=form)

@bp.route('/usuarios/novo', methods=['GET', 'POST'])
@login_required
@permissao_necessaria('ADMIN')
def novo_usuario():
    """Cria um novo usuário"""
    form = UsuarioForm()
    form.funcao.choices = Usuario.FUNCOES
    form.id.data = 0  # Define um valor padrão para o ID em novos usuários
    
    if form.validate_on_submit():
        try:
            usuario = Usuario(
                nome=form.nome.data,
                username=form.username.data,
                email=form.email.data,
                senha=generate_password_hash(form.senha.data, method='sha256'),
                funcao=form.funcao.data,
                ativo=form.ativo.data
            )
            
            db.session.add(usuario)
            db.session.commit()
            
            flash(f'Usuário {usuario.nome} criado com sucesso!', 'success')
            return redirect(url_for('main.listar_usuarios'))
            
        except Exception as e:
            db.session.rollback()
            flash('Erro ao criar usuário. Por favor, tente novamente.', 'danger')
            app.logger.error(f'Erro ao criar usuário: {str(e)}')
    
    return render_template('usuarios/form.html', form=form)

@bp.route('/usuarios/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@permissao_necessaria('ADMIN')
def editar_usuario(id):
    """Edita um usuário existente"""
    usuario = Usuario.query.get_or_404(id)
    form = UsuarioForm(obj=usuario)
    form.funcao.choices = Usuario.FUNCOES
    
    # Armazena o ID para validação
    form.id = id
    
    if form.validate_on_submit():
        try:
            usuario.nome = form.nome.data
            usuario.username = form.username.data
            usuario.email = form.email.data
            usuario.funcao = form.funcao.data
            usuario.ativo = form.ativo.data
            
            # Atualiza a senha apenas se for informada
            if form.senha.data:
                usuario.senha = generate_password_hash(form.senha.data, method='sha256')
            
            db.session.commit()
            
            flash('Usuário atualizado com sucesso!', 'success')
            return redirect(url_for('main.listar_usuarios'))
            
        except Exception as e:
            db.session.rollback()
            flash('Erro ao atualizar usuário. Por favor, tente novamente.', 'danger')
            app.logger.error(f'Erro ao atualizar usuário: {str(e)}')
    
    return render_template('usuarios/form.html', form=form, usuario=usuario)

@bp.route('/usuarios/alterar-status/<int:id>', methods=['POST'])
@login_required
@permissao_necessaria('ADMIN')
def alterar_status_usuario(id):
    """Ativa/desativa um usuário"""
    if current_user.id == id:
        flash('Você não pode alterar seu próprio status.', 'warning')
        return redirect(url_for('main.listar_usuarios'))
    
    usuario = Usuario.query.get_or_404(id)
    
    try:
        usuario.ativo = not usuario.ativo
        status = 'ativado' if usuario.ativo else 'desativado'
        
        db.session.commit()
        flash(f'Usuário {status} com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Erro ao alterar status do usuário.', 'danger')
        app.logger.error(f'Erro ao alterar status do usuário: {str(e)}')
    
    return redirect(url_for('main.listar_usuarios'))

@bp.route('/usuario/<int:id>/excluir', methods=['POST'])
@login_required
@permissao_necessaria('ADMIN')
def excluir_usuario(id):
    """Exclui um usuário"""
    if current_user.id == id:
        flash('Você não pode excluir seu próprio usuário.', 'danger')
        return redirect(url_for('main.listar_usuarios'))
    
    usuario = Usuario.query.get_or_404(id)
    
    try:
        db.session.delete(usuario)
        db.session.commit()
        flash('Usuário excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Erro ao excluir usuário. Tente novamente.', 'danger')
    
    return redirect(url_for('main.listar_usuarios'))

# Rotas de Gerenciamento de Produtos
@bp.route('/produtos')
@login_required
def listar_produtos():
    """Lista todos os produtos com paginação e filtros"""
    pagina = request.args.get('pagina', 1, type=int)
    busca = request.args.get('busca', '')
    ativo = request.args.get('ativo', 'todos')
    
    query = Produto.query
    
    # Aplica filtros
    if busca:
        query = query.filter(
            (Produto.nome.ilike(f'%{busca}%')) | 
            (Produto.codigo.ilike(f'%{busca}%')) |
            (Produto.descricao.ilike(f'%{busca}%'))
        )
    
    if ativo == 'ativo':
        query = query.filter_by(ativo=True)
    elif ativo == 'inativo':
        query = query.filter_by(ativo=False)
    
    # Ordena por nome
    produtos = query.order_by(Produto.nome.asc()).paginate(page=pagina, per_page=10)
    
    return render_template('produtos/listar.html', 
                         produtos=produtos, 
                         busca=busca,
                         ativo=ativo)

@bp.route('/produto/novo', methods=['GET', 'POST'])
@login_required
def novo_produto():
    """Cria um novo produto"""
    form = ProdutoForm()
    
    if form.validate_on_submit():
        try:
            produto = Produto(
                codigo=form.codigo.data,
                nome=form.nome.data,
                descricao=form.descricao.data,
                preco_compra=form.preco_compra.data,
                preco_venda=form.preco_venda.data,
                estoque_atual=form.estoque_atual.data,
                estoque_minimo=form.estoque_minimo.data or 0,
                unidade_medida=form.unidade_medida.data,
                ativo=True
            )
            
            db.session.add(produto)
            db.session.commit()
            
            flash('Produto cadastrado com sucesso!', 'success')
            return redirect(url_for('main.listar_produtos'))
            
        except Exception as e:
            db.session.rollback()
            flash('Erro ao cadastrar produto. Por favor, tente novamente.', 'danger')
    
    return render_template('produtos/form.html', form=form, titulo='Novo Produto')

@bp.route('/produto/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_produto(id):
    """Edita um produto existente"""
    produto = Produto.query.get_or_404(id)
    form = ProdutoForm(obj=produto)
    
    if form.validate_on_submit():
        try:
            produto.codigo = form.codigo.data
            produto.nome = form.nome.data
            produto.descricao = form.descricao.data
            produto.preco_compra = form.preco_compra.data
            produto.preco_venda = form.preco_venda.data
            produto.estoque_atual = form.estoque_atual.data
            produto.estoque_minimo = form.estoque_minimo.data or 0
            produto.unidade_medida = form.unidade_medida.data
            
            db.session.commit()
            
            flash('Produto atualizado com sucesso!', 'success')
            return redirect(url_for('main.listar_produtos'))
            
        except Exception as e:
            db.session.rollback()
            flash('Erro ao atualizar produto. Por favor, tente novamente.', 'danger')
    
    return render_template('produtos/form.html', form=form, titulo='Editar Produto', produto=produto)

@bp.route('/produto/<int:id>/excluir', methods=['POST'])
@login_required
def excluir_produto(id):
    """Exclui um produto"""
    produto = Produto.query.get_or_404(id)
    
    try:
        # Verifica se o produto está vinculado a alguma venda
        if ItemVenda.query.filter_by(produto_id=produto.id).first():
            flash('Não é possível excluir este produto pois ele está vinculado a uma ou mais vendas.', 'warning')
            return redirect(url_for('main.listar_produtos'))
        
        db.session.delete(produto)
        db.session.commit()
        flash('Produto excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Erro ao excluir produto. Tente novamente.', 'danger')
    
    return redirect(url_for('main.listar_produtos'))

@bp.route('/produto/<int:id>')
@login_required
def visualizar_produto(id):
    """Visualiza os detalhes de um produto"""
    produto = Produto.query.get_or_404(id)
    return render_template('produtos/visualizar.html', produto=produto)

# Rotas de Gerenciamento de Vendas
@bp.route('/vendas')
@login_required
def listar_vendas():
    """Lista todas as vendas com paginação e filtros"""
    pagina = request.args.get('pagina', 1, type=int)
    busca = request.args.get('busca', '')
    status = request.args.get('status', 'todas')
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    
    query = Venda.query
    
    # Aplica filtros
    if busca:
        query = query.join(Cliente).filter(
            (Cliente.nome.ilike(f'%{busca}%')) | 
            (Venda.observacoes.ilike(f'%{busca}%')) |
            (Venda.id == busca) if busca.isdigit() else False
        )
    
    if status == 'pendente':
        query = query.filter_by(status='pendente')
    elif status == 'finalizada':
        query = query.filter_by(status='finalizada')
    elif status == 'cancelada':
        query = query.filter_by(status='cancelada')
    
    if data_inicio:
        try:
            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
            query = query.filter(Venda.data_venda >= data_inicio)
        except ValueError:
            pass
    
    if data_fim:
        try:
            data_fim = datetime.strptime(data_fim, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(Venda.data_venda <= data_fim)
        except ValueError:
            pass
    
    # Ordena por data de venda mais recente
    vendas = query.order_by(Venda.data_venda.desc()).paginate(page=pagina, per_page=15)
    
    return render_template('vendas/listar.html', 
                         vendas=vendas, 
                         busca=busca,
                         status=status,
                         data_inicio=data_inicio,
                         data_fim=data_fim)

@bp.route('/vendas/nova', methods=['GET', 'POST'])
@login_required
def nova_venda():
    """Cria uma nova venda"""
    form = VendaForm()
    
    # Carrega clientes ativos
    form.cliente_id.choices = [(c.id, c.nome) for c in Cliente.query.filter_by(ativo=True).order_by('nome').all()]
    
    # Carrega produtos ativos
    produtos_disponiveis = Produto.query.filter_by(ativo=True).order_by('nome').all()
    
    if form.validate_on_submit():
        try:
            # Cria a venda
            venda = Venda(
                cliente_id=form.cliente_id.data,
                usuario_id=current_user.id,
                forma_pagamento=form.forma_pagamento.data,
                status='pendente',
                observacoes=form.observacoes.data or None,
                data_venda=datetime.now()
            )
            
            db.session.add(venda)
            db.session.flush()  # Obtém o ID da venda
            
            # Adiciona os itens da venda
            for item in form.itens.data:
                produto = Produto.query.get(item['produto_id'])
                if not produto or not produto.ativo:
                    continue
                    
                quantidade = float(item['quantidade'] or 0)
                if quantidade <= 0:
                    continue
                
                # Atualiza o estoque
                if produto.estoque_atual < quantidade:
                    flash(f'Estoque insuficiente para o produto {produto.nome}.', 'warning')
                    db.session.rollback()
                    return redirect(url_for('main.nova_venda'))
                
                produto.estoque_atual -= quantidade
                
                # Cria o item da venda
                item_venda = ItemVenda(
                    venda_id=venda.id,
                    produto_id=produto.id,
                    quantidade=quantidade,
                    preco_unitario=produto.preco_venda,
                    desconto=float(item.get('desconto', 0) or 0)
                )
                
                db.session.add(item_venda)
            
            # Verifica se há itens na venda
            if not venda.itens:
                flash('Adicione pelo menos um item à venda.', 'warning')
                db.session.rollback()
                return redirect(url_for('main.nova_venda'))
            
            # Atualiza totais
            venda.calcular_totais()
            
            # Se o pagamento for à vista, atualiza o status
            if form.forma_pagamento in ['dinheiro', 'pix', 'cartao_credito', 'cartao_debito', 'transferencia']:
                venda.status = 'finalizada'
            
            db.session.commit()
            
            flash('Venda registrada com sucesso!', 'success')
            return redirect(url_for('main.visualizar_venda', id=venda.id))
            
        except Exception as e:
            db.session.rollback()
            flash('Erro ao registrar venda. Por favor, tente novamente.', 'danger')
    
    return render_template('vendas/form.html', 
                         form=form, 
                         produtos_disponiveis=produtos_disponiveis,
                         titulo='Nova Venda')

@bp.route('/vendas/<int:id>')
@login_required
def visualizar_venda(id):
    """Visualiza os detalhes de uma venda"""
    venda = Venda.query.get_or_404(id)
    return render_template('vendas/visualizar.html', venda=venda)

@bp.route('/vendas/<int:id>/cancelar', methods=['POST'])
@login_required
def cancelar_venda(id):
    """Cancela uma venda"""
    venda = Venda.query.get_or_404(id)
    
    if venda.status == 'cancelada':
        flash('Esta venda já está cancelada.', 'warning')
        return redirect(url_for('main.visualizar_venda', id=venda.id))
    
    if venda.status == 'finalizada':
        # Estorna os itens para o estoque
        for item in venda.itens:
            produto = item.produto
            produto.estoque_atual += item.quantidade
    
    try:
        venda.status = 'cancelada'
        venda.data_cancelamento = datetime.now()
        db.session.commit()
        
        flash('Venda cancelada com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Erro ao cancelar venda. Por favor, tente novamente.', 'danger')
    
    return redirect(url_for('main.visualizar_venda', id=venda.id))

@bp.route('/financeiro')
@login_required
@permissao_necessaria('FINANCEIRO')
def financeiro():
    """Página principal do módulo financeiro"""
    # Filtros
    status = request.args.get('status', 'pendentes')
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    cliente_id = request.args.get('cliente_id', type=int)
    
    # Consulta base
    query = Venda.query.filter(Venda.status.in_(['pendente', 'pago']))
    
    # Aplicar filtros
    if status == 'pendentes':
        query = query.filter_by(status='pendente')
    elif status == 'pagos':
        query = query.filter_by(status='pago')
    
    if data_inicio:
        try:
            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
            query = query.filter(Venda.data_venda >= data_inicio)
        except ValueError:
            pass
    
    if data_fim:
        try:
            data_fim = datetime.strptime(data_fim, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(Venda.data_venda <= data_fim)
        except ValueError:
            pass
    
    if cliente_id:
        query = query.filter_by(cliente_id=cliente_id)
    
    # Ordena por data de venda mais antiga primeiro (mais antigas primeiro)
    vendas = query.order_by(Venda.data_venda.asc()).all()
    
    # Calcula totais
    total_pendente = sum(v.valor_total for v in vendas if v.status == 'pendente')
    total_recebido = sum(v.valor_total for v in vendas if v.status == 'pago')
    
    # Lista de clientes para o filtro
    clientes = Cliente.query.order_by(Cliente.nome).all()
    
    return render_template('financeiro/index.html',
                         vendas=vendas,
                         status=status,
                         data_inicio=data_inicio,
                         data_fim=data_fim,
                         cliente_id=cliente_id,
                         clientes=clientes,
                         total_pendente=total_pendente,
                         total_recebido=total_recebido)

@bp.route('/financeiro/venda/<int:id>/confirmar-pagamento', methods=['POST'])
@login_required
@permissao_necessaria('FINANCEIRO')
def confirmar_pagamento(id):
    """Confirma o recebimento de pagamento de uma venda"""
    venda = Venda.query.get_or_404(id)
    
    if venda.status == 'cancelada':
        flash('Não é possível confirmar pagamento de uma venda cancelada.', 'danger')
        return redirect(url_for('main.financeiro'))
    
    if venda.status == 'pago':
        flash('Esta venda já foi marcada como paga.', 'info')
        return redirect(url_for('main.financeiro'))
    
    try:
        venda.status = 'pago'
        venda.data_pagamento = datetime.now()
        db.session.commit()
        
        flash('Pagamento confirmado com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Erro ao confirmar pagamento. Por favor, tente novamente.', 'danger')
    
    return redirect(url_for('main.financeiro'))

# Rotas de Gerenciamento de Clientes
@bp.route('/clientes')
@login_required
def listar_clientes():
    """Lista todos os clientes com paginação e filtros"""
    pagina = request.args.get('pagina', 1, type=int)
    busca = request.args.get('busca', '')
    ativo = request.args.get('ativo', 'todos')
    
    query = Cliente.query
    
    # Aplica filtros
    if busca:
        query = query.filter(
            (Cliente.nome.ilike(f'%{busca}%')) | 
            (Cliente.email.ilike(f'%{busca}%')) |
            (Cliente.telefone.ilike(f'%{busca}%')) |
            (Cliente.cpf_cnpj.ilike(f'%{busca}%'))
        )
    
    if ativo == 'ativo':
        query = query.filter_by(ativo=True)
    elif ativo == 'inativo':
        query = query.filter_by(ativo=False)
    
    # Ordena por nome
    clientes = query.order_by(Cliente.nome.asc()).paginate(page=pagina, per_page=15)
    
    return render_template('clientes/listar.html', 
                         clientes=clientes, 
                         busca=busca,
                         ativo=ativo)

@bp.route('/clientes/novo', methods=['GET', 'POST'])
@login_required
def novo_cliente():
    """Cria um novo cliente"""
    form = ClienteForm()
    
    if form.validate_on_submit():
        try:
            cliente = Cliente(
                nome=form.nome.data,
                email=form.email.data,
                telefone=form.telefone.data,
                cpf_cnpj=form.cpf_cnpj.data or None,
                endereco=form.endereco.data or None,
                bairro=form.bairro.data or None,
                cidade=form.cidade.data or None,
                estado=form.estado.data or None,
                cep=form.cep.data or None,
                observacoes=form.observacoes.data or None,
                ativo=True
            )
            
            db.session.add(cliente)
            db.session.commit()
            
            flash('Cliente cadastrado com sucesso!', 'success')
            return redirect(url_for('main.visualizar_cliente', id=cliente.id))
            
        except Exception as e:
            db.session.rollback()
            flash('Erro ao cadastrar cliente. Por favor, tente novamente.', 'danger')
    
    return render_template('clientes/form.html', form=form, titulo='Novo Cliente')

@bp.route('/clientes/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_cliente(id):
    """Edita um cliente existente"""
    cliente = Cliente.query.get_or_404(id)
    form = ClienteForm(obj=cliente)
    
    if form.validate_on_submit():
        try:
            cliente.nome = form.nome.data
            cliente.email = form.email.data
            cliente.telefone = form.telefone.data
            cliente.cpf_cnpj = form.cpf_cnpj.data or None
            cliente.endereco = form.endereco.data or None
            cliente.bairro = form.bairro.data or None
            cliente.cidade = form.cidade.data or None
            cliente.estado = form.estado.data or None
            cliente.cep = form.cep.data or None
            cliente.observacoes = form.observacoes.data or None
            
            db.session.commit()
            
            flash('Cliente atualizado com sucesso!', 'success')
            return redirect(url_for('main.visualizar_cliente', id=cliente.id))
            
        except Exception as e:
            db.session.rollback()
            flash('Erro ao atualizar cliente. Por favor, tente novamente.', 'danger')
    
    return render_template('clientes/form.html', form=form, titulo='Editar Cliente', cliente=cliente)

@bp.route('/clientes/<int:id>/excluir', methods=['POST'])
@login_required
def excluir_cliente(id):
    """Exclui um cliente"""
    cliente = Cliente.query.get_or_404(id)
    
    try:
        # Verifica se o cliente está vinculado a alguma venda
        if Venda.query.filter_by(cliente_id=cliente.id).first():
            flash('Não é possível excluir este cliente pois ele está vinculado a uma ou mais vendas.', 'warning')
            return redirect(url_for('main.visualizar_cliente', id=cliente.id))
        
        db.session.delete(cliente)
        db.session.commit()
        
        flash('Cliente excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Erro ao excluir cliente. Por favor, tente novamente.', 'danger')
    
    return redirect(url_for('main.listar_clientes'))

@bp.route('/clientes/<int:id>')
@login_required
def visualizar_cliente(id):
    """Visualiza os detalhes de um cliente"""
    cliente = Cliente.query.get_or_404(id)
    
    # Busca as últimas compras do cliente
    vendas = Venda.query.filter_by(cliente_id=id)\
                        .order_by(Venda.data_venda.desc())\
                        .limit(10)\
                        .all()
    
    return render_template('clientes/visualizar.html', cliente=cliente, vendas=vendas)
