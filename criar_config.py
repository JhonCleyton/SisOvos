import json

config = {
    "nome_empresa": "SisOvos",
    "email_contato": "contato@sisovos.com",
    "itens_por_pagina": 10,
    "manutencao_ativa": False,
    "notificar_erros": True,
    "tema": "claro",
    "timezone": "America/Sao_Paulo",
    "idioma": "pt_BR"
}

with open('instance/config_sistema.json', 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=4, ensure_ascii=False)
