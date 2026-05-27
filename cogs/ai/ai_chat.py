import discord
from discord import app_commands
from discord.ext import commands
from google import genai
from google.genai import types
import os
import json
import logging
import traceback
from pathlib import Path

logger = logging.getLogger(__name__)

class ChatAI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        api_key = os.getenv("AI_API_KEY")
        if not api_key:
            logger.warning("Variável de ambiente 'AI_API_KEY' não encontrada. A IA não vai funcionar.")
        self.client = genai.Client(api_key=api_key)

        canal_id = os.getenv("AI_CHANNEL_ID")
        self.canal_permitido_id = int(canal_id) if canal_id and canal_id.strip() else None

        self.base_dir = Path.cwd() / "config" / "locales" / "pt_br" / "ai"
        self.config_ai = self._carregar_config_ai()
        self.personalidade = self._carregar_persona()

    def _carregar_config_ai(self):
        caminho_config = self.base_dir / "config_ai.json"
        try:
            with open(caminho_config, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return {"messages": {}, "limits": {"max_image_size_bytes": 5242880}}
        except Exception as e:
            logger.error(f"Falha ao carregar {caminho_config}: {e}")
            return {"messages": {}, "limits": {"max_image_size_bytes": 5242880}}

    def _carregar_persona(self):
        caminho_persona = self.base_dir / "saka_persona.txt"
        try:
            with open(caminho_persona, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return "Você é uma assistente útil e amigável."
        except Exception as e:
            logger.error(f"Falha ao carregar {caminho_persona}: {e}")
            return "Você é uma assistente útil e amigável."

    # =================================================================
    # MOTOR PRINCIPAL DA IA (Usado tanto pelo / quanto pelo !)
    # =================================================================
    async def _gerar_resposta(self, user_id: int, channel_id: int, ask: str, img: discord.Attachment, enviar_mensagem_func):
        msgs = self.config_ai.get("messages", {})
        limits = self.config_ai.get("limits", {})

        if self.canal_permitido_id and channel_id != self.canal_permitido_id:
            msg_canal = msgs.get("wrong_channel", f"❌ Canal incorreto! Use: <#{self.canal_permitido_id}>")
            await enviar_mensagem_func(msg_canal)
            return

        if not ask and not img:
            await enviar_mensagem_func("❌ **Ops!** Você precisa me enviar um texto, uma imagem, ou os dois juntos.")
            return

        if img:
            is_valid_type = img.content_type and img.content_type.startswith('image/')
            max_size = limits.get("max_image_size_bytes", 5242880) 
            is_valid_size = img.size <= max_size

            if not is_valid_type or not is_valid_size:
                await enviar_mensagem_func(msgs.get("invalid_image", f"❌ A imagem enviada é inválida ou passa de {max_size / (1024*1024):.0f}MB."))
                return

        try:
            conteudo_para_enviar = []

            # Se tiver texto, adiciona. Se tiver SÓ imagem, adiciona um texto padrão.
            if ask:
                conteudo_para_enviar.append(ask)
            elif img and not ask:
                conteudo_para_enviar.append("Por favor, descreva ou analise esta imagem para mim.")

            if img:
                bytes_image = await img.read()
                dados_image = types.Part.from_bytes(
                    data=bytes_image,
                    mime_type=img.content_type or "image/png",
                )
                conteudo_para_enviar.append(dados_image)

            api_config = types.GenerateContentConfig(system_instruction=self.personalidade)
            response = await self.client.aio.models.generate_content(
                model='gemini-2.5-flash',
                contents=conteudo_para_enviar,
                config=api_config
            )

            texto_resposta = response.text if response.text else msgs.get("ignored", "A Saka apenas te olhou e ignorou...")

            tamanho_maximo = 1950 
            if len(texto_resposta) > tamanho_maximo:
                chunks = [texto_resposta[i:i + tamanho_maximo] for i in range(0, len(texto_resposta), tamanho_maximo)]
                for chunk in chunks:
                    await enviar_mensagem_func(chunk)
            else:
                await enviar_mensagem_func(texto_resposta)

        except Exception as e:
            logger.error(f"Erro ao gerar resposta da API: {e}\n{traceback.format_exc()}")
            erro_msg = msgs.get("internal_error", "❌ Ocorreu um erro interno na IA. Tente novamente mais tarde.")
            await enviar_mensagem_func(erro_msg)


    # =================================================================
    # 1. COMANDO DE PREFIXO (!ai ou !ia)
    # =================================================================
    @commands.command(name="ai", aliases=["ia"])
    @commands.cooldown(1, 30.0, commands.BucketType.user)
    async def prefix_ai(self, ctx: commands.Context, *, ask: str = None):
        """
        Uso: !ai <texto> e anexe uma imagem se quiser.
        """
        img = ctx.message.attachments[0] if ctx.message.attachments else None
        
        async with ctx.typing():
            await self._gerar_resposta(
                user_id=ctx.author.id,
                channel_id=ctx.channel.id,
                ask=ask,
                img=img,
                enviar_mensagem_func=ctx.reply
            )

    @prefix_ai.error
    async def prefix_ai_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.reply(f"⏳ Calma lá! Aguarde {error.retry_after:.1f} segundos para falar comigo de novo.")


    # =================================================================
    # 2. SLASH COMMAND (/ai)
    # =================================================================
    @app_commands.command(name="ai", description="Converse com a Saka. Envie texto, imagem, ou os dois!")
    @app_commands.guild_only()
    @app_commands.describe(
        ask="O que você quer perguntar/falar com a Saka?",
        img="Uma imagem para ela analisar (opcional)"
    )
    @app_commands.checks.cooldown(1, 30.0, key=lambda i: i.user.id)
    async def slash_ai(self, interaction: discord.Interaction, ask: str = None, img: discord.Attachment = None):
        await interaction.response.defer(thinking=True)
        
        await self._gerar_resposta(
            user_id=interaction.user.id,
            channel_id=interaction.channel_id,
            ask=ask,
            img=img,
            enviar_mensagem_func=interaction.followup.send
        )

    @slash_ai.error
    async def slash_ai_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            msg = f"⏳ Calma lá! Aguarde {error.retry_after:.1f} segundos para falar comigo de novo."
            if interaction.response.is_done():
                await interaction.followup.send(msg, ephemeral=True)
            else:
                await interaction.response.send_message(msg, ephemeral=True)
            return

        logger.error(f"Erro no comando /ai: {error}")
        msg_erro = "⚠️ Ocorreu um erro inesperado."
        if interaction.response.is_done():
            await interaction.followup.send(msg_erro, ephemeral=True)
        else:
            await interaction.response.send_message(msg_erro, ephemeral=True)


async def setup(bot):
    await bot.add_cog(ChatAI(bot))
