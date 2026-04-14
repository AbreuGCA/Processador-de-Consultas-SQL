SCHEMA_VENDAS = {
    "categoria": ["idCategoria", "Descricao"],
    "produto": ["idProduto", "Nome", "Descricao", "Preco", "QuantEstoque", "Categoria_idCategoria"],
    "tipocliente": ["idTipoCliente", "Descricao"],
    "cliente": ["idCliente", "Nome", "Email", "Nascimento", "Senha", "TipoCliente_idTipoCliente", "DataRegistro"],
    "tipoendereco": ["idTipoEndereco", "Descricao"],
    "endereco": ["idEndereco", "EnderecoPadrao", "Logradouro", "Numero", "Complemento", "Bairro", "Cidade", "UF", "CEP", "TipoEndereco_idTipoEndereco", "Cliente_idCliente"],
    "telefone": ["Numero", "Cliente_idCliente"],
    "status": ["idStatus", "Descricao"],
    "pedido": ["idPedido", "Status_idStatus", "DataPedido", "ValorTotalPedido", "Cliente_idCliente"],
    "pedido_has_produto": ["idPedidoProduto", "Pedido_idPedido", "Produto_idProduto", "Quantidade", "PrecoUnitario"]
}