import logging
from typing import Literal

import discord
from discord import app_commands
from discord.ext import commands

logger = logging.getLogger('saka.cogs.admin')

class SakaCoreAdmin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _responder(self, ctx: commands.Context, mensagem: str):
        if len(mensagem) > 2000:
            mensagem = mensagem[:1990] + "..."

        if ctx.interaction:
            if ctx.interaction.response.is_done():
                await ctx.interaction.followup.send(mensagem, ephemeral=True)
            else:
                await ctx.interaction.response.send_message(mensagem, ephemeral=True)
        else:
            try:
                await ctx.reply(mensagem)
            except discord.HTTPException as e:
                if e.code == 50035 or "message_reference" in str(e).lower():
                    await ctx.send(mensagem)
                else:
                    raise e

    # ==========================================
    # COMANDO PRINCIPAL
    # ==========================================
    @commands.hybrid_command(name="sync", hidden=True, description="[DEV] Painel de controle da árvore de comandos da Saka.")
    @app_commands.describe(escopo="Escolha o modo de manutenção da árvore de comandos")
    @app_commands.default_permissions(administrator=True)
    @commands.has_permissions(administrator=True) 
    async def sync(self, ctx: commands.Context, escopo: Literal["local", "global", "clear", "check"]):

        if ctx.interaction:
            await ctx.interaction.response.defer(ephemeral=True)
        else:
            await ctx.typing()

        executor = ctx.author.name
        logger.info(f"[SYNC] Comando disparado por {executor} com escopo: '{escopo}'")

        try:
            if escopo == "local":
                await self._sync_local(ctx)
            elif escopo == "global":
                await self._sync_global(ctx)
            elif escopo == "clear":
                await self._sync_clear(ctx)
            elif escopo == "check":
                await self._sync_check(ctx)

        except Exception as e:
            await self._handle_sync_error(ctx, e, escopo)

    async def _sync_local(self, ctx: commands.Context):
        guild = ctx.guild
        if not guild:
            return await self._responder(ctx, "❌ B-baka! Eu só posso sincronizar coisas dentro de um servidor!")

        logger.info(f"[SYNC LOCAL] Copiando comandos globais temporariamente para a guilda: {guild.name} ({guild.id})")

        self.bot.tree.copy_global_to(guild=guild)
        synced = await self.bot.tree.sync(guild=guild)

        logger.info(f"[SYNC LOCAL SUCESSO] {len(synced)} comandos sincronizados localmente no servidor {guild.id}.")

        msg = (f"✨ Prontinho! Copiei os comandos globais e sincronizei **{len(synced)}** comandos locais neste servidor para testes rápidos.\n"
               f"Use logo os seus comandos com `/` e não me irrite! 💅")
        await self._responder(ctx, msg)

    async def _sync_global(self, ctx: commands.Context):
        logger.info("[SYNC GLOBAL] Iniciando sincronização na árvore global do Discord.")
        synced = await self.bot.tree.sync()

        logger.info(f"[SYNC GLOBAL SUCESSO] {len(synced)} comandos sincronizados globalmente.")

        msg = (f"🌍 Ugh... Sincronizei **{len(synced)}** comandos **globalmente**.\n"
               f"Lembre-se: o Discord pode demorar até 1 hora pra atualizar isso para os plebeus em outros servidores! 💅")
        await self._responder(ctx, msg)

    async def _sync_clear(self, ctx: commands.Context):
        guild = ctx.guild
        executor = ctx.author.name
        logger.warning(f"[SYNC CLEAR] Faxina total iniciada por {executor}.")

        if guild:
            self.bot.tree.clear_commands(guild=guild)
            await self.bot.tree.sync(guild=guild)
            logger.info(f"[SYNC CLEAR] Comandos locais da guilda {guild.id} apagados.")

        self.bot.tree.clear_commands(guild=None)
        await self.bot.tree.sync(guild=None)
        logger.info("[SYNC CLEAR] Comandos globais apagados com sucesso da API do Discord.")

        msg = ("🧹 Faxina completa! Apaguei todos os comandos antigos do cache do Discord.\n\n"
               "⚠️ **E agora eu estou com amnésia!** Eu deletei tudo da minha memória RAM. "
               "Você **PRECISA** usar `!reload all` agora mesmo para eu lembrar de quem eu sou e reconstruir a árvore! 💅")
        await self._responder(ctx, msg)

    async def _sync_check(self, ctx: commands.Context):
        logger.info("[SYNC CHECK] Verificando comandos globais na API do Discord.")
        tree_commands = await self.bot.tree.fetch_commands(guild=None)
        nomes = [f"`/{cmd.name}`" for cmd in tree_commands]

        if nomes:
            msg = f"🔍 **Comandos atualmente registrados na árvore global do Discord:**\n" + ", ".join(nomes)
        else:
            msg = "🔍 **A árvore global do Discord está 100% vazia!** Nossos comandos limpos foram desativados com sucesso. 🧹"

        await self._responder(ctx, msg)

    # --- TRATAMENTO DE ERROS ---
    async def _handle_sync_error(self, ctx: commands.Context, error: Exception, escopo: str):
        if isinstance(error, discord.HTTPException):
            logger.warning(f"[SYNC HTTP ERROR] O Discord barrou a requisição ({escopo}): {error}")
            await self._responder(ctx, "⏳ O Discord está me limitando! Você tá fazendo isso rápido demais, b-baka!")
        else:
            logger.error(f"[SYNC CRITICAL ERROR] Falha na operação '{escopo}': {error}", exc_info=True)
            await self._responder(ctx, "💢 Ah, ótimo! Deu um erro interno bizarro na hora de sincronizar. Vai olhar o terminal!")

    @sync.error
    async def sync_error(self, ctx: commands.Context, error: commands.CommandError):
        async def _erro_seguro(texto_erro: str):
            if ctx.interaction:
                if ctx.interaction.response.is_done():
                    await ctx.interaction.followup.send(texto_erro, ephemeral=True)
                else:
                    await ctx.interaction.response.send_message(texto_erro, ephemeral=True)
            else:
                try:
                    await ctx.reply(texto_erro)
                except discord.HTTPException:
                    await ctx.send(texto_erro)

        executor = ctx.author.name
        if isinstance(error, commands.MissingPermissions):
            logger.warning(f"[SYNC NEGADO] {executor} tentou usar o comando sem permissões de administrador.")
            await _erro_seguro("💢 Quem você pensa que é? Só a autoridade máxima do servidor pode me dar esse tipo de ordem! Hmph!!")
        elif isinstance(error, commands.MissingRequiredArgument):
            await _erro_seguro("💢 B-baka! Você precisa me dizer o que sincronizar! Use `!sync local`, `!sync global`, `!sync clear` ou `!sync check`.")
        else:
            logger.error(f"[SYNC ERROR HANDLER] Erro não tratado: {error}", exc_info=True)
            await _erro_seguro("❌ Deu algum problema interno bizarro.")

async def setup(bot: commands.Bot):
    await bot.add_cog(SakaCoreAdmin(bot))
