import logging
import discord
import aiohttp
import os
import asyncio
from discord import app_commands
from discord.ext import commands

logger = logging.getLogger('saka.cogs.stats')

class Admin(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.render_key = os.getenv('RENDER_API_KEY')
        self.uptime_key = os.getenv('UPTIMEROBOT_API_KEY')
        self.service_id = os.getenv('RENDER_SERVICE_ID')

    def _get_msg(self, path: str) -> str:
        try:
            dados = self.bot.config.locales_pt_br_admin_system_status
            for chave in path.split('.'):
                dados = dados[chave]
            return str(dados)
        except (AttributeError, KeyError, TypeError) as e:
            logger.error(f"Erro na string de configuração stats '{path}': {e}")
            return f"❌ [Erro: {path}]"

    @property
    def versao(self) -> str:
        try:
            return str(self.bot.config.version)
        except AttributeError:
            return "V-Desconhecida"

    async def _fetch_render(self, session: aiohttp.ClientSession) -> str:
        if not self.render_key or not self.service_id:
            return self._get_msg("responses.sem_chaves")

        try:
            headers = {"Authorization": f"Bearer {self.render_key}"}
            async with session.get(f"https://api.render.com/v1/services/{self.service_id}", headers=headers, timeout=10) as r:
                if r.status == 200:
                    data = await r.json()
                    is_suspended = data.get('suspended') not in (None, "not_suspended", "")
                    return self._get_msg("responses.render_suspenso") if is_suspended else self._get_msg("responses.render_ok")
                return f'{self._get_msg("responses.http_error")} {r.status}'
        except asyncio.TimeoutError:
            return self._get_msg("responses.timeout")
        except Exception as e:
            logger.error(f"Erro na API Render: {e}")
            return self._get_msg("responses.fora_alcance")

    async def _fetch_uptime(self, session: aiohttp.ClientSession) -> str:
        if not self.uptime_key:
            return self._get_msg("responses.sem_chaves")

        try:
            payload = {"api_key": self.uptime_key, "format": "json"}
            async with session.post("https://api.uptimerobot.com/v2/getMonitors", data=payload, timeout=10) as u:
                if u.status == 200:
                    data = await u.json()
                    monitors = data.get('monitors', [])
                    if not monitors:
                        return self._get_msg("responses.sem_monitores")

                    monitor = monitors[0]
                    status_chave = "responses.uptime_online" if monitor.get('status') == 2 else "responses.uptime_offline"
                    status_localizado = self._get_msg(status_chave)
                    
                    return f"{status_localizado} ({monitor.get('friendly_name', 'Sem Nome')})"
                return f'{self._get_msg("responses.http_error")} {u.status}'
        except asyncio.TimeoutError:
            return self._get_msg("responses.timeout")
        except Exception as e:
            logger.error(f"Erro na API UptimeRobot: {e}")
            return self._get_msg("responses.fora_alcance")

    @commands.hybrid_command(name="stats", hidden=True, description="[DEV] Verifica os sinais vitais do bot e dos servidores")
    @app_commands.default_permissions(administrator=True)
    @commands.is_owner()
    @commands.guild_only()
    async def stats(self, ctx: commands.Context) -> None:
        await ctx.defer(ephemeral=True)

        async with aiohttp.ClientSession() as session:
            status_render, status_uptime = await asyncio.gather(
                self._fetch_render(session),
                self._fetch_uptime(session)
            )

        embed = discord.Embed(
            title="🩺 Relatório de Saúde",
            description="Estou bem, obrigada por perguntar. 🙄",
            color=discord.Color.brand_green(),
            timestamp=discord.utils.utcnow()
        )

        embed.add_field(name="☁️ Render Host", value=status_render, inline=False)
        embed.add_field(name="📡 UptimeRobot", value=status_uptime, inline=False)
        embed.set_footer(text=f"Versão: {self.versao} • Requisitado por {ctx.author.display_name}")

        await ctx.send(embed=embed, ephemeral=True)
        logger.info(f"Relatório {self.versao} gerado para {ctx.author.name}")

    @stats.error
    async def stats_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.NotOwner):
            err_msg = self._get_msg("errors.not_owner")
            if ctx.interaction and ctx.interaction.response.is_done():
                await ctx.interaction.followup.send(err_msg, ephemeral=True)
            else:
                await ctx.send(err_msg, ephemeral=True)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Admin(bot))
