import uuid
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session, send_file, abort, current_app
from flask_login import login_required, current_user, login_user, logout_user
from utils.auth_utils import get_password_hash
from functools import wraps
from datetime import datetime, timedelta
from extensions import csrf

from models import db, Usuario, Cliente, Produto, Venda, ItemVenda, EstoqueDiario, HistoricoVenda
from forms import (LoginForm, ProdutoForm, VendaForm, UsuarioForm, 
                  BuscarUsuarioForm, ClienteForm, EstoqueDiarioForm, PerfilUsuarioForm,
                  ItemVendaForm)
from decorators import permissao_necessaria, admin_required, producao_required, faturamento_required, financeiro_required, logistica_required
from permissions import has_permission

bp = Blueprint('main', __name__)

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
        
        if user:
            # Log para depuração
            print(f"[DEBUG] Usuário encontrado: {user.username}")
            print(f"[DEBUG] Hash da senha no banco: {user.senha}")
            print(f"[DEBUG] Senha fornecida: {form.password.data}")
            
            # Verifica se o usuário está ativo
            if not user.ativo:
                flash('Este usuário está desativado. Entre em contato com o administrador.', 'warning')
                return redirect(url_for('main.login'))
            
            # Verifica se a senha está correta usando o utilitário de autenticação
            from utils.auth_utils import check_password
            senha_correta = check_password(user.senha, form.password.data)
            print(f"[DEBUG] Senha correta? {senha_correta}")
            
            if senha_correta:
                # Autenticação bem-sucedida
                login_user(user, remember=True)
                next_page = request.args.get('next')
                flash(f'Bem-vindo(a) de volta, {user.nome}!', 'success')
                return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
            else:
                # Log para depuração
                print(f"[DEBUG] Verificação de senha falhou para o usuário: {user.username}")
                print(f"[DEBUG] Tipo do hash: {type(user.senha)}")
                print(f"[DEBUG] Tipo da senha fornecida: {type(form.password.data)}")
                
                # Tenta verificar a senha manualmente para depuração
                from utils.auth_utils import get_password_hash
                print(f"[DEBUG] Hash gerado agora: {get_password_hash(form.password.data)}")
        else:
            print(f"[DEBUG] Usuário não encontrado: {form.username.data}")
            
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
    # Verifica se o usuário tem permissão para acessar o dashboard
    if not has_permission(current_user, 'main.dashboard'):
        abort(403)
        
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
            unidade_medida='cx',
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
            valor_estoque=valor_estoque,
            entrada=0,
            saida=0,
            estoque_inicial=produto.estoque_atual,
            estoque_final=produto.estoque_atual,
            usuario_id=current_user.id
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
@admin_required
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
                telefone=form.telefone.data if hasattr(form, 'telefone') else '',
                senha=get_password_hash(form.senha.data),
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
            current_app.logger.error(f'Erro ao criar usuário: {str(e)}')
    
    return render_template('usuarios/form.html', form=form)

@bp.route('/usuarios/alterar-status/<int:id>', methods=['POST'])
@login_required
@permissao_necessaria('ADMIN')
def alterar_status_usuario(id):
    """Altera o status de ativação de um usuário"""
    if not has_permission(current_user, 'main.alterar_status_usuario'):
        return jsonify({'success': False, 'message': 'Você não tem permissão para realizar esta ação.'}), 403
    
    usuario = Usuario.query.get_or_404(id)
    
    # Impede que o usuário desative a si mesmo
    if usuario.id == current_user.id:
        return jsonify({'success': False, 'message': 'Você não pode alterar seu próprio status.'}), 400
    
    try:
        usuario.ativo = not usuario.ativo
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Status do usuário atualizado com sucesso!',
            'novo_status': usuario.ativo
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Erro ao alterar status do usuário: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Erro ao alterar o status do usuário. Por favor, tente novamente.'
        }), 500

