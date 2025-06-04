from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, IntegerField, SelectField, TextAreaField, BooleanField, DateTimeField, PasswordField, validators
from wtforms.widgets import HiddenInput
from wtforms.validators import DataRequired, NumberRange, Optional, Email, EqualTo, ValidationError, Length, InputRequired
from datetime import datetime
from extensions import db
from models import Usuario, Produto

class LoginForm(FlaskForm):
    """Formulário de login"""
    username = StringField('Usuário', validators=[
        DataRequired(message='O nome de usuário é obrigatório'),
        Length(min=3, max=50, message='O nome de usuário deve ter entre 3 e 50 caracteres')
    ])
    
    password = PasswordField('Senha', validators=[
        DataRequired(message='A senha é obrigatória'),
        Length(min=6, message='A senha deve ter pelo menos 6 caracteres')
    ])
    
    remember_me = BooleanField('Lembrar de mim')


class UsuarioForm(FlaskForm):
    """Formulário para criação e edição de usuários"""
    id = IntegerField('ID', widget=HiddenInput())
    nome = StringField('Nome Completo', validators=[
        DataRequired(message='O nome é obrigatório'),
        validators.Length(min=3, max=100, message='O nome deve ter entre 3 e 100 caracteres')
    ])
    
    username = StringField('Nome de Usuário', validators=[
        DataRequired(message='O nome de usuário é obrigatório'),
        validators.Length(min=3, max=50, message='O nome de usuário deve ter entre 3 e 50 caracteres'),
        validators.Regexp('^[A-Za-z0-9_.]+$', message='Use apenas letras, números, pontos e underlines')
    ])
    
    email = StringField('E-mail', validators=[
        DataRequired(message='O e-mail é obrigatório'),
        Email(message='Informe um e-mail válido')
    ])
    
    senha = PasswordField('Senha', validators=[
        validators.Optional(),  # Opcional para edição
        validators.Length(min=6, message='A senha deve ter pelo menos 6 caracteres'),
        validators.EqualTo('confirmar_senha', message='As senhas não conferem')
    ])
    
    confirmar_senha = PasswordField('Confirmar Senha')
    
    funcao = SelectField('Função', choices=Usuario.FUNCOES, validators=[
        DataRequired(message='Selecione uma função')
    ])
    
    ativo = BooleanField('Usuário Ativo', default=True)
    
    def validate_username(self, field):
        """Valida se o nome de usuário já está em uso"""
        if hasattr(self, 'id') and self.id.data:  # Se for uma edição
            usuario = Usuario.query.filter(
                Usuario.username == field.data,
                Usuario.id != self.id.data
            ).first()
        else:  # Se for um novo usuário
            usuario = Usuario.query.filter_by(username=field.data).first()
            
        if usuario:
            raise ValidationError('Este nome de usuário já está em uso. Por favor, escolha outro.')
    
    def validate_email(self, field):
        """Valida se o e-mail já está em uso"""
        if hasattr(self, 'id') and self.id.data:  # Se for uma edição
            usuario = Usuario.query.filter(
                Usuario.email == field.data,
                Usuario.id != self.id.data
            ).first()
        else:  # Se for um novo usuário
            usuario = Usuario.query.filter_by(email=field.data).first()
            
        if usuario:
            raise ValidationError('Este e-mail já está em uso. Por favor, utilize outro.')

# Formulário para busca de usuários
class BuscarUsuarioForm(FlaskForm):
    busca = StringField('Buscar', validators=[Optional()])
    funcao = SelectField('Função', choices=[('', 'Todas as funções')] + Usuario.FUNCOES, validators=[Optional()])
    status = SelectField('Status', choices=[
        ('', 'Todos'),
        ('ativo', 'Ativos'),
        ('inativo', 'Inativos')
    ], validators=[Optional()])

