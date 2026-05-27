import discord
from discord.ext import commands
from discord import app_commands
import logging
import traceback

logger = logging.getLogger(__name__)

class HelpDropdown(discord.ui.Select):
    def __init__(self, config_help: dict, bot_user: discord.ClientUser):
        self.config_help = config_help
        self.categorias = config_help.get("categorias", {})
        self.bot_user = bot_user

        options = []
        for key, dados in self.categorias.items():
            nome_completo = dados.get("nome", key)
            
            # Extrai o emoji com seguranç
            emoji = nome_completo.split()[0] if " " in nome_completo else None
            label = nome_completo.replace(emoji, "").strip() if emoji else nome_completo
            label = label[:100] 

            options.append(discord.SelectOption(
                label=label, 
                value=key,
                emoji=emoji, 
                description=f"Ver comandos de {label}"[:100]
            ))

        super().__init__(
            placeholder="Selecione uma categoria de comandos...",
            min_values=1,
            max_values=1,
            options=options[:25]
        )

    async def callback(self, interaction: discord.Interaction):
        categoria_key = self.values[0]
        dados_cat = self.categorias.get(categoria_key, {})
        msgs = self.config_help.get("messages", {})

        embed = discord.Embed(
            title=dados_cat.get("nome", "Categoria Desconhecida"),
            description=f"{dados_cat.get('descricao', '')}\n\n{msgs.get('hybrid_note', '')}",
            color=discord.Color.blurple()
        )

        comandos_lista = dados_cat.get("comandos", [])
        if comandos_lista:
            linhas = [f"**{item.get('cmd', '?')}** - {item.get('desc', 'Sem descrição')}" for item in comandos_lista]
            embed.add_field(name="Comandos Disponíveis", value="\n".join(linhas), inline=False)
        else:
            embed.add_field(name="Comandos Disponíveis", value="Nenhum comando encontrado aqui.", inline=False)

        icone_bot = self.bot_user.display_avatar.url if self.bot_user.display_avatar else None
        embed.set_footer(text=msgs.get("footer", "Sistema de Ajuda"), icon_url=icone_bot)

        await interaction.response.edit_message(embed=embed)


class HelpView(discord.ui.View):
    def __init__(self, config_help: dict, bot_user: discord.ClientUser):
        super().__init__(timeout=120)
        self.dropdown = HelpDropdown(config_help, bot_user)
        self.add_item(self.dropdown)
        self.message: discord.Message = None

    async def on_timeout(self):
        """Desativa o dropdown visualmente quando o tempo expira."""
        self.dropdown.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass

    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item):
        logger.error(f"Erro no Dropdown de Ajuda: {error}\n{traceback.format_exc()}")
        if not interaction.response.is_done():
            await interaction.response.send_message("❌ Ocorreu um erro ao carregar esta categoria.", ephemeral=True)


class HelpCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        if self.bot.get_command("help"):
            self.bot.remove_command("help")

    def _gerar_embed_categoria(self, config_help: dict, categoria_key: str) -> discord.Embed:
        """Gera o embed direto para uma categoria específica."""
        dados_cat = config_help.get("categorias", {}).get(categoria_key, {})
        msgs = config_help.get("messages", {})

        embed = discord.Embed(
            title=dados_cat.get("nome", "Categoria"),
            description=f"{dados_cat.get('descricao', '')}\n\n{msgs.get('hybrid_note', '')}",
            color=discord.Color.blurple()
        )
        
        comandos_lista = dados_cat.get("comandos", [])
        if comandos_lista:
            linhas = [f"**{item.get('cmd', '?')}** - {item.get('desc', 'Sem descrição')}" for item in comandos_lista]
            embed.add_field(name="Comandos Disponíveis", value="\n".join(linhas), inline=False)

        icone_bot = self.bot.user.display_avatar.url if self.bot.user.display_avatar else None
        embed.set_footer(text=msgs.get("footer", "Sistema de Ajuda"), icon_url=icone_bot)
        return embed

    # ==========================================
    # AUTOCOMPLETE LENDO DIRETO DO JSON
    # ==========================================
    async def categoria_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        try:
            config_help = self.bot.config.locales_pt_br_help
            categorias = config_help.get("categorias", {})
        except AttributeError:
            return []

        choices = []
        for key, dados in categorias.items():
            nome = dados.get("nome", key)
            if current.lower() in nome.lower() or current.lower() in key.lower():
                label_limpo = nome.split()[1] if " " in nome else nome
                choices.append(app_commands.Choice(name=label_limpo, value=key))
                
        return choices[:25]

    # ==========================================
    # COMANDO HÍBRIDO
    # ==========================================
    @commands.hybrid_command(name="help", description="Mostra o painel interativo de comandos da Saka.", aliases=["ajuda"])
    @app_commands.describe(categoria="Deseja ir direto para uma categoria específica?")
    @app_commands.autocomplete(categoria=categoria_autocomplete)
    async def help_command(self, ctx: commands.Context, categoria: str = None):
        
        if not hasattr(self.bot, 'config') or not hasattr(self.bot.config, 'locales_pt_br_help'):
            await ctx.send("❌ As configurações de ajuda ainda não foram carregadas no bot.", ephemeral=True)
            return

        config_help = self.bot.config.locales_pt_br_help
        msgs = config_help.get("messages", {})

        # Fluxo 1: Usuário pediu uma categoria específica direto
        if categoria:
            categoria_key = categoria.lower()
            if categoria_key in config_help.get("categorias", {}):
                embed = self._gerar_embed_categoria(config_help, categoria_key)
                
                if ctx.interaction:
                    await ctx.send(embed=embed, ephemeral=True)
                else:
                    msg = await ctx.send(embed=embed, delete_after=120)
                    try: await ctx.message.delete()
                    except discord.Forbidden: pass
                return
            else:
                erro_msg = msgs.get("invalid_category", "❌ Categoria '{cat}' inválida.").replace("{cat}", categoria)
                await ctx.send(erro_msg, ephemeral=True, delete_after=10)
                return

        # Fluxo 2: Menu interativo padrão
        embed_inicial = discord.Embed(
            title=msgs.get("main_title", "Central de Ajuda"),
            description=msgs.get("main_description", "Selecione uma categoria abaixo."),
            color=discord.Color.blurple()
        )
        icone_bot = self.bot.user.display_avatar.url if self.bot.user.display_avatar else None
        embed_inicial.set_thumbnail(url=icone_bot)

        view = HelpView(config_help, self.bot.user)

        if ctx.interaction:
            await ctx.send(embed=embed_inicial, view=view, ephemeral=True)
            try:
                view.message = await ctx.interaction.original_response()
            except discord.HTTPException:
                pass 
        else:
            msg = await ctx.send(embed=embed_inicial, view=view, delete_after=120)
            view.message = msg
            try:
                await ctx.message.delete()
            except discord.Forbidden:
                pass

async def setup(bot: commands.Bot):
    await bot.add_cog(HelpCog(bot))