@bp.route('/usuarios/excluir/<int:id>', methods=['POST'])
@login_required
@permissao_necessaria('ADMIN')
def excluir_usuario(id):
    """Exclui um usuário existente"""
    if not has_permission(current_user, 'main.excluir_usuario'):
        if request.is_json:
            return jsonify({'success': False, 'message': 'Você não tem permissão para realizar esta ação.'}), 403
        flash('Você não tem permissão para realizar esta ação.', 'danger')
        return redirect(url_for('main.listar_usuarios'))
    
    usuario = Usuario.query.get_or_404(id)
    
    # Impede que o usuário exclua a si mesmo
    if usuario.id == current_user.id:
        if request.is_json:
            return jsonify({'success': False, 'message': 'Você não pode excluir seu próprio usuário.'}), 400
        flash('Você não pode excluir seu próprio usuário.', 'danger')
        return redirect(url_for('main.listar_usuarios'))
    
    try:
        # Verifica se o usuário tem alguma venda associada
        if usuario.vendas:
            if request.is_json:
                return jsonify({
                    'success': False, 
                    'message': 'Não é possível excluir um usuário que possui vendas associadas.'
                }), 400
            flash('Não é possível excluir um usuário que possui vendas associadas.', 'danger')
            return redirect(url_for('main.listar_usuarios'))
        
        # Remove o usuário
        db.session.delete(usuario)
        db.session.commit()
        
        if request.is_json:
            return jsonify({
                'success': True,
                'message': 'Usuário excluído com sucesso!'
            })
            
        flash('Usuário excluído com sucesso!', 'success')
        return redirect(url_for('main.listar_usuarios'))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Erro ao excluir usuário: {str(e)}')
        
        if request.is_json:
            return jsonify({
                'success': False,
                'message': 'Erro ao excluir o usuário. Por favor, tente novamente.'
            }), 500
            
        flash('Erro ao excluir o usuário. Por favor, tente novamente.', 'danger')
        return redirect(url_for('main.listar_usuarios'))