class ProdutoForm(FlaskForm):
    codigo = StringField('Código', validators=[DataRequired(message='O código é obrigatório')])
    nome = StringField('Nome', validators=[DataRequired(message='O nome é obrigatório')])
    descricao = TextAreaField('Descrição', validators=[Optional()])
    categoria = StringField('Categoria', validators=[Optional()])
    preco_compra = FloatField('Preço de Custo', validators=[
        DataRequired(message='O preço de custo é obrigatório'),
        NumberRange(min=0, message='O preço não pode ser negativo')
    ])
    preco_venda = FloatField('Preço de Venda', validators=[
        DataRequired(message='O preço de venda é obrigatório'),
        NumberRange(min=0, message='O preço não pode ser negativo')
    ])
    estoque_atual = FloatField('Estoque Atual', validators=[
        DataRequired(message='O estoque é obrigatório'),
        NumberRange(min=0, message='O estoque não pode ser negativo')
    ])
    estoque_minimo = FloatField('Estoque Mínimo', validators=[
        Optional(),
        NumberRange(min=0, message='O estoque mínimo não pode ser negativo')
    ])
    unidade_medida = SelectField('Unidade de Medida', choices=[
        ('cx', 'Caixa'),
        ('un', 'Unidade'),
        ('kg', 'Quilograma'),
        ('g', 'Grama'),
        ('l', 'Litro'),
        ('ml', 'Mililitro'),
        ('dz', 'Dúzia')
    ], validators=[DataRequired()], default='cx')
    ativo = BooleanField('Ativo', default=True)

class VendaForm(FlaskForm):
    # Opções de forma de pagamento
    FORMAS_PAGAMENTO = [
        ('dinheiro', 'Dinheiro'),
        ('cartao_credito', 'Cartão de Crédito'),
        ('cartao_debito', 'Cartão de Débito'),
        ('pix', 'PIX'),
        ('transferencia', 'Transferência Bancária'),
        ('outro', 'Outro')
    ]
    
    cliente_id = SelectField('Cliente', 
                           coerce=lambda x: int(x) if x and x != '' else None, 
                           validators=[Optional()], 
                           validate_choice=False)
    
    nome_cliente = StringField('Nome do Cliente (se não cadastrado)', 
                             validators=[
                                 Optional(),
                                 Length(max=100, message='O nome do cliente deve ter no máximo 100 caracteres')
                             ],
                             render_kw={"placeholder": "Nome do cliente não cadastrado"})
    
    forma_pagamento = SelectField('Forma de Pagamento', 
                                 choices=FORMAS_PAGAMENTO,
                                 validators=[DataRequired(message='Selecione a forma de pagamento')],
                                 default='dinheiro')
    
    data_venda = DateTimeField('Data da Venda', 
                             format='%Y-%m-%dT%H:%M',
                             validators=[DataRequired(message='A data da venda é obrigatória')],
                             render_kw={"type": "datetime-local"})
    
    desconto = FloatField('Desconto (R$)',
                        validators=[
                            NumberRange(min=0, message='O desconto não pode ser negativo'),
                            Optional()
                        ],
                        default=0.0,
                        render_kw={"step": "0.01", "min": "0"})
    
    numero_cupom = StringField('Número do Cupom', 
                             validators=[
                                 Optional(),
                                 Length(max=50, message='O número do cupom deve ter no máximo 50 caracteres')
                             ],
                             render_kw={"placeholder": "Opcional"})
    
    observacoes = TextAreaField('Observações', 
                              validators=[Optional()],
                              render_kw={"rows": 3, "placeholder": "Observações adicionais sobre a venda"})
    
    def validate(self, extra_validators=None):
        """Validação personalizada para garantir que pelo menos um cliente seja selecionado"""
        if not super().validate():
            return False
            
        # Verifica se pelo menos um dos campos de cliente foi preenchido
        if not self.cliente_id.data and not self.nome_cliente.data:
            self.cliente_id.errors.append('Selecione um cliente ou informe o nome do cliente')
            return False
            
        return True


