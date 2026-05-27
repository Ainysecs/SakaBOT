# ⚠️ Resolução de Problemas & Avisos Importantes (Saka Bot)

Este guia centraliza configurações avançadas, comportamentos de hospedagem e soluções rápidas para erros conhecidos.
<div id="top"></div>

---

## 📌 Sumário
* [📊 Integração com Google Sheets](#-integração-com-google-sheets)
* [🚀 Hospedagem no Render](#-hospedagem-no-render)
* [🛑 Erros Comuns](#-erros-comuns)
    * [Falha Crítica ao carregar módulo (AttributeError)](#1-attributeerror)
    * [ModuleNotFoundError](#2-modulenotfounderror)
    * [discord.errors.LoginFailure](#3-discorderrorsloginfailure)
    * [Interaction Already Acknowledged](#4-interaction-already-acknowledged)
    * [Ignoring Exception in App Commands Tree](#5-ignoring-exception-in-app-commands-tree)
---

## 📊 Integração com Google Sheets

> [!CAUTION]
> **SEGURANÇA DE CHAVES:** Nunca envie o arquivo `credenciais.json` para o GitHub. Se o Google detectar uma chave exposta, ela será revogada instantaneamente.

**Como configurar corretamente:**
1. Abra o arquivo `.json` no seu computador.
2. Copie todo o conteúdo (a estrutura de chaves `{...}`).
3. No seu `.env` ou painel da hospedagem, cole o bloco como uma string de linha única:
   * *Exemplo:* `GOOGLE_CREDENTIALS={"type": "service_account", ...}`

[ 🏠 Voltar ao Sumário ](#top)
---

## 🚀 Hospedagem no Render

### 1. Sistemas de Arquivos Efêmeros
O Render limpa o armazenamento local a cada reinicialização ou *deploy*.
* **Regra:** Não use armazenamento local para dados persistentes (logs `.txt` ou `.sqlite`).
* **Solução:** Utilize bancos de dados externos ou a API do Google Sheets.

### 2. Forçar Versão do Python
Se houver incompatibilidade de bibliotecas, force a versão no painel do Render:
1. Vá em **Environment** -> **Add Environment Variable**.
2. **Key:** `PYTHON_VERSION` | **Value:** `3.14.3`

[ 🏠 Voltar ao Sumário ](#top)
---

## 🛑 Erros Comuns

### 1. `AttributeError`
**Mensagem de Erro:** 
```text
`Extension '{modulo}' raised an error: AttributeError: Configuração '{caminho}' não existe.`
```

* **Causa:** O código tentou acessar uma chave de configuração que não existe no seu arquivo `.env` ou o arquivo de config não foi carregado.

* **Solução:** 
    - Verifique se você renomeou o `.env.example` para `.env`.
    - Confira se a variável mencionada no erro está presente no arquivo.
    - Verifique se o arquivo está no local correto ou se o caminho dentro do código do módulo está de acordo.
    - Reinicie o bot para garantir o carregamento das novas variáveis.

### 2. `ModuleNotFoundError`
* **Causa:** Dependência não instalada no ambiente.

* **Solução:** Execute o comando abaixo. Se estiver usando `venv`, certifique-se de que ele está ativado.
```bash
`pip install -r requirements.txt`.
```

### 3. `discord.errors.LoginFailure`
* **Causa:** Token do bot inválido ou expirado.

* **Solução:** Gere um novo token no [Discord Developer Portal](https://discord.com/developers/applications) e atualize a variável `DISCORD_TOKEN`.

### 4. `Interaction Already Acknowledged`
Mensagem de Erro:
```text
discord.errors.HTTPException: 400 Bad Request (error code: 40060): Interaction has already been acknowledged.
```
* **Causa:** Este erro ocorre quando o bot tenta responder a uma mesma interação (como um Slash Command, botão ou menu de seleção) mais de uma vez usando métodos de resposta inicial (ex: interaction.response.send_message()), ou quando tenta responder a uma interação que já foi deferida (interaction.response.defer()). A API do Discord permite apenas uma resposta inicial por interação.

* **Solução:** Respostas Subsequentes: Se você precisa enviar mais de uma mensagem em resposta a um único comando, utilize interaction.followup.send() para todas as mensagens após a primeira.
Processos Demorados: Se o comando realizar tarefas que demoram mais de 3 segundos (limite do Discord), use await interaction.response.defer() no início e conclua com await interaction.followup.send().

* **Revisão de Fluxo:** Verifique se não há condicionais (blocos if/else) no seu código executando acidentalmente mais de um interaction.response durante a mesma execução.

### 5. Ignoring Exception in App Commands Tree
Mensagem de Erro:
```text
[ERROR] discord.app_commands.tree: Ignoring exception in {autocomplete/command} for '{comando}' (Guild: [...], User: [...])
```
* **Causa:** Este é um erro genérico que indica que uma exceção (bug ou falha lógica) não tratada ocorreu durante a execução de um comando de aplicação (Slash Command/Context Menu) ou durante uma função de autocomplete. A biblioteca discord.py captura a falha para evitar que o bot inteiro trave, loga esse aviso e, consequentemente, o comando falha silenciosamente para o usuário.
* **Solução:** Analisar o Traceback: Logo abaixo dessa linha no seu terminal, haverá um traceback (rastreamento) detalhado. Leia o último erro desse bloco para identificar exatamente qual linha do seu código e qual exceção específica (ex: KeyError, ValueError, AttributeError) causou a falha.

* **Tratamento de Erros Global:** Implemente um manipulador global de erros para a sua command tree usando tree.on_error para capturar falhas de forma elegante e avisar o usuário que algo deu errado, em vez de deixá-lo sem resposta.
Tratamento de Erros Local: Utilize o decorador @app_commands.command.error na função do comando específico caso a falha seja esperada (como falta de permissões ou argumentos inválidos).

[ 🏠 Voltar ao Sumário ](#top)
---

