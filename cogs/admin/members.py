import os
import json
import yaml
import discord
import asyncio
import gspread
from discord import app_commands
from discord.ext import commands

# ==========================================
# SISTEMA DE PAGINAÇÃO POR BOTÕES
# ==========================================
class PaginatorView(discord.ui.View):
    """
    Paginador de uso efêmero. Controla as páginas individualmente
    para cada usuário sem conflito global.
    """
    def __init__(self, embeds: list[discord.Embed]):
        super().__init__(timeout=180)  #3 minutos
        self.embeds = embeds
        self.current_page = 0
        self._update_buttons()

    def _update_buttons(self):
        """Desabilita botões de forma inteligente dependendo da página."""
        if len(self.embeds) <= 1:
            self.clear_items()
            return
        self.previous_page.disabled = (self.current_page == 0)
        self.next_page.disabled = (self.current_page == len(self.embeds) - 1)

    @discord.ui.button(label="◀ Anterior", style=discord.ButtonStyle.grey)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            self._update_buttons()
            await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)
        else:
            await interaction.response.defer()

    @discord.ui.button(label="Próximo ▶", style=discord.ButtonStyle.grey)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < len(self.embeds) - 1:
            self.current_page += 1
            self._update_buttons()
            await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)
        else:
            await interaction.response.defer()