class ItemVendaForm(FlaskForm):
    """Formulário para adicionar itens a uma venda"""
    produto_id = SelectField('Produto', 
                           coerce=lambda x: int(x) if x else 0, 
                           validators=[
                               DataRequired(message='Selecione um produto')
                           ],
                           choices=[],  # Will be populated in the route
                           render_kw={"class": "form-select produto-select"})
    
    quantidade = FloatField('Quantidade', 
                          validators=[
                              DataRequired(message='A quantidade é obrigatória'),
                              NumberRange(min=0.001, message='A quantidade deve ser maior que zero')
                          ],
                          render_kw={
                              "class": "form-control quantidade",
                              "step": "0.001",
                              "min": "0.001"
                          })
    
    preco_unitario = FloatField('Preço Unitário', 
                              validators=[
                                  DataRequired(message='O preço unitário é obrigatório'),
                                  NumberRange(min=0.01, message='O preço deve ser maior que zero')
                              ],
                              render_kw={
                                  "class": "form-control preco-unitario",
                                  "step": "0.01",
                                  "min": "0.01"
                              })
    
    desconto = FloatField('Desconto (%)', 
                         validators=[
                             NumberRange(min=0, max=100, message='O desconto deve estar entre 0 e 100%'),
                             Optional()
                         ], 
                         default=0,
                         render_kw={
                             "class": "form-control desconto",
                             "step": "0.1",
                             "min": "0",
                             "max": "100"
                         })
    
    def __init__(self, *args, **kwargs):
        super(ItemVendaForm, self).__init__(*args, **kwargs)
        # Carrega a lista de produtos ativos em estoque
        self.atualizar_choices_produtos()
    
    def atualizar_choices_produtos(self):
        """Atualiza as opções de produtos disponíveis"""
        self.produto_id.choices = [('', 'Selecione um produto')] + [
            (str(p.id), f"{p.nome} - Estoque: {p.estoque_atual} {p.unidade_medida} - R$ {p.preco_venda:.2f}") 
            for p in Produto.query.filter(
                Produto.ativo == True, 
                Produto.estoque_atual > 0
            ).order_by(Produto.nome).all()
        ]
    
    def validate_quantidade(self, field):
        """Valida se a quantidade está disponível em estoque"""
        if field.data and self.produto_id.data:
            produto = Produto.query.get(self.produto_id.data)
            if produto and field.data > produto.estoque_atual:
                raise ValidationError(f'Quantidade indisponível em estoque. Disponível: {produto.estoque_atual} {produto.unidade_medida}')
    
    def validate_preco_unitario(self, field):
        """Valida se o preço unitário é válido"""
        if field.data and field.data <= 0:
            raise ValidationError('O preço unitário deve ser maior que zero')
    
    def validate_produto_id(self, field):
        """Valida se o produto selecionado é válido"""
        if field.data:
            produto = Produto.query.get(field.data)
            if not produto or not produto.ativo or produto.estoque_atual <= 0:
                raise ValidationError('Produto selecionado não está disponível')

class ClienteForm(FlaskForm):
    """Formulário para criação e edição de clientes"""
    id = IntegerField('ID', widget=HiddenInput())
    
    nome = StringField('Nome Completo', validators=[
        DataRequired(message='O nome é obrigatório'),
        Length(min=3, max=100, message='O nome deve ter entre 3 e 100 caracteres')
    ])
    
    tipo_pessoa = SelectField('Tipo', choices=[
        ('fisica', 'Pessoa Física'),
        ('juridica', 'Pessoa Jurídica')
    ], default='fisica')
    
    cpf_cnpj = StringField('CPF/CNPJ', validators=[
        Optional(),
        Length(min=11, max=14, message='CPF/CNPJ inválido')
    ])
    
    rg_ie = StringField('RG/Inscrição Estadual', validators=[
        Optional(),
        Length(max=20, message='Máximo de 20 caracteres')
    ])
    
    email = StringField('E-mail', validators=[
        Optional(),
        Email(message='Informe um e-mail válido')
    ])
    
    telefone = StringField('Telefone', validators=[
        Optional(),
        Length(min=10, max=15, message='Telefone inválido')
    ])
    
    celular = StringField('Celular', validators=[
        Optional(),
        Length(min=10, max=15, message='Celular inválido')
    ])
    
    cep = StringField('CEP', validators=[
        Optional(),
        Length(min=8, max=9, message='CEP inválido')
    ])
    
    endereco = StringField('Endereço', validators=[
        Optional(),
        Length(max=100, message='Máximo de 100 caracteres')
    ])
    
    numero = StringField('Número', validators=[
        Optional(),
        Length(max=20, message='Máximo de 20 caracteres')
    ])
    
    complemento = StringField('Complemento', validators=[
        Optional(),
        Length(max=100, message='Máximo de 100 caracteres')
    ])
    
    bairro = StringField('Bairro', validators=[
        Optional(),
        Length(max=50, message='Máximo de 50 caracteres')
    ])
    
    cidade = StringField('Cidade', validators=[
        Optional(),
        Length(max=50, message='Máximo de 50 caracteres')
    ])
    
    estado = SelectField('Estado', choices=[
        ('', 'Selecione...'),
        ('AC', 'Acre'),
        ('AL', 'Alagoas'),
        ('AP', 'Amapá'),
        ('AM', 'Amazonas'),
        ('BA', 'Bahia'),
        ('CE', 'Ceará'),
        ('DF', 'Distrito Federal'),
        ('ES', 'Espírito Santo'),
        ('GO', 'Goiás'),
        ('MA', 'Maranhão'),
        ('MT', 'Mato Grosso'),
        ('MS', 'Mato Grosso do Sul'),
        ('MG', 'Minas Gerais'),
        ('PA', 'Pará'),
        ('PB', 'Paraíba'),
        ('PR', 'Paraná'),
        ('PE', 'Pernambuco'),
        ('PI', 'Piauí'),
        ('RJ', 'Rio de Janeiro'),
        ('RN', 'Rio Grande do Norte'),
        ('RS', 'Rio Grande do Sul'),
        ('RO', 'Rondônia'),
        ('RR', 'Roraima'),
        ('SC', 'Santa Catarina'),
        ('SP', 'São Paulo'),
        ('SE', 'Sergipe'),
        ('TO', 'Tocantins')
    ], validators=[Optional()])
    
    observacoes = TextAreaField('Observações', validators=[Optional()])
    ativo = BooleanField('Cliente Ativo', default=True)
    
    def validate_cpf_cnpj(self, field):
        if field.data:
            numeros = ''.join(filter(str.isdigit, field.data))
            valor = ''.join(filter(str.isdigit, field.data))
            
            if self.tipo_pessoa.data == 'fisica' and len(valor) != 11:
                raise ValidationError('CPF deve conter 11 dígitos')
            elif self.tipo_pessoa.data == 'juridica' and len(valor) != 14:
                raise ValidationError('CNPJ deve conter 14 dígitos')


