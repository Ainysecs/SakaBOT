# 🤖 Saka Bot

A **Saka** é um bot para Discord focado em automação, gestão de servidores e ferramentas úteis para a comunidade.

---

## ⚙️ Status do Ambiente
*   **Hospedagem:** Render
*   **Versão do Python:** 3.14.3
*   **Status:** Online

---

## 🚀 Comandos da Saka

### ⚙️ Administração (Sistema)
*Painel de controle técnico para gerir o núcleo do bot. Permite atualizar configurações em tempo real e monitorar o desempenho dos módulos.*

| Comando | Descrição | Modo |
| :---: | :--- | :---: |
| `/sync` | Sincronização e limpeza do cache. | `⚡ Hybrid` |
| `/reload` | Recarrega módulos (Cogs). | `⚡ Hybrid` |
| `/cogs` | Monitoramento dos módulos. | `⚡ Hybrid` |
| `/stats` | Performance e uptime. | `⚡ Hybrid` |

### 🛡️ Moderação (Servidor)
*Ferramentas essenciais para a staff manter a comunidade limpa, organizada e segura, agilizando as tarefas diárias de moderação.*

| Comando | Descrição | Modo |
| :---: | :--- | :---: |
| `/clear` | Limpeza de histórico. | `Slash Only` |
| `/member` | Gestão de membros (list, add, remove, edit). | `Slash Only` |

### 🧩 Extras & Utilidades
*Sistemas auxiliares, integrações de APIs externas e painéis interativos criados para facilitar o suporte e o dia a dia dos membros.*

| Comando | Descrição | Modo |
| :---: | :--- | :---: |
| `/help` | Lista de comandos interativa. | `⚡ Hybrid` |
| `/support` | Canal de atendimento (SAC). | `Slash Only` |
| `/gcmd` | Comandos gerais/Painel fixo. | `Slash Only` |
| `/rmural` | Remoção/gerenciamento de mural. | `Slash Only` |

### 🌐 Área Pública (Comunitários)
*Recursos interativos e de entretenimento focados no utilizador final.*

| Comando | Descrição | Modo |
| :---: | :--- | :---: |
| `/ai` | Interação com IA (texto/imagem). | `⚡ Hybrid` |

---

> ℹ️ **Nota de Compatibilidade:** 
> - Comandos marcados com `⚡ Hybrid` aceitam prefixo `!` e `slash (/)`. 
> - Comandos marcados como `Slash Only` funcionam **exclusivamente** através de `slash (/)`.

---

## 🛠️ Como Instalar

> ℹ️ **Pré-requisito:** Recomenda-se o uso do **Python 3.14.x** para garantir a compatibilidade com todas as dependências.

1. Clone o repositório:
```bash
git clone https://github.com/Ainysecs/SakaBOT.git
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Configure as credenciais (.env): 
   
   Crie uma cópia do arquivo `.env.example` (localizado dentro da pasta `config`), remova o .example do nome e mova-o para a raiz do projeto.

Se preferir fazer isso rapidamente pelo terminal, execute:
```bash
cp config/.env.example .env
```

4. Inicie o bot:
```bash
python3 saka.py
```

---

## ❓ Problemas ou Dúvidas?
   Se você tiver dificuldades com as credenciais do Google Sheets, variáveis no Render ou outras coisas, consulte o [Guia de Resolução de Problemas](TROUBLESHOOTING.md) para ver as instruções detalhadas.

---

# 📖 Changelog (v2.0)
  Aqui sempre estarão as changelogs mais recentes. [Dê uma olhada!](CHANGELOG.md)

---

# 📝 Contribuição

Sinta-se à vontade para abrir uma Issue ou enviar um Pull Request para melhorias!

