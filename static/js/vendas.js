// Função para formatar valores monetários
function formatarMoeda(valor) {
    return parseFloat(valor).toLocaleString('pt-BR', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

// Função para calcular o valor com desconto
function calcularValorComDesconto(quantidade, precoUnitario, desconto) {
    const valorBruto = quantidade * precoUnitario;
    const valorDesconto = valorBruto * (desconto / 100);
    return valorBruto - valorDesconto;
}

// Função para atualizar os valores totais da venda
function atualizarValoresTotais() {
    let subtotal = 0;
    
    // Soma os valores de todos os itens
    $('table tbody tr').each(function() {
        const quantidade = parseFloat($(this).find('td:eq(1)').text().trim().replace('.', '').replace(',', '.'));
        const precoUnitario = parseFloat($(this).find('td:eq(2)').text().replace('R$', '').trim().replace('.', '').replace(',', '.'));
        const desconto = $(this).find('td:eq(3)').text().trim();
        const descontoPercentual = desconto === '-' ? 0 : parseFloat(desconto);
        
        const valorTotal = calcularValorComDesconto(quantidade, precoUnitario, descontoPercentual);
        subtotal += valorTotal;
    });
    
    // Atualiza os totais
    const descontoGeral = parseFloat($('#desconto_geral').val()) || 0;
    const total = subtotal - descontoGeral;
    
    $('#subtotal').text('R$ ' + formatarMoeda(subtotal));
    $('#total_geral').text('R$ ' + formatarMoeda(total));
}

// Document Ready
$(document).ready(function() {
    // Inicializa os tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Evento para carregar dados do produto selecionado (Adicionar Item)
    $('#produto_id').on('change', function() {
        const produtoId = $(this).val();
        if (!produtoId) {
            resetarCamposProduto();
            return;
        }
        
        const option = $(this).find('option:selected');
        const estoque = parseFloat(option.data('estoque'));
        const unidade = option.data('unidade');
        const preco = parseFloat(option.data('preco'));
        
        // Atualiza campos
        $('#unidade_medida').text(unidade);
        $('#estoque_disponivel').text(estoque + ' ' + unidade);
        $('#preco_unitario').val(preco.toFixed(2));
        $('#preco_sugerido').text(formatarMoeda(preco));
        
        // Atualiza o valor com desconto
        calcularValorComDescontoAdicionar();
    });
    
    // Eventos para calcular valores ao alterar quantidade, preço ou desconto (Adicionar Item)
    $('#quantidade, #preco_unitario, #desconto').on('input', function() {
        calcularValorComDescontoAdicionar();
    });
    
    // Função para calcular valor com desconto (Adicionar Item)
    function calcularValorComDescontoAdicionar() {
        const quantidade = parseFloat($('#quantidade').val()) || 0;
        const precoUnitario = parseFloat($('#preco_unitario').val()) || 0;
        const desconto = parseFloat($('#desconto').val()) || 0;
        
        const valorComDesconto = calcularValorComDesconto(quantidade, precoUnitario, desconto);
        $('#valor_com_desconto').text(formatarMoeda(valorComDesconto));
    }
    
    // Evento para editar item
    $('.btn-editar-item').on('click', function() {
        const itemId = $(this).data('item-id');
        const produtoId = $(this).data('produto-id');
        const produtoNome = $(this).data('produto-nome');
        const quantidade = $(this).data('quantidade');
        const precoUnitario = $(this).data('preco-unitario');
        const desconto = $(this).data('desconto') || 0;
        const observacoes = $(this).data('observacoes') || '';
        
        // Preenche o formulário de edição
        $('#editar_item_id').val(itemId);
        $('#info_produto_nome').text(produtoNome);
        $('#editar_quantidade').val(quantidade);
        $('#editar_preco_unitario').val(precoUnitario);
        $('#editar_desconto').val(desconto);
        $('#editar_observacoes').val(observacoes);
        
        // Atualiza a unidade de medida
        const unidade = $(`#produto_id option[value="${produtoId}"]`).data('unidade');
        $('#editar_unidade_medida').text(unidade);
        
        // Atualiza o preço original
        $('#editar_preco_original').text(formatarMoeda(precoUnitario));
        
        // Atualiza os valores
        calcularValorComDescontoEditar();
        
        // Atualiza o action do formulário
        $('#formEditarItem').attr('action', `/vendas/{{ venda.id }}/itens/${itemId}/editar`);
    });
    
    // Eventos para calcular valores ao alterar quantidade, preço ou desconto (Editar Item)
    $('#editar_quantidade, #editar_preco_unitario, #editar_desconto').on('input', function() {
        calcularValorComDescontoEditar();
    });
    
    // Função para calcular valor com desconto (Editar Item)
    function calcularValorComDescontoEditar() {
        const quantidade = parseFloat($('#editar_quantidade').val()) || 0;
        const precoUnitario = parseFloat($('#editar_preco_unitario').val()) || 0;
        const desconto = parseFloat($('#editar_desconto').val()) || 0;
        
        const valorComDesconto = calcularValorComDesconto(quantidade, precoUnitario, desconto);
        $('#editar_valor_com_desconto').text(formatarMoeda(valorComDesconto));
        $('#editar_valor_total').val('R$ ' + formatarMoeda(valorComDesconto));
    }
    
    // Evento para remover item
    $('.btn-remover-item').on('click', function() {
        const itemId = $(this).data('item-id');
        const produtoNome = $(this).data('produto-nome');
        const quantidade = $(this).data('quantidade');
        const valor = $(this).data('valor');
        const unidade = $(this).data('unidade') || 'un';
        
        // Preenche o modal de confirmação
        $('#remover_produto_nome').text(produtoNome);
        $('#remover_quantidade').text(quantidade);
        $('#remover_unidade_medida').text(unidade);
        $('#remover_valor').text(valor);
        
        // Atualiza o action do formulário
        $('#formRemoverItem').attr('action', `/vendas/{{ venda.id }}/itens/${itemId}/remover`);
    });
    
    // Validação do formulário de adicionar item
    $('#formAdicionarItem').on('submit', function(e) {
        const quantidade = parseFloat($('#quantidade').val()) || 0;
        const estoqueDisponivel = parseFloat($('#produto_id option:selected').data('estoque')) || 0;
        
        if (quantidade > estoqueDisponivel) {
            e.preventDefault();
            alert('A quantidade informada é maior que o estoque disponível.');
            return false;
        }
        
        // Mostra o indicador de carregamento
        $('#btnAdicionarItem').prop('disabled', true).html(
            '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Adicionando...'
        );
    });
    
    // Validação do formulário de editar item
    $('#formEditarItem').on('submit', function() {
        // Mostra o indicador de carregamento
        $('#btnSalvarItem').prop('disabled', true).html(
            '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Salvando...'
        );
    });
    
    // Atualiza os totais quando a página carrega
    atualizarValoresTotais();
    
    // Atualiza os totais quando o desconto geral é alterado
    $('#desconto_geral').on('input', function() {
        atualizarValoresTotais();
    });
});

// Função para resetar os campos do produto
function resetarCamposProduto() {
    $('#unidade_medida').text('---');
    $('#estoque_disponivel').text('0');
    $('#preco_unitario').val('');
    $('#preco_sugerido').text('0,00');
    $('#valor_com_desconto').text('0,00');
    $('#quantidade').val('');
    $('#desconto').val('0');
    $('#observacoes').val('');
}