class PerfilUsuarioForm(FlaskForm):
    """Formulário para edição do perfil do usuário"""
    id = IntegerField('ID', widget=HiddenInput())
    
    nome = StringField('Nome Completo', validators=[
        DataRequired(message='O nome é obrigatório'),
        validators.Length(min=3, max=100, message='O nome deve ter entre 3 e 100 caracteres')
    ])
    
    username = StringField('Nome de Usuário', validators=[
        DataRequired(message='O nome de usuário é obrigatório'),
        validators.Length(min=3, max=50, message='O nome de usuário deve ter entre 3 e 50 caracteres'),
        validators.Regexp('^[A-Za-z0-9_.]+$', message='Use apenas letras, números, pontos e underlines')
    ])
    
    email = StringField('E-mail', validators=[
        DataRequired(message='O e-mail é obrigatório'),
        Email(message='Informe um e-mail válido')
    ])
    
    senha_atual = PasswordField('Senha Atual', validators=[
        Optional(),  # Opcional, mas necessário para alterar a senha
        Length(min=6, message='A senha deve ter pelo menos 6 caracteres')
    ])
    
    nova_senha = PasswordField('Nova Senha', validators=[
        Optional(),  # Opcional, só é necessário se quiser alterar a senha
        Length(min=6, message='A senha deve ter pelo menos 6 caracteres'),
        EqualTo('confirmar_nova_senha', message='As senhas não conferem')
    ])
    
    confirmar_nova_senha = PasswordField('Confirmar Nova Senha')
    
    telefone = StringField('Telefone', validators=[
        Optional(),
        Length(min=10, max=15, message='Telefone inválido')
    ])
    
    def __init__(self, *args, **kwargs):
        super(PerfilUsuarioForm, self).__init__(*args, **kwargs)
        self.original_username = self.username.data if self.username.data else None
        self.original_email = self.email.data if self.email.data else None
    
    def validate_username(self, field):
        # Verifica se o nome de usuário já está em uso por outro usuário
        if field.data != self.original_username:
            usuario = Usuario.query.filter_by(username=field.data).first()
            if usuario is not None:
                raise ValidationError('Este nome de usuário já está em uso. Por favor, escolha outro.')
    
    def validate_email(self, field):
        # Verifica se o e-mail já está em uso por outro usuário
        if field.data != self.original_email:
            usuario = Usuario.query.filter_by(email=field.data).first()
            if usuario is not None:
                raise ValidationError('Este e-mail já está cadastrado. Por favor, utilize outro.')


