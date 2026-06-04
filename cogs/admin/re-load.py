import logging
import importlib
import traceback
import discord
from discord.ext import commands
from discord import app_commands

logger = logging.getLogger('saka.cogs.reload')

class Developer(commands.Cog):
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

    def _formatar_traceback(self, erro: Exception) -> str:
        tb = "".join(traceback.format_exception(type(erro), erro, erro.__traceback__))
        tb = tb.replace("```", "'''").replace("`", "'")

        if len(tb) > 1600:
            tb = tb[:1600] + "\n\n[... O erro era grande demais e foi cortado por segurança ...]"
        return tb

    # ==========================================
    # COMANDO HÍBRIDO
    # ==========================================
    @commands.hybrid_command(name="reload", hidden=True, description="[DEV] Recarrega os módulos da Saka.")
    @app_commands.describe(
        cog="Nome do módulo (ou 'all' para todos)",
        sync_tree="Força o sync da tree de comandos após o reload? (Padrão: False)"
    )
    @app_commands.default_permissions(administrator=True)
    async def reload(self, ctx: commands.Context, cog: str, sync_tree: bool = False):

        if ctx.interaction:
            await ctx.interaction.response.defer(ephemeral=True)
        else:
            await ctx.typing()

        is_bot_owner = await self.bot.is_owner(ctx.author)
        if not is_bot_owner:
            raise commands.NotOwner("Apenas o dono do bot pode usar este comando.")

        current_ext = self.__module__
        importlib.invalidate_caches()

        executor = ctx.author.name
        logger.info(f"[RELOAD] Iniciado por {executor}. Alvo: '{cog}' | Forçar Sync: {sync_tree}")

        if cog.lower() == "all":
            extensions = list(self.bot.extensions.keys())
            sucessos = 0
            falhas = []

            for ext in extensions:
                if ext == current_ext:
                    continue 
                try:
                    await self.bot.reload_extension(ext)
                    sucessos += 1
                except Exception as e:
                    erro_real = getattr(e, 'original', e)
                    falhas.append(f"❌ `{ext}`: {type(erro_real).__name__}")
                    logger.error(f"[RELOAD ERROR] Falha ao recarregar a extensão '{ext}': {e}", exc_info=True)

            msg = f"🔄 *Ufa...* Troquei de roupa e reiniciei **{sucessos}** módulos. (É óbvio que ignorei a mim mesma! 😉)"
            if falhas:
                msg += "\n\n💢 M-Mas olha aqui! Alguns módulos estão quebrados, conserta isso logo:\n" + "\n".join(falhas)

            if sync_tree:
                try:
                    await self.bot.tree.sync()
                    msg += "\n✨ Ah, e eu limpei o cache e sincronizei a árvore de comandos também!"
                    logger.info("[RELOAD] Árvore de comandos sincronizada com sucesso globalmente.")
                except Exception as e:
                    logger.error(f"[RELOAD SYNC ERROR] Falha ao sincronizar comandos após recarregar todos: {e}", exc_info=True)
                    msg += "\n⚠️ Recarreguei os cogs, mas a sincronização da árvore falhou catastroficamente. Olha o console!"

            logger.info(f"[RELOAD COMPLETO] Todos os cogs processados por {executor}. Sucessos: {sucessos}, Falhas: {len(falhas)}")
            await self._responder(ctx, msg)
            return

        cog_limpo = cog.replace("cog:", "").strip()
        cog_path = f"cogs.{cog_limpo}" if not cog_limpo.startswith("cogs.") else cog_limpo

        if cog_path == current_ext:
            logger.warning(f"[RELOAD ADVERTÊNCIA] {executor} tentou recarregar o próprio cog de reload.")
            await self._responder(ctx, "`💢 B-Baka! Eu não posso recarregar a mim mesma enquanto conversamos, senão eu desmaio no meio da frase! Não faça isso!`")
            return

        try:
            await self.bot.reload_extension(cog_path)
            msg = f"✅ Tá, tá... Recarreguei o módulo `{cog_path}`. Satisfeito, seu nerd? 🙄"

            if sync_tree:
                try:
                    await self.bot.tree.sync()
                    msg += "\n✨ E a árvore de comandos foi limpa e updated!"
                    logger.info(f"[RELOAD SYNC] Árvore sincronizada após recarga de {cog_path}")
                except Exception as e:
                    logger.error(f"[RELOAD SYNC ERROR] Falha ao sincronizar comandos após recarregar '{cog_path}': {e}", exc_info=True)
                    msg += "\n⚠️ Módulo updated, mas o cache da árvore falhou ao sincronizar!"

            await self._responder(ctx, msg)
            logger.info(f"[RELOAD SUCESSO] Módulo '{cog_path}' recarregado com sucesso por {executor}")

        except commands.ExtensionNotLoaded:
            logger.info(f"[LOAD AUTOMÁTICO] Módulo '{cog_path}' não estava carregado. Tentando buscar no disco...")
            try:
                await self.bot.load_extension(cog_path)
                msg = f"🆕 *Olha só o que temos aqui...* Detectei que o módulo `{cog_path}` é novinho em folha e acabei de carregar ele com sucesso! 😉"

                if sync_tree:
                    await self.bot.tree.sync()
                    msg += "\n✨ E a árvore já foi limpa para registrar os novos comandos!"

                await self._responder(ctx, msg)
                logger.info(f"[LOAD SUCESSO] Módulo novo '{cog_path}' carregado com sucesso via automação.")

            except commands.ExtensionNotFound:
                logger.warning(f"[LOAD AVISO] Arquivo '{cog_path}' não existe no servidor (Tentativa por {executor})")
                await self._responder(ctx, f"🔍 Eu até tentei procurar por `{cog_path}` para carregar como um módulo novo, mas não achei nenhum arquivo com esse nome. Escreveu certo? (Cuidado com subpastas!)")

            except commands.ExtensionFailed as e:
                erro_real = e.original if hasattr(e, 'original') else e
                tb = self._formatar_traceback(erro_real)
                logger.error(f"[LOAD FALHA CRÍTICA] Erro interno ao inicializar módulo NOVO '{cog_path}': {erro_real}", exc_info=True)
                error_msg = f"❌ B-Baka! Você tentou colocar o módulo novo `{cog_path}` mas o código dele tá todo quebrado! Conserta isso:\n```py\n{tb}\n```"
                await self._responder(ctx, error_msg)
                
            except Exception as e:
                tb = self._formatar_traceback(e)
                logger.error(f"[LOAD ERRO IMPREVISTO] Instabilidade ao carregar módulo novo '{cog_path}': {e}", exc_info=True)
                error_msg = f"❌ Ocorreu um erro bizarro ao tentar carregar o módulo novo `{cog_path}`:\n```py\n{tb}\n```"
                await self._responder(ctx, error_msg)

        except commands.ExtensionNotFound:
            logger.warning(f"[RELOAD AVISO] Módulo '{cog_path}' não foi encontrado no projeto (Tentativa por {executor})")
            await self._responder(ctx, f"🔍 Procurei em todo o projeto e não achei nenhum arquivo para `{cog_path}`.")

        except commands.NoEntryPointError:
            logger.error(f"[RELOAD FALHA] Falta de setup() no módulo '{cog_path}' por {executor}")
            await self._responder(ctx, f"❌ B-Baka! Você esqueceu de colocar a função `async def setup(bot):` no final do módulo `{cog_path}`!")

        except commands.ExtensionFailed as e:
            erro_real = e.original if hasattr(e, 'original') else e
            tb = self._formatar_traceback(erro_real)
            logger.error(f"[RELOAD FALHA CRÍTICA] Erro interno ao atualizar '{cog_path}' por {executor}: {erro_real}", exc_info=True)
            error_msg = f"❌ B-Baka! Seu código tá todo quebrado! Olha esse erro grotesco ao tentar mexer em `{cog_path}`:\n```py\n{tb}\n```"
            await self._responder(ctx, error_msg)

        except Exception as e:
            tb = self._formatar_traceback(e)
            logger.error(f"[RELOAD ERRO IMPREVISTO] Instabilidade desconhecida em '{cog_path}' por {executor}: {e}", exc_info=True)
            error_msg = f"❌ Ocorreu um erro bizarro que nem eu entendi em `{cog_path}`:\n```py\n{tb}\n```"
            await self._responder(ctx, error_msg)

    # ==========================================
    # AUTOCOMPLETE
    # ==========================================
    @reload.autocomplete("cog")
    async def reload_autocomplete(self, interaction: discord.Interaction, current: str):
        if not await interaction.client.is_owner(interaction.user):
            return []

        current_ext = self.__module__
        choices = [app_commands.Choice(name="all", value="all")]

        for ext in self.bot.extensions.keys():
            if ext == current_ext:
                continue
            ext_limpo = ext.replace("cogs.", "")
            if current.lower() in ext_limpo.lower():
                choices.append(app_commands.Choice(name=ext_limpo, value=ext_limpo))
                if len(choices) == 25:
                    break

        return choices

    # ==========================================
    # TRATAMENTO DE ERROS DE PERMISSÃO/ARGUMENTO
    # ==========================================
    @reload.error
    async def reload_error(self, ctx: commands.Context, error: commands.CommandError):
        executor = ctx.author.name
        if isinstance(error, commands.NotOwner):
            logger.warning(f"[RELOAD NEGADO] Usuário não autorizado '{executor}' tentou usar o comando.")
            await self._responder(ctx, "💢 Tira as patas daí! Só o meu criador pode mexer nas minhas engrenagens e configurações internas! Hmph!")
        elif isinstance(error, commands.MissingRequiredArgument):
            await self._responder(ctx, "💢 B-baka! Me diz qual módulo eu devo recarregar ou escreve `all`!")
        else:
            logger.error(f"[RELOAD ERRO DESCONHECIDO] Falha no manipulador de erros do reload: {error}", exc_info=True)
            await self._responder(ctx, "❌ Ocorreu um erro interno horrível ao processar o comando. Olha o console.")

async def setup(bot: commands.Bot):
    await bot.add_cog(Developer(bot))
