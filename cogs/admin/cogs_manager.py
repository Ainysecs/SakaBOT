import logging
import discord
from discord import app_commands
from discord.ext import commands
from pathlib import Path
from collections import defaultdict

logger = logging.getLogger('saka.cogs.cogs_manager')

class CogsManager(commands.Cog):

    MAX_EMBED_FIELD_LENGTH = 1024

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.cogs_dir = Path("cogs")

    def _get_msg(self, path: str) -> str:
        try:
            dados = self.bot.config.locales_pt_br_admin_cogs_manager

            for chave in path.split('.'):
                dados = dados[chave]

            return str(dados)
        except (AttributeError, KeyError, TypeError) as e:
            logger.error(f"Falha ao recuperar string no cogs_manager para o caminho '{path}': {e}")
            return f"❌ [Erro de Localização: {path}]"

    @commands.hybrid_command(name="cogs", hidden=True, description="[DEV] Painel detalhado com o status de todos os módulos")
    @app_commands.default_permissions(administrator=True)
    @commands.is_owner()
    async def cogs(self, ctx: commands.Context) -> None:
        await ctx.defer(ephemeral=True)

        if not self.cogs_dir.exists() or not self.cogs_dir.is_dir():
            logger.warning("O diretório 'cogs' não foi encontrado durante a execução do comando /cogs.")
            await ctx.send(self._get_msg("errors.dir_not_found"), ephemeral=True)
            return

        carregados = set(self.bot.extensions.keys())
        categorias: dict[str, list[str]] = defaultdict(list)
        total_online = 0
        total_encontrados = 0

        for path in self.cogs_dir.rglob("*.py"):
            if path.name == "__init__.py":
                continue

            modulo = ".".join(path.with_suffix("").parts)
            nome_pasta = path.parent.name.capitalize() if path.parent != self.cogs_dir else "Raiz"

            total_encontrados += 1
            if modulo in carregados:
                categorias[nome_pasta].append(self._get_msg("status.online").format(modulo=modulo))
                total_online += 1
            else:
                categorias[nome_pasta].append(self._get_msg("status.offline").format(modulo=modulo))

        embed = discord.Embed(
            title=self._get_msg("embeds.title"),
            color=discord.Color.blurple(),
            timestamp=discord.utils.utcnow()
        )

        if not categorias:
            embed.description = self._get_msg("errors.no_categories")
        else:
            mensagem_corte = self._get_msg("errors.corte_lista")
            for pasta, modulos in categorias.items():
                valor_field = ""

                for mod in modulos:
                    if len(valor_field) + len(mod) + len(mensagem_corte) + 1 > self.MAX_EMBED_FIELD_LENGTH:
                        valor_field += mensagem_corte
                        break
                    valor_field += f"{mod}\n"

                nome_field = self._get_msg("embeds.folder").format(pasta=pasta)
                embed.add_field(name=nome_field, value=valor_field.strip(), inline=False)

        footer_text = self._get_msg("embeds.footer").format(online=total_online, total=total_encontrados)
        embed.set_footer(text=footer_text)

        await ctx.send(
            content=self._get_msg("responses.relatorio_sucesso"),
            embed=embed,
            ephemeral=True
        )

    @cogs.error
    async def cogs_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        if isinstance(error, commands.NotOwner):
            await ctx.send(self._get_msg("errors.not_owner"), ephemeral=True)
        else:
            logger.error(f"Erro inesperado no comando /cogs disparado por {ctx.author}: {error}", exc_info=True)

            err_msg = self._get_msg("errors.generic_error")
            if ctx.interaction and ctx.interaction.response.is_done():
                await ctx.interaction.followup.send(err_msg, ephemeral=True)
            else:
                await ctx.send(err_msg, ephemeral=True)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(CogsManager(bot))