class EstoqueDiarioForm(FlaskForm):
    """Formulário para controle de estoque diário"""
    entrada = FloatField('Entrada', validators=[
        DataRequired(message='A quantidade de entrada é obrigatória'),
        NumberRange(min=0, message='A quantidade não pode ser negativa')
    ])
    
    observacoes = TextAreaField('Observações', validators=[
        Optional(),
        Length(max=500, message='Máximo de 500 caracteres')
    ])
    
    def __init__(self, *args, **kwargs):
        super(EstoqueDiarioForm, self).__init__(*args, **kwargs)
        
    def validate(self, extra_validators=None):
        if not super().validate():
            return False
            
        # Validações adicionais podem ser adicionadas aqui
        return True


class ConfiguracaoSistemaForm(FlaskForm):
    """Formulário para configurações do sistema"""
    nome_empresa = StringField('Nome da Empresa', validators=[
        DataRequired(message='O nome da empresa é obrigatório'),
        Length(max=100, message='Máximo de 100 caracteres')
    ])
    
    email_contato = StringField('E-mail de Contato', validators=[
        DataRequired(message='O e-mail de contato é obrigatório'),
        Email(message='Informe um e-mail válido')
    ])
    
    itens_por_pagina = IntegerField('Itens por Página', validators=[
        DataRequired(message='O número de itens por página é obrigatório'),
        NumberRange(min=5, max=100, message='Deve ser entre 5 e 100 itens')
    ], default=10)
    
    horario_abertura = StringField('Horário de Abertura', validators=[
        Optional(),
        Length(max=5, message='Formato: HH:MM')
    ], render_kw={"placeholder": "08:00"})
    
    horario_fechamento = StringField('Horário de Fechamento', validators=[
        Optional(),
        Length(max=5, message='Formato: HH:MM')
    ], render_kw={"placeholder": "18:00"})
    
    notificacoes_por_email = BooleanField('Notificações por E-mail', default=True,
                                         description='Habilita o envio de notificações por e-mail')
    
    modo_manutencao = BooleanField('Modo Manutenção', default=False,
                                 description='Ative para colocar o sistema em modo manutenção')
    
    mensagem_manutencao = TextAreaField('Mensagem de Manutenção', validators=[
        Optional(),
        Length(max=500, message='Máximo de 500 caracteres')
    ], render_kw={"rows": 3, "placeholder": "Sistema em manutenção. Volte em breve!"})
    
    def __init__(self, *args, **kwargs):
        super(ConfiguracaoSistemaForm, self).__init__(*args, **kwargs)


class ConfiguracaoSegurancaForm(FlaskForm):
    """Formulário para configurações de segurança"""
    forca_senha = SelectField('Força da Senha Mínima', choices=[
        ('fraca', 'Fraca (mínimo 6 caracteres)'),
        ('media', 'Média (letras, números e 8+ caracteres)'),
        ('forte', 'Forte (letras maiúsculas, minúsculas, números e caracteres especiais)')
    ], validators=[DataRequired()])
    
    autenticacao_dois_fatores = BooleanField('Exigir autenticação em dois fatores para administradores', 
                                           default=False)
    
    bloqueio_tentativas = BooleanField('Bloquear conta após 5 tentativas de login malsucedidas', 
                                     default=True)
    
    tempo_sessao = IntegerField('Tempo de expiração da sessão (minutos)', 
                              validators=[
                                  DataRequired(message='O tempo de sessão é obrigatório'),
                                  NumberRange(min=5, max=1440, message='O tempo deve estar entre 5 e 1440 minutos')
                              ], 
                              default=30)
    
    def __init__(self, *args, **kwargs):
        super(ConfiguracaoSegurancaForm, self).__init__(*args, **kwargs)


class ConfiguracaoBackupForm(FlaskForm):
    """Formulário para configurações de backup"""
    backup_automatico = BooleanField('Ativar backup automático', default=True)
    
    frequencia_backup = SelectField('Frequência do Backup', choices=[
        ('diario', 'Diário'),
        ('semanal', 'Semanal'),
        ('mensal', 'Mensal')
    ], validators=[DataRequired()])
    
    hora_backup = StringField('Horário do Backup', 
                             validators=[
                                 DataRequired(message='O horário do backup é obrigatório'),
                                 Length(max=5, message='Formato: HH:MM')
                             ],
                             default='02:00')
    
    manter_backups = IntegerField('Manter os últimos backups', 
                                validators=[
                                    DataRequired(message='O número de backups é obrigatório'),
                                    NumberRange(min=1, message='Deve ser pelo menos 1 backup')
                                ],
                                default=30)
