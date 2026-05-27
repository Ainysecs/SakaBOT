import os
import discord
import logging
from discord.ext import commands
from discord import app_commands, ui

logger = logging.getLogger('saka.cogs.support')

class ViewSAC(ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    def _get_msg(self, path):
        return self.bot.config.locales_pt_br_admin_support.get("responses", {}).get(path, "Erro")

    @ui.button(label="Falar com Suporte", style=discord.ButtonStyle.green, custom_id="sac_atendente_btn_v1")
    async def confirm(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message(self._get_msg("atendente_ativado"), ephemeral=True)

    @ui.button(label="Desistir", style=discord.ButtonStyle.danger, custom_id="sac_desistir_btn_v1")
    async def cancel(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message(self._get_msg("desistencia"), ephemeral=True)

class Support(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        self.bot.add_view(ViewSAC(self.bot))

    @app_commands.command(name="support", description="[ADMIN] Inicia o painel de suporte")
    @app_commands.default_permissions(manage_guild=True) 
    async def support(self, interaction: discord.Interaction):
        canal_id = int(os.getenv('SUPPORT_CHANNEL_ID', '0'))

        if canal_id and interaction.channel.id != canal_id:
            msg = self.bot.config.locales_pt_br_admin_support["responses"]["erro_canal"].format(canal_id=canal_id)
            await interaction.response.send_message(msg, ephemeral=True)
            return

        embed = discord.Embed(
            title="🎯 Saka - Sistema de Suporte",
            description=self.bot.config.locales_pt_br_admin_support["responses"]["painel_suporte"],
            color=discord.Color.blue()
        )

        await interaction.response.send_message(embed=embed, view=ViewSAC(self.bot))

    @support.error
    async def support_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(self.bot.config.locales_pt_br_admin_support["errors"]["not_authorized"], ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Support(bot))