@bp.route('/usuarios/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@permissao_necessaria('ADMIN')
def editar_usuario(id):
    """Edita um usuário existente"""
    usuario = Usuario.query.get_or_404(id)
    form = UsuarioForm(obj=usuario)
    form.funcao.choices = Usuario.FUNCOES
    
    # Define o ID no formulário para validação
    form.id.data = id
    
    if form.validate_on_submit():
        try:
            usuario.nome = form.nome.data
            usuario.username = form.username.data
            usuario.email = form.email.data
            usuario.funcao = form.funcao.data
            usuario.ativo = form.ativo.data
            
            # Atualiza a senha apenas se for informada
            if form.senha.data:
                usuario.senha = get_password_hash(form.senha.data)
            
            db.session.commit()
            
            flash('Usuário atualizado com sucesso!', 'success')
            return redirect(url_for('main.listar_usuarios'))
            
        except Exception as e:
            db.session.rollback()
            flash('Erro ao atualizar usuário. Por favor, tente novamente.', 'danger')
            current_app.logger.error(f'Erro ao atualizar usuário: {str(e)}')
    
    return render_template('usuarios/form.html', form=form, usuario=usuario)

@bp.route('/vendas/nova', methods=['GET', 'POST'])
@login_required
@permissao_necessaria('FATURAMENTO', 'FINANCEIRO')
def nova_venda():
    """Cria uma nova venda"""
    if not has_permission(current_user, 'main.nova_venda'):
        abort(403)
        
    form = VendaForm()
    
    # Carrega a lista de clientes ativos
    form.cliente_id.choices = [('', 'Selecione um cliente')] + [
        (str(c.id), c.nome) for c in Cliente.query.filter_by(ativo=True).order_by('nome').all()
    ]
    
    if form.validate_on_submit():
        try:
            # Validação: cliente_id ou nome_cliente deve ser fornecido
            if not form.cliente_id.data and not form.nome_cliente.data:
                flash('Selecione um cliente ou informe o nome do cliente.', 'danger')
                return render_template('vendas/nova.html', form=form)
                
            # Se cliente_id for fornecido, verifica se é válido
            cliente_id = form.cliente_id.data if form.cliente_id.data != '' else None
            if cliente_id:
                try:
                    cliente = Cliente.query.get(int(cliente_id))
                    if not cliente or not cliente.ativo:
                        flash('Cliente selecionado é inválido ou está inativo.', 'danger')
                        return render_template('vendas/nova.html', form=form)
                except (ValueError, TypeError):
                    flash('ID do cliente inválido.', 'danger')
                    return render_template('vendas/nova.html', form=form)
            
            # Trata o valor do desconto (pode vir como string vazia)
            desconto = 0.0
            if form.desconto.data is not None and form.desconto.data != '':
                try:
                    desconto = float(form.desconto.data)
                except (ValueError, TypeError):
                    desconto = 0.0
            
            # Cria a venda com status 'rascunho' para permitir adicionar itens
            venda = Venda(
                cliente_id=cliente_id,
                nome_cliente=form.nome_cliente.data if not cliente_id else None,
                usuario_id=current_user.id,
                valor_total=0,  # Inicialmente zero, será atualizado com os itens
                status='rascunho',  # Status inicial como rascunho
                observacoes=form.observacoes.data or None,
                numero_cupom=form.numero_cupom.data or None,
                forma_pagamento=form.forma_pagamento.data or 'dinheiro',
                data_venda=form.data_venda.data or datetime.utcnow(),
                desconto=desconto
            )
            
            db.session.add(venda)
            db.session.commit()
            
            flash('Venda criada com sucesso! Adicione os itens da venda.', 'success')
            return redirect(url_for('main.visualizar_venda', id=venda.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar venda: {str(e)}', 'danger')
            current_app.logger.error(f'Erro ao criar venda: {str(e)}')
    
    # Define a data e hora atuais como padrão
    form.data_venda.data = datetime.utcnow()
    return render_template('vendas/nova.html', form=form)

@bp.route('/vendas')
@login_required
@permissao_necessaria('FATURAMENTO', 'FINANCEIRO')
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
    elif status == 'rascunho':
        query = query.filter_by(status='rascunho')
    # Se nenhum filtro de status for aplicado, mostra todos os status
    
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
    
    # Ordena por data de venda mais recente primeiro
    vendas = query.options(
        db.joinedload(Venda.itens).joinedload(ItemVenda.produto)
    ).order_by(Venda.data_venda.desc()).paginate(page=pagina, per_page=15, error_out=False)
    
    return render_template('vendas/listar.html', 
                         vendas=vendas, 
                         busca=busca,
                         status=status,
                         data_inicio=data_inicio,
                         data_fim=data_fim)

@bp.route('/vendas/<int:id>')
@login_required
@permissao_necessaria('FATURAMENTO', 'FINANCEIRO')
def visualizar_venda(id):
    """Visualiza os detalhes de uma venda específica"""
    if not has_permission(current_user, 'main.visualizar_venda'):
        abort(403)
        
    venda = Venda.query.options(
        db.joinedload(Venda.cliente),
        db.joinedload(Venda.usuario),
        db.joinedload(Venda.itens).joinedload(ItemVenda.produto)
    ).get_or_404(id)
    
    # Se a venda estiver finalizada, não permite edição
    if venda.status == 'finalizada':
        flash('Esta venda já foi finalizada e não pode mais ser alterada.', 'warning')
    
    # Formulário para adicionar itens
    form = ItemVendaForm()
    
    # Popula o dropdown de produtos com os produtos ativos
    form.produto_id.choices = [('', 'Selecione um produto...')]  # Adiciona uma opção vazia
    form.produto_id.choices += [(p.id, f"{p.nome} - {p.unidade_medida}") 
                             for p in Produto.query.filter_by(ativo=True).order_by(Produto.nome).all()]
    
    return render_template('vendas/visualizar.html', venda=venda, form=form)


@bp.route('/vendas/<int:venda_id>/imprimir')
@login_required
@permissao_necessaria('FATURAMENTO', 'FINANCEIRO')
def imprimir_venda(venda_id):
    """Gera uma versão para impressão da venda"""
    if not has_permission(current_user, 'main.visualizar_venda'):
        abort(403)
        
    venda = Venda.query.options(
        db.joinedload(Venda.cliente),
        db.joinedload(Venda.usuario),
        db.joinedload(Venda.itens).joinedload(ItemVenda.produto)
    ).get_or_404(venda_id)
    
    # Gera um código de autenticação se não existir
    if not venda.codigo_autenticacao:
        venda.codigo_autenticacao = str(uuid.uuid4())[:8].upper()
        db.session.commit()
    
    return render_template('vendas/imprimir.html', venda=venda, now=datetime.utcnow())


@bp.route('/vendas/<int:venda_id>/itens/adicionar', methods=['POST'])
@login_required
@permissao_necessaria('FATURAMENTO', 'FINANCEIRO')
def adicionar_item_venda(venda_id):
    """Adiciona um item a uma venda existente"""
    if not has_permission(current_user, 'main.editar_venda'):
        abort(403)
    
    venda = Venda.query.get_or_404(venda_id)
    
    # Verifica se a venda pode ser alterada
    if venda.status == 'finalizada':
        flash('Não é possível adicionar itens a uma venda finalizada.', 'danger')
        return redirect(url_for('main.visualizar_venda', id=venda_id))
    
    # Verifica se a venda foi cancelada
    if venda.status == 'cancelada':
        flash('Não é possível adicionar itens a uma venda cancelada.', 'danger')
        return redirect(url_for('main.visualizar_venda', id=venda_id))
    
    form = ItemVendaForm()
    
    if form.validate_on_submit():
        try:
            produto = Produto.query.get_or_404(form.produto_id.data)
            
            # Verifica se há estoque suficiente
            if produto.estoque_atual < form.quantidade.data:
                flash(f'Estoque insuficiente para o produto {produto.nome}. Estoque disponível: {produto.estoque_atual} {produto.unidade_medida}', 'danger')
                return redirect(url_for('main.visualizar_venda', id=venda_id))
            
            # Calcula o total do item
            desconto = form.desconto.data or 0
            total_item = form.quantidade.data * form.preco_unitario.data * (1 - (desconto / 100))
            
            # Cria o item da venda
            item = ItemVenda(
                venda_id=venda.id,
                produto_id=produto.id,
                quantidade=form.quantidade.data,
                preco_unitario=form.preco_unitario.data,
                desconto=desconto,
                total=total_item
            )
            
            # Adiciona o item à venda
            db.session.add(item)
            
            # Atualiza o estoque do produto
            produto.estoque_atual -= form.quantidade.data
            
            # Atualiza o valor total da venda
            # Primeiro, recalculamos o total baseado nos itens atuais
            # Isso é mais seguro do que tentar adicionar ao valor existente
            venda.valor_total = sum(item.total for item in venda.itens)
            
            # Se houver desconto na venda, aplica ao total
            if venda.desconto and venda.desconto > 0:
                venda.valor_total = venda.valor_total * (1 - (venda.desconto / 100))
            
            db.session.commit()
            
            flash('Item adicionado à venda com sucesso!', 'success')
            return redirect(url_for('main.visualizar_venda', id=venda_id))
            
        except Exception as e:
            db.session.rollback()
            flash('Erro ao adicionar item à venda. Por favor, tente novamente.', 'danger')
            current_app.logger.error(f'Erro ao adicionar item à venda: {str(e)}')
    else:
        # Se houver erros de validação, exibe mensagens de erro
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Erro no campo {getattr(form, field).label.text}: {error}', 'danger')
    
    return redirect(url_for('main.visualizar_venda', id=venda_id))


@bp.route('/vendas/<int:venda_id>/itens/<int:item_id>/remover', methods=['POST'])
@login_required
@permissao_necessaria('FATURAMENTO', 'FINANCEIRO')
def remover_item_venda(venda_id, item_id):
    """Remove um item de uma venda"""
    if not has_permission(current_user, 'main.editar_venda'):
        abort(403)
    
    venda = Venda.query.get_or_404(venda_id)
    item = ItemVenda.query.get_or_404(item_id)
    
    # Verifica se o item pertence à venda
    if item.venda_id != venda.id:
        abort(404)
    
    # Verifica se a venda pode ser alterada
    if venda.status == 'finalizada':
        flash('Não é possível remover itens de uma venda finalizada.', 'danger')
        return redirect(url_for('main.visualizar_venda', id=venda_id))
    
    # Verifica se a venda foi cancelada
    if venda.status == 'cancelada':
        flash('Não é possível remover itens de uma venda cancelada.', 'danger')
        return redirect(url_for('main.visualizar_venda', id=venda_id))
    
    try:
        # Obtém o produto para atualizar o estoque
        produto = item.produto
        
        # Remove o item da venda
        db.session.delete(item)
        
        # Atualiza o estoque do produto
        produto.estoque_atual += item.quantidade
        
        # Atualiza o valor total da venda
        venda.valor_total = sum(item.total for item in venda.itens)
        
        # Se a venda não tiver mais itens, define o valor total como zero
        if not venda.itens:
            venda.valor_total = 0
        
        db.session.commit()
        
        flash('Item removido da venda com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Erro ao remover item da venda. Por favor, tente novamente.', 'danger')
        current_app.logger.error(f'Erro ao remover item da venda: {str(e)}')
    
    return redirect(url_for('main.visualizar_venda', id=venda_id))


@bp.route('/api/produto/<int:produto_id>', methods=['GET'])
@login_required
def obter_dados_produto(produto_id):
    """Retorna os dados de um produto em formato JSON para uso via AJAX"""
    produto = Produto.query.get_or_404(produto_id)
    
    if not produto.ativo or produto.estoque_atual <= 0:
        return jsonify({'error': 'Produto indisponível'}), 400
    
    return jsonify({
        'id': produto.id,
        'nome': produto.nome,
        'preco_venda': produto.preco_venda,
        'estoque_atual': produto.estoque_atual,
        'unidade_medida': produto.unidade_medida
    })


@bp.route('/vendas/<int:venda_id>/finalizar', methods=['POST'])
@login_required
@permissao_necessaria('FATURAMENTO', 'FINANCEIRO')
def finalizar_venda(venda_id):
    """Finaliza uma venda, atualizando o status para 'finalizada'"""
    if not has_permission(current_user, 'main.finalizar_venda'):
        abort(403)
    
    venda = Venda.query.get_or_404(venda_id)
    
    # Verifica se a venda já foi finalizada
    if venda.status == 'finalizada':
        flash('Esta venda já foi finalizada anteriormente.', 'warning')
        return redirect(url_for('main.visualizar_venda', id=venda_id))
    
    # Verifica se a venda foi cancelada
    if venda.status == 'cancelada':
        flash('Não é possível finalizar uma venda cancelada.', 'danger')
        return redirect(url_for('main.visualizar_venda', id=venda_id))
    
    # Verifica se a venda tem itens
    if not venda.itens:
        flash('Não é possível finalizar uma venda sem itens.', 'danger')
        return redirect(url_for('main.visualizar_venda', id=venda_id))
    
    try:
        # Atualiza o status da venda para finalizada
        venda.status = 'finalizada'
        # Não define a data de pagamento aqui - será definida na aprovação financeira
        
        # Registra no histórico
        historico = HistoricoVenda(
            venda_id=venda.id,
            status='finalizada',
            usuario_id=current_user.id,
            observacao='Venda finalizada - Aguardando aprovação financeira'
        )
        db.session.add(historico)
        
        db.session.commit()
        
        flash('Venda finalizada com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Erro ao finalizar venda. Por favor, tente novamente.', 'danger')
        current_app.logger.error(f'Erro ao finalizar venda: {str(e)}')
    
    return redirect(url_for('main.visualizar_venda', id=venda_id))


@bp.route('/vendas/<int:venda_id>/aprovar-pagamento', methods=['POST'])
@login_required
@financeiro_required
def aprovar_pagamento(venda_id):
    """Aprova o pagamento de uma venda pelo setor financeiro"""
    if not has_permission(current_user, 'main.aprovar_pagamento'):
        abort(403)
    
    venda = Venda.query.get_or_404(venda_id)
    
    # Verifica se a venda já foi finalizada
    if venda.status != 'finalizada':
        flash('Apenas vendas finalizadas podem ter o pagamento aprovado.', 'warning')
        return redirect(url_for('main.visualizar_venda', id=venda_id))
    
    # Verifica se o pagamento já foi aprovado
    if venda.data_pagamento:
        flash('O pagamento desta venda já foi aprovado anteriormente.', 'info')
        return redirect(url_for('main.visualizar_venda', id=venda_id))
    
    try:
        # Atualiza a data de pagamento
        venda.data_pagamento = datetime.utcnow()
        
        # Registra no histórico
        historico = HistoricoVenda(
            venda_id=venda.id,
            status='pagamento_aprovado',
            usuario_id=current_user.id,
            observacao='Pagamento aprovado pelo setor financeiro'
        )
        db.session.add(historico)
        
        db.session.commit()
        
        flash('Pagamento aprovado com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Erro ao aprovar pagamento. Por favor, tente novamente.', 'danger')
        current_app.logger.error(f'Erro ao aprovar pagamento: {str(e)}')
    
    return redirect(url_for('main.visualizar_venda', id=venda_id))


@bp.route('/vendas/<int:venda_id>/cancelar', methods=['POST'])
@login_required
@permissao_necessaria('FATURAMENTO', 'FINANCEIRO')
def cancelar_venda(venda_id):
    """Cancela uma venda, atualizando o status para 'cancelada'"""
    if not has_permission(current_user, 'main.cancelar_venda'):
        abort(403)
    
    venda = Venda.query.get_or_404(venda_id)
    
    # Verifica se a venda já foi cancelada
    if venda.status == 'cancelada':
        flash('Esta venda já foi cancelada anteriormente.', 'warning')
        return redirect(url_for('main.visualizar_venda', id=venda_id))
    
    # Verifica se a venda já foi finalizada
    if venda.status == 'finalizada':
        flash('Não é possível cancelar uma venda já finalizada.', 'danger')
        return redirect(url_for('main.visualizar_venda', id=venda_id))
    
    try:
        # Obtém o motivo do cancelamento do formulário
        motivo = request.form.get('motivo_cancelamento', 'Sem motivo informado')
        
        # Atualiza o status da venda para cancelada
        venda.status = 'cancelada'
        venda.data_cancelamento = datetime.utcnow()
        
        # Registra no histórico
        historico = HistoricoVenda(
            venda_id=venda.id,
            status='cancelada',
            usuario_id=current_user.id,
            observacao=f'Venda cancelada. Motivo: {motivo}'
        )
        db.session.add(historico)
        
        # Se a venda já estava finalizada, devolve os itens ao estoque
        if venda.status == 'finalizada':
            for item in venda.itens:
                if item.produto:
                    item.produto.estoque_atual += item.quantidade
        
        db.session.commit()
        
        flash('Venda cancelada com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Erro ao cancelar venda. Por favor, tente novamente.', 'danger')
        current_app.logger.error(f'Erro ao cancelar venda: {str(e)}')
    
    return redirect(url_for('main.visualizar_venda', id=venda_id))

@bp.route('/produtos')
@login_required
@producao_required
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

@bp.route('/clientes')
@login_required
@faturamento_required
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

@bp.route('/estoque/diario', methods=['GET', 'POST'])
@login_required
@producao_required
def estoque_diario():
    """Página de estoque diário"""
    hoje = datetime.utcnow().date()
    
    # Obtém o produto (ovos)
    produto = Produto.query.filter_by(ativo=True).first()
    
    if not produto:
        flash('Nenhum produto ativo encontrado.', 'warning')
        return redirect(url_for('main.dashboard'))
    
    # Obtém ou cria o registro de estoque de hoje
    estoque = EstoqueDiario.query.filter_by(
        produto_id=produto.id,
        data=hoje
    ).first()
    
    if not estoque:
        # Se não existe registro para hoje, cria um com base no estoque atual
        valor_estoque = produto.estoque_atual * (produto.preco_compra or 0)
        estoque = EstoqueDiario(
            data=hoje,
            produto_id=produto.id,
            quantidade=produto.estoque_atual,
            valor_estoque=valor_estoque,
            estoque_inicial=produto.estoque_atual,
            entrada=0,
            saida=0,
            estoque_final=produto.estoque_atual,
            observacoes='',
            usuario_id=current_user.id
        )
        db.session.add(estoque)
        db.session.commit()
    
    # Cria o formulário
    form = EstoqueDiarioForm()
    
    # Se for uma requisição POST, valida e processa os dados
    if form.validate_on_submit():
        try:
            entrada = form.entrada.data or 0
            
            # Log para depuração
            print(f"[DEBUG] Dados do formulário: entrada={entrada}, observacoes={form.observacoes.data}")
            print(f"[DEBUG] Estoque antes da atualização: entrada={estoque.entrada}, saida={estoque.saida}, estoque_inicial={estoque.estoque_inicial}")
            
            # Atualiza os dados do estoque
            # Soma a nova entrada ao valor existente
            estoque.entrada = (estoque.entrada or 0) + entrada
            
            # Calcula o estoque final corretamente
            estoque.estoque_final = (estoque.estoque_inicial or 0) + (estoque.entrada or 0) - (estoque.saida or 0)
            
            # Atualiza observações e usuário
            if form.observacoes.data:
                if estoque.observacoes:
                    estoque.observacoes += f"\n{form.observacoes.data}"
                else:
                    estoque.observacoes = form.observacoes.data
                    
            estoque.usuario_id = current_user.id
            
            # Atualiza o estoque do produto
            produto.estoque_atual = estoque.estoque_final
            
            # Log após atualização
            print(f"[DEBUG] Estoque após atualização: entrada={estoque.entrada}, saida={estoque.saida}, estoque_final={estoque.estoque_final}")
            
            # Salva as alterações
            db.session.commit()
            
            flash('Estoque atualizado com sucesso!', 'success')
            return redirect(url_for('main.estoque_diario'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar o estoque: {str(e)}', 'danger')
    
    # Se for GET, preenche o formulário com os dados atuais
    elif request.method == 'GET':
        form.entrada.data = estoque.entrada or 0
        form.observacoes.data = estoque.observacoes or ''
    
    return render_template('estoque/diario.html',
                         produto=produto,
                         estoque=estoque,
                         form=form,
                         hoje=hoje.strftime('%d/%m/%Y'))


@bp.route('/financeiro')
@login_required
@faturamento_required
def financeiro():
    """Dashboard financeiro"""
    if not has_permission(current_user, 'relatorios.relatorio_financeiro'):
        abort(403)
    
    # Obter parâmetros de filtro
    status = request.args.get('status', 'pendentes')
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    cliente_id = request.args.get('cliente_id', type=int)
    
    # Construir a consulta
    query = Venda.query
    
    # Aplicar filtros
    if status == 'pagos':
        query = query.filter_by(status='pago')
    elif status == 'canceladas':
        query = query.filter_by(status='cancelada')
    elif status == 'pendentes':
        query = query.filter_by(status='pendente')
    # 'todos' não precisa de filtro adicional
    
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
    
    # Ordenar por data de venda (mais recente primeiro)
    vendas = query.order_by(Venda.data_venda.desc()).all()
    
    # Obter lista de clientes para o filtro
    clientes = Cliente.query.order_by(Cliente.nome).all()
    
    return render_template('financeiro/index.html',
                         vendas=vendas,
                         clientes=clientes,
                         status=status,
                         data_inicio=data_inicio,
                         data_fim=data_fim,
                         cliente_id=cliente_id)

@bp.route('/clientes/novo', methods=['GET', 'POST'])
@login_required
def novo_cliente():
    """Cadastrar novo cliente"""
    if not has_permission(current_user, 'main.novo_cliente'):
        abort(403)
    
    form = ClienteForm()
    
    if form.validate_on_submit():
        try:
            cliente = Cliente(
                nome=form.nome.data,
                email=form.email.data,
                telefone=form.telefone.data,
                endereco=form.endereco.data,
                ativo=True
            )
            
            db.session.add(cliente)
            db.session.commit()
            
            flash('Cliente cadastrado com sucesso!', 'success')
            return redirect(url_for('main.listar_clientes'))
            
        except Exception as e:
            db.session.rollback()
            flash('Erro ao cadastrar cliente. Por favor, tente novamente.', 'danger')
            current_app.logger.error(f'Erro ao cadastrar cliente: {str(e)}')
    
    return render_template('clientes/novo.html', form=form, title='Novo Cliente')

@bp.route('/produtos/novo', methods=['GET', 'POST'])
@login_required
def novo_produto():
    """Cadastrar novo produto"""
    if not has_permission(current_user, 'main.novo_produto'):
        abort(403)
    
    form = ProdutoForm()
    
    if form.validate_on_submit():
        try:
            produto = Produto(
                codigo=form.codigo.data,
                nome=form.nome.data,
                descricao=form.descricao.data,
                categoria=form.categoria.data,
                preco_compra=form.preco_compra.data,
                preco_venda=form.preco_venda.data,
                estoque_atual=form.estoque_atual.data or 0,
                estoque_minimo=form.estoque_minimo.data or 0,
                unidade_medida=form.unidade_medida.data,
                ativo=form.ativo.data
            )
            
            db.session.add(produto)
            db.session.commit()
            
            flash('Produto cadastrado com sucesso!', 'success')
            return redirect(url_for('main.listar_produtos'))
            
        except Exception as e:
            db.session.rollback()
            flash('Erro ao cadastrar produto. Por favor, verifique os dados e tente novamente.', 'danger')
            current_app.logger.error(f'Erro ao cadastrar produto: {str(e)}')
    
    return render_template('produtos/novo.html', form=form, title='Novo Produto')

@bp.route('/produtos/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_produto(id):
    """Editar produto existente"""
    if not has_permission(current_user, 'main.editar_produto'):
        abort(403)
    
    produto = Produto.query.get_or_404(id)
    form = ProdutoForm(obj=produto)
    
    if form.validate_on_submit():
        try:
            produto.codigo = form.codigo.data
            produto.nome = form.nome.data
            produto.descricao = form.descricao.data
            produto.categoria = form.categoria.data
            produto.preco_compra = form.preco_compra.data
            produto.preco_venda = form.preco_venda.data
            produto.estoque_atual = form.estoque_atual.data or 0
            produto.estoque_minimo = form.estoque_minimo.data or 0
            produto.unidade_medida = form.unidade_medida.data
            produto.ativo = form.ativo.data
            
            db.session.commit()
            
            flash('Produto atualizado com sucesso!', 'success')
            return redirect(url_for('main.listar_produtos'))
            
        except Exception as e:
            db.session.rollback()
            flash('Erro ao atualizar produto. Por favor, tente novamente.', 'danger')
            current_app.logger.error(f'Erro ao atualizar produto: {str(e)}')
    
    return render_template('produtos/editar.html', form=form, produto=produto, title='Editar Produto')

@bp.route('/produtos/visualizar/<int:id>')
@login_required
def visualizar_produto(id):
    """Visualizar detalhes de um produto"""
    if not has_permission(current_user, 'main.visualizar_produto'):
        abort(403)
    
    produto = Produto.query.get_or_404(id)
    return render_template('produtos/visualizar.html', produto=produto, title='Visualizar Produto')

@bp.route('/produtos/alterar-status/<int:id>', methods=['POST'])
@login_required
def alterar_status_produto(id):
    """Alterar o status de ativação de um produto"""
    if not has_permission(current_user, 'main.alterar_status_produto'):
        return jsonify({'success': False, 'message': 'Você não tem permissão para realizar esta ação.'}), 403
    
    produto = Produto.query.get_or_404(id)
    
    try:
        data = request.get_json()
        if 'ativo' not in data:
            return jsonify({'success': False, 'message': 'Dados inválidos.'}), 400
        
        produto.ativo = data['ativo']
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Status do produto atualizado com sucesso!',
            'novo_status': produto.ativo
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Erro ao alterar status do produto: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Erro ao alterar o status do produto. Por favor, tente novamente.'
        }), 500

@bp.route('/produtos/excluir/<int:id>', methods=['POST'])
@login_required
def excluir_produto(id):
    """Excluir um produto"""
    if not has_permission(current_user, 'main.excluir_produto'):
        abort(403)
    
    produto = Produto.query.get_or_404(id)
    
    try:
        # Verificar se o produto está sendo usado em alguma venda ou compra
        # Se estiver, não permitir a exclusão
        # if produto.vendas or produto.compras:
        #     flash('Não é possível excluir este produto, pois existem registros de venda ou compra associados a ele.', 'danger')
        #     return redirect(url_for('main.visualizar_produto', id=id))
        
        # Marcar como inativo em vez de excluir fisicamente (soft delete)
        produto.ativo = False
        db.session.commit()
        
        flash('Produto desativado com sucesso!', 'success')
        return redirect(url_for('main.listar_produtos'))
        
    except Exception as e:
        db.session.rollback()
        flash('Erro ao desativar o produto. Por favor, tente novamente.', 'danger')
        current_app.logger.error(f'Erro ao desativar produto: {str(e)}')
        return redirect(url_for('main.visualizar_produto', id=id))

@bp.route('/ajuda')
@login_required
def ajuda():
    """Página principal de ajuda"""
    return render_template('ajuda/index.html')

@bp.route('/perfil', methods=['GET', 'POST'])
@login_required
def perfil():
    """Exibe e permite a edição do perfil do usuário logado"""
    form = PerfilUsuarioForm()
    
    # Preenche o formulário com os dados atuais do usuário
    if request.method == 'GET':
        form.id.data = current_user.id
        form.nome.data = current_user.nome
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.telefone.data = current_user.telefone
    
    if form.validate_on_submit():
        try:
            # Verifica se a senha atual foi fornecida se estiver tentando alterar a senha
            if form.nova_senha.data and not check_password_hash(current_user.senha, form.senha_atual.data):
                flash('A senha atual fornecida está incorreta.', 'danger')
                return render_template('usuarios/perfil.html', form=form)
            
            # Atualiza os dados do usuário
            current_user.nome = form.nome.data
            current_user.username = form.username.data
            current_user.email = form.email.data
            current_user.telefone = form.telefone.data
            
            # Atualiza a senha se fornecida
            if form.nova_senha.data:
                current_user.senha = get_password_hash(form.nova_senha.data)
            
            db.session.commit()
            flash('Perfil atualizado com sucesso!', 'success')
            return redirect(url_for('main.perfil'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Erro ao atualizar perfil: {str(e)}')
            flash('Ocorreu um erro ao atualizar o perfil. Por favor, tente novamente.', 'danger')
    
    return render_template('usuarios/perfil.html', form=form)

@bp.route('/ajuda/contato', methods=['GET', 'POST'])
@login_required
def contato():
    if request.method == 'POST':
        # Aqui você pode adicionar a lógica para processar o formulário de contato
        nome = request.form.get('nome')
        email = request.form.get('email')
        mensagem = request.form.get('mensagem')
        
        # Exemplo de validação simples
        if not nome or not email or not mensagem:
            flash('Por favor, preencha todos os campos do formulário.', 'danger')
        else:
            # Aqui você pode adicionar a lógica para enviar o e-mail
            # Por exemplo, usando Flask-Mail ou outro serviço de e-mail
            
            # Simulando o envio do e-mail
            print(f"Novo contato de {nome} ({email}): {mensagem}")
            
            flash('Sua mensagem foi enviada com sucesso! Entraremos em contato em breve.', 'success')
            return redirect(url_for('main.ajuda'))
    
    return render_template('ajuda/contato.html')
