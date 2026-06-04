import discord
from discord.ext import commands
from discord import app_commands
import logging
import traceback
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class EphemeralPaginator(discord.ui.View):
    def __init__(self, pages: list[dict], embed_base: dict):
        super().__init__(timeout=300.0) # Expira em 5 minutos
        self.pages = pages
        self.embed_base = embed_base
        self.current_page = 0
        
        if not self.pages or len(self.pages) <= 1:
            self.next_button.disabled = True
            
        self._update_button_states()

    def _parse_color(self, color_str: str) -> int:
        try:
            return int(str(color_str).replace("#", ""), 16)
        except (ValueError, TypeError):
            return 0x2b2d31

    def create_embed(self) -> discord.Embed:
        page_data = self.pages[self.current_page]
        color_int = self._parse_color(self.embed_base.get("color", "2b2d31"))

        embed = discord.Embed(
            title=self.embed_base.get("title", "Comandos"),
            url=self.embed_base.get("url"),
            description=self.embed_base.get("description", ""),
            color=color_int
        )
        
        if thumbnail := self.embed_base.get("thumbnail"):
            embed.set_thumbnail(url=thumbnail)

        commands_format = "\n".join(page_data.get("commands", []))
        embed.add_field(
            name=page_data.get("title", f"Página {self.current_page + 1}"), 
            value=commands_format or "Nenhum comando encontrado.", 
            inline=False
        )
        
        footer_text = self.embed_base.get('footer', 'Sistema de Ajuda')
        embed.set_footer(text=f"{footer_text} | Página {self.current_page + 1}/{len(self.pages)}")

        return embed

    def _update_button_states(self):
        self.back_button.disabled = (self.current_page == 0)
        self.next_button.disabled = (self.current_page == len(self.pages) - 1)

    @discord.ui.button(label="◀ Voltar", style=discord.ButtonStyle.grey)
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page -= 1
        self._update_button_states()
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    @discord.ui.button(label="Avançar ▶", style=discord.ButtonStyle.blurple)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += 1
        self._update_button_states()
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item) -> None:
        logger.error(f"Erro no Paginador Efêmero: {error}\n{traceback.format_exc()}")
        if not interaction.response.is_done():
            await interaction.response.send_message("❌ Ocorreu um erro ao trocar de página.", ephemeral=True)

class PersistentMuralView(discord.ui.View):
    def __init__(self, config: dict):
        super().__init__(timeout=None)
        self.config = config

    @discord.ui.button(label="Comandos Brawl Tools", style=discord.ButtonStyle.green, custom_id="btn_mural_bt", emoji="🤖")
    async def btn_brawl_tools(self, interaction: discord.Interaction, button: discord.ui.Button):
        bt_config = self.config.get("brawl_tools", {})
        pages = bt_config.get("pages", [])
        embed_base = bt_config.get("embed_base", {})

        if not pages:
            await interaction.response.send_message("⚠️ Nenhuma página de comando configurada para esta sessão.", ephemeral=True)
            return

        view = EphemeralPaginator(pages=pages, embed_base=embed_base)
        await interaction.response.send_message(embed=view.create_embed(), view=view, ephemeral=True)

    @discord.ui.button(label="Ver Comandos Gerais", style=discord.ButtonStyle.primary, custom_id="btn_mural_gerais", emoji="⚙️")
    async def btn_gerais(self, interaction: discord.Interaction, button: discord.ui.Button):
        gerais_config = self.config.get("gerais", {})
        pages = gerais_config.get("pages", [])
        embed_base = gerais_config.get("embed_base", {})

        if not pages:
            await interaction.response.send_message("⚠️ Nenhuma página de comando configurada para esta sessão.", ephemeral=True)
            return

        view = EphemeralPaginator(pages=pages, embed_base=embed_base)
        await interaction.response.send_message(embed=view.create_embed(), view=view, ephemeral=True)
        
    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item) -> None:
        logger.error(f"Erro no Mural Fixo: {error}\n{traceback.format_exc()}")
        if not interaction.response.is_done():
            await interaction.response.send_message("❌ Ocorreu um erro ao carregar esta seção.", ephemeral=True)

class SystemCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
        self.caminho_arquivo = "config/locales/pt_br/general/config_commands.json"
        self.config = self._carregar_json()

    def _carregar_json(self) -> dict:
        """Função auxiliar para ler o JSON e evitar quebrar se o arquivo não existir"""
        try:
            with open(self.caminho_arquivo, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Falha ao carregar arquivo de configuração do mural: {e}")
            return {}

    async def cog_load(self):
        """Registra o mural na inicialização para resistir a reboots"""
        self.bot.add_view(PersistentMuralView(self.config))

    @app_commands.command(name="gcmd", description="[ADMIN] Instala o mural de comandos interativo neste canal.")
    @app_commands.default_permissions(manage_guild=True)
    async def setup_mural(self, interaction: discord.Interaction):
        
        embed_mural = discord.Embed(
            title="Central de Comandos",
            description="Selecione abaixo qual lista de comandos você deseja consultar. O menu será aberto de forma privada apenas para você.",
            color=0x2b2d31 
        )
        embed_mural.set_thumbnail(url="https://brawltools.net/img/brand/bt_logo4.webp")
        view = PersistentMuralView(self.config)

        await interaction.channel.send(embed=embed_mural, view=view)
        
        await interaction.response.send_message("✅ Mural instalado com sucesso neste canal!", ephemeral=True)

    @app_commands.command(name="rmural", description="[ADMIN] Recarrega os textos do mural do JSON sem reiniciar o bot.")
    @app_commands.default_permissions(manage_guild=True)
    async def reload_mural(self, interaction: discord.Interaction):
        
        try:
            with open(self.caminho_arquivo, "r", encoding="utf-8") as f:
                nova_config = json.load(f)
                
            self.config = nova_config
            
            self.bot.add_view(PersistentMuralView(self.config))
            
            await interaction.response.send_message("✅ **JSON recarregado com sucesso!** O mural já está usando as novas configurações.", ephemeral=True)
            
        except FileNotFoundError:
            await interaction.response.send_message(f"❌ **Erro:** Arquivo não encontrado em `{self.caminho_arquivo}`. Ajuste o caminho no código.", ephemeral=True)
        except json.JSONDecodeError as e:
            await interaction.response.send_message(f"❌ **Erro de Sintaxe no JSON:** Verifique se você não esqueceu de fechar alguma aspa ou vírgula.\nDetalhe: `{e}`", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ **Erro inesperado ao recarregar:** {e}", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(SystemCommands(bot))