# ==========================================
# VIEW PERSISTENTE DO MURAL PÚBLICO
# ==========================================
class PersistentMemberMuralView(discord.ui.View):
    """
    View fixa do canal. Nunca expira (timeout=None) e resiste a reboots
    do bot por utilizar custom_id fixo.
    """
    def __init__(self, cog: commands.Cog):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(label="Ver Lista de Membros", style=discord.ButtonStyle.blurple, custom_id="mural_member_list_btn_v1", emoji="👥")
    async def view_list(self, interaction: discord.Interaction, button: discord.ui.Button):
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            
            embeds = await self.cog.gerar_embeds_membros()
            
            if not embeds:
                await interaction.followup.send("🌵 A lista de membros está vazia no momento.", ephemeral=True)
                return

            
            view = PaginatorView(embeds)
            await interaction.followup.send(embed=embeds[0], view=view, ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(f"⚠️ Erro ao carregar o painel dinâmico: `{e}`", ephemeral=True)


# ==========================================
# COG PRINCIPAL DE GERENCIAMENTO
# ==========================================
class GerenciadorMembros(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.gc = None
        self.sh = None
        self.ws = None

        self._cache = []
        self._cache_carregado = False

        self.mascote_url = "https://i.pinimg.com/736x/30/e1/1c/30e11c78a6661cd42dd1f5390aa4bbd3.jpg"

        self.locales = self._load_locales()

    def _load_locales(self):
        """Carrega as falas do arquivo YAML especificado."""
        caminho = "config/locales/pt_br/admin/members.yaml"
        if os.path.exists(caminho):
            with open(caminho, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        else:
            print(f"[AVISO] Arquivo de locale não encontrado em: {caminho}")
            return {"messages": {}}

    async def cog_load(self):
        """Roda automaticamente quando o módulo liga, em background."""
        self.bot.add_view(PersistentMemberMuralView(self))

        try:
            google_creds_json = os.environ.get("GOOGLE_CREDENTIALS")

            if not google_creds_json:
                print("[SISTEMA MEMBERS ERRO] A variável GOOGLE_CREDENTIALS não foi encontrada no ambiente!")
                return

            credenciais_dict = json.loads(google_creds_json)

            self.gc = await asyncio.to_thread(gspread.service_account_from_dict, credenciais_dict)
            self.sh = await asyncio.to_thread(self.gc.open, 'NerdsSEDEXO')
            self.ws = await asyncio.to_thread(self.sh.worksheet, 'Membros')

            await self._atualizar_cache()
            print("[SISTEMA MEMBERS] Conexão com Google Sheets estabelecida e cache alimentado!")
        except Exception as e:
            print(f"[SISTEMA MEMBERS ERRO] Falha crítica ao iniciar conexão: {e}")

    async def _atualizar_cache(self):
        """Baixa os dados mais recentes da planilha para a memória (Full Sync)."""
        if self.ws:
            self._cache = await asyncio.to_thread(
                self.ws.get_all_records, 
                expected_headers=['MEMBRO', 'FUNCAO', 'DESCRICAO']
            )
            self._cache_carregado = True

    async def gerar_embeds_membros(self) -> list[discord.Embed]:
        """Processa o cache interno e gera a lista estruturada de Embeds paginados."""
        if not self.ws:
            raise RuntimeError("A conexão com a planilha do Google Sheets está inativa.")

        if not self._cache_carregado or not self._cache:
            await self._atualizar_cache()

        registros = self._cache
        if not registros:
            return []

        embeds = []
        titulo = self.locales.get('messages', {}).get('list_title', "🤓 Os Nerds do Grupo")

        current_embed = discord.Embed(title=titulo, color=0x2b2d31)
        current_embed.set_thumbnail(url=self.mascote_url)

        field_count = 0
        for linha in registros:
            nome = linha.get('MEMBRO', 'Desconhecido')
            funcao = linha.get('FUNCAO', 'Sem Função')
            desc = linha.get('DESCRICAO', '...')

            if field_count >= 4:
                embeds.append(current_embed)
                current_embed = discord.Embed(title=f"{titulo} (Continuação)", color=0x2b2d31)
                current_embed.set_thumbnail(url=self.mascote_url)
                field_count = 0

            current_embed.add_field(
                name=f"👤 {nome}", 
                value=f"**{funcao}**\n*{desc}*\n\u200b", 
                inline=False
            )
            field_count += 1

        embeds.append(current_embed)

        for i, emb in enumerate(embeds):
            emb.set_footer(text=f"Página {i+1}/{len(embeds)} • SAKAnagem Enterprise • 2026")

        return embeds

    member_group = app_commands.Group(
        name="member", 
        description="Gerenciamento da Elite SEDEXO.",
        default_permissions=discord.Permissions(manage_guild=True)
    )

    # ---------------------------------------------------------
    # COMANDO: /member list
    # ---------------------------------------------------------
    @member_group.command(name="list", description="[ADMIN] Envia o mural oficial fixo de membros para este canal.")
    async def list(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)

        if not self.ws:
            return await interaction.followup.send("❌ Erro crítico: Sem conexão ativa com o banco de dados.", ephemeral=True)

        try:
            embed_mural = discord.Embed(
                title="🏆 Galeria de Membros Oficiais",
                description="Clique no botão abaixo para consultar a lista de membros e suas respectivas funções na **Elite SEDEXO**.\n\n*Nota: O painel abrirá de forma individual e privada para você.*",
                color=0x2b2d31
            )
            embed_mural.set_image(url="https://i.pinimg.com/originals/26/3e/3f/263e3f082246cb9cc522bedf09ccb80c.gif")
            embed_mural.set_footer(text="Painel de Consulta Operacional • Clique abaixo")

            view = PersistentMemberMuralView(self)
            await interaction.followup.send(embed=embed_mural, view=view)

        except Exception as e:
            await interaction.followup.send(f"⚠️ Erro ao implantar o mural: {e}", ephemeral=True)

    # ---------------------------------------------------------
    # COMANDOS DE MANUTENÇÃO
    # ---------------------------------------------------------
    @member_group.command(name="add", description="[ADMIN] Adiciona um novo membro.")
    async def add(self, interaction: discord.Interaction, nome: str, funcao: str, descricao: str):
        await interaction.response.defer(ephemeral=True)

        try:
            linha_insercao = [nome, funcao, descricao]
            await asyncio.to_thread(self.ws.append_row, linha_insercao)

            novo_registro = {'MEMBRO': nome, 'FUNCAO': funcao, 'DESCRICAO': descricao}
            self._cache.append(novo_registro)
            self._cache_carregado = True

            asyncio.create_task(self._atualizar_cache())
            await interaction.followup.send(f"✅ **{nome}** foi enviado para o Mural da Vergonha.")

        except Exception as e:
            erro_msg = str(e).lower()
            if "validation" in erro_msg or "violates" in erro_msg or "400" in erro_msg:
                await interaction.followup.send("🚨 **Acesso Negado!** A planilha rejeitou a entrada. Provavelmente o limite máximo de membros foi atingido.")
            else:
                await interaction.followup.send(f"❌ Ocorreu um erro inesperado: `{e}`")

    @member_group.command(name="remove", description="[ADMIN] Remove um membro.")
    async def remove(self, interaction: discord.Interaction, nome: str):
        await interaction.response.defer(ephemeral=True)

        celula = await asyncio.to_thread(self.ws.find, nome, in_column=1)
        if celula:
            await asyncio.to_thread(self.ws.delete_rows, celula.row)
            self._cache = [r for r in self._cache if str(r.get('MEMBRO')).lower() != nome.lower()]

            asyncio.create_task(self._atualizar_cache())
            await interaction.followup.send(f"🗑️ **{nome}** removido com sucesso e cache limpo.")
        else:
            await interaction.followup.send("❌ Membro não encontrado.")

    @member_group.command(name="edit", description="[ADMIN] Edita um membro.")
    async def edit(self, interaction: discord.Interaction, nome_atual: str, novo_nome: str = None, nova_funcao: str = None, nova_descricao: str = None):
        await interaction.response.defer(ephemeral=True)

        celula = await asyncio.to_thread(self.ws.find, nome_atual, in_column=1)
        if not celula: 
            return await interaction.followup.send("❌ Não achei esse nerd.")

        old = next((r for r in self._cache if str(r.get('MEMBRO')).lower() == nome_atual.lower()), {})

        final_n = novo_nome or nome_atual
        final_f = nova_funcao or old.get('FUNCAO', '')
        final_d = nova_descricao or old.get('DESCRICAO', '')

        try:
            await asyncio.to_thread(self.ws.update_cell, celula.row, 1, final_n)
            await asyncio.to_thread(self.ws.update_cell, celula.row, 2, final_f)
            await asyncio.to_thread(self.ws.update_cell, celula.row, 3, final_d)

            for r in self._cache:
                if str(r.get('MEMBRO')).lower() == nome_atual.lower():
                    r['MEMBRO'] = final_n
                    r['FUNCAO'] = final_f
                    r['DESCRICAO'] = final_d
                    break

            asyncio.create_task(self._atualizar_cache())
            await interaction.followup.send(f"📝 Dados de **{nome_atual}** atualizados no cache e na nuvem.")

        except Exception as e:
            await interaction.followup.send(f"⚠️ Erro ao atualizar a planilha: `{e}`")

async def setup(bot: commands.Bot):
    await bot.add_cog(GerenciadorMembros(bot))
