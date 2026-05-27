import logging
import discord
import datetime
from discord import app_commands
from discord.ext import commands

logger = logging.getLogger('saka.cogs.clear')

class Util(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="clear", description="[MOD] Faz a Saka limpar a bagunça do chat.")
    @app_commands.describe(amount="Quantas mensagens você quer que eu apague? (1-100)")
    @app_commands.guild_only() 
    @app_commands.default_permissions(manage_messages=True) 
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.checks.bot_has_permissions(manage_messages=True, read_message_history=True)
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: i.user.id)
    async def clear(self, interaction: discord.Interaction, amount: app_commands.Range[int, 1, 100] = 20):

        await interaction.response.defer(ephemeral=True)

        if not interaction.guild or not isinstance(interaction.channel, discord.abc.Messageable):
            await interaction.followup.send("❌ Eu só posso limpar mensagens em canais de texto de servidores, baka!", ephemeral=True)
            return

        limite_14_dias = discord.utils.utcnow() - datetime.timedelta(days=14)

        try:
            deleted = await interaction.channel.purge(
                limit=amount,
                check=lambda m: m.created_at > limite_14_dias
            )

            if len(deleted) == 0:
                await interaction.followup.send(
                    "🙄 Não encontrei nenhuma mensagem recente para apagar. Lembre-se que eu não toco em lixo com mais de 14 dias!",
                    ephemeral=True
                )
                return

            await interaction.followup.send(
                f"🧹 *Ugh*... Terminei de limpar a bagunça de vocês. Apaguei **{len(deleted)}** mensagens.\n"
                f"E não se acostume com isso, seu folgado! 💅",
                ephemeral=True
            )
            logger.info(f"🧹 Faxina concluída: {len(deleted)} msgs em #{interaction.channel.name} por {interaction.user.name}")

        except Exception as e:
            logger.error(f"Erro crítico no clear: {e}", exc_info=True)
            await interaction.followup.send(
                "❌ Um erro interno e bizarro aconteceu enquanto eu tentava limpar o chat.",
                ephemeral=True
            )

    # === TRATAMENTO DE ERROS ===
    @clear.error
    async def clear_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        msg = "❌ Ops! Algo deu errado ao tentar executar este comando."

        if isinstance(error, app_commands.MissingPermissions):
            msg = "💢 Quem você pensa que é? Você não tem permissão para me dar ordens de limpeza! Hmph!!"
        elif isinstance(error, app_commands.BotMissingPermissions):
            msg = "🚨 B-Baka! Eu não tenho permissão de `Gerenciar Mensagens` ou de ler o histórico neste canal. Ajuste meus cargos antes de me dar ordens!"
        elif isinstance(error, app_commands.CommandOnCooldown):
            msg = f"⏳ Calma lá! Eu acabei de varrer o chão, espere {error.retry_after:.1f} segundos para pedir de novo."
        else:
            logger.error(f"Erro não tratado no comando /clear: {error}", exc_info=True)

        if interaction.response.is_done():
            await interaction.followup.send(msg, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Util(bot))
