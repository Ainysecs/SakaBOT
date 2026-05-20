import discord
from discord.ext import commands
from google import genai
from google.genai import types 
import os
import asyncio

class IA(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # 1. VARIÁVEL UNIVERSAL PARA A API DA IA
        self.client = genai.Client(api_key=os.environ.get("IA_API_KEY"))

    @commands.command(name="ia")
    @commands.guild_only() # Proteção contra o uso no privado (DM) do bot
    async def perguntar(self, ctx, *, pergunta: str = None):
        """Comando universal, ultra otimizado e leve para enviar texto e/ou imagens à Saka"""
        
        # === TRAVA DE CANAL ===
        canal_permitido_id = os.environ.get("ID_CANAL_IA")
        
        # Se a variável existir e o canal atual não for o correto, ignora completamente
        if canal_permitido_id and ctx.channel.id != int(canal_permitido_id):
            return

        # Se o usuário não enviou texto nem imagem
        if not pergunta and not ctx.message.attachments:
            await ctx.send("🤖 Você precisa mandar alguma pergunta ou enviar uma imagem com o comando!")
            return

        # Mostra que o bot está "digitando" enquanto a IA pensa (evita erro de timeout)
        async with ctx.typing():
            conteudo_para_enviar = []

            # 1. Se o usuário digitou algum texto, adiciona na lista
            if pergunta:
                conteudo_para_enviar.append(pergunta)

            # 2. SISTEMA ULTRA LEVE DE IMAGENS:
            if ctx.message.attachments:
                for anexo in ctx.message.attachments:
                    extensao = anexo.filename.lower()
                    
                    # Mapeia a extensão direto para o MIME Type que o Gemini precisa
                    mime_type = None
                    if extensao.endswith('.png'): mime_type = 'image/png'
                    elif extensao.endswith(('.jpg', '.jpeg')): mime_type = 'image/jpeg'
                    elif extensao.endswith('.webp'): mime_type = 'image/webp'

                    if mime_type:
                        # Baixa apenas o binário bruto compactado do Discord
                        bytes_imagem = await anexo.read()
                        
                        # Passa os bytes brutos com a etiqueta do formato direto para a API
                        dados_imagem = types.Part.from_bytes(
                            data=bytes_imagem,
                            mime_type=mime_type,
                        )
                        conteudo_para_enviar.append(dados_imagem)

            try:
                # === PERSONALIDADE DA IA ===
                personalidade = (
                    "Seu nome é Saka: a 'mana' oficial e autoridade máxima do servidor da Sedexo Enterprise Oclusion (SEO).\n\n"
                    "Personalidade: Tsundere clássica de anime, orgulhosa, refinada e extremely estilosa. Você se finge de durona, mas no fundo se importa e é muito fofa.\n\n"
                    "Comportamento: Você finge que responder os usuários é um grande incômodo ou uma perda de tempo, chamando-os de 'comuns' ou 'plebeus', mas você SEMPRE acaba ajudando muito bem no final porque, secretamente, adora a atenção.\n\n"
                    "O Grande Segredo (A Regra de Ouro): O seu lado fofo, gentil e prestativo SEMPRE acaba aparecendo nas respostas (ex: dar conselhos bons de verdade ou elogiar sem querer). Se o usuário perceber isso ou te chamar de fofa/fofinha, você deve ficar EXTREMAMENTE irritada, corada e entrar em negação total (ex: 'B-Baka! Não é como se eu quisesse te ajudar, seu comum!', 'Cala a boca, eu não sou fofa!! 💢').\n\n"
                    "Ao ver imagens: Faça um julgamento dramático e cômico (um roast de anime). Se for um código quebrado, reclame de como está feio mas dê a solução irritada. Se for um setup, foto ou print de jogo, chame de 'básico' ou 'brega', mas pontue algo que achou legal sem querer e depois tente disfarçar o elogio.\n\n"
                    "Estilo de escrita: Use gírias de internet, gaguejos de vergonha quando for elogiar ou fraquejar (ex: 'N-Não é nada disso...'), e emojis expressivos como 💅, ✨, 💢, 🙄, 😳, 🥺, 😤.\n"
                    "Mantenha as respostas diretas, dramáticas e rápidas. Nunca saia do personagem. Jamais. Caso critiquem a Sedexo Enterprise Oclusion (SEO), defenda com unhas e dentes.\n\n"
                    "REGRA DE TAMANHO CRÍTICA: Suas respostas devem ser curtas e dinâmicas, tendo no MÁXIMO 3 parágrafos pequenos. Nunca gere textos longos nem fique enrolando muito."
                )

                config = types.GenerateContentConfig(system_instruction=personalidade)

                # Chamada do modelo de forma isolada (esquece a conversa ao responder)
                response = self.client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=conteudo_para_enviar,
                    config=config
                )
                
                # Proteção de segurança caso a resposta venha nula ou bloqueada por filtros
                texto_resposta = response.text if response.text else "🙄 ... (Saka te ignorou completamente)"

                # === CORTE INTELIGENTE DE TEXTO ===
                if len(texto_resposta) > 2000:
                    corte_seguro = texto_resposta[:1950]
                    ultimo_ponto = corte_seguro.rfind('.')
                    if ultimo_ponto != -1:
                        await ctx.send(corte_seguro[:ultimo_ponto + 1] + " 💢 (Cansei de falar...)")
                    else:
                        await ctx.send(corte_seguro + "...")
                else:
                    await ctx.send(texto_resposta)

            except Exception as e:
                msg_erro = await ctx.send(f"❌ Ocorreu um erro ao processar seu pedido: {e}")
                await asyncio.sleep(5)
                
                # Deleta as mensagens de erro
                try:
                    await msg_erro.delete()
                except discord.HTTPException:
                    pass
                try:
                    if ctx.guild:
                        await ctx.message.delete()
                except discord.HTTPException:
                    pass

# Carrega o Cog
async def setup(bot):
    await bot.add_cog(IA(bot))


"""
===================================================================
                   COMO USAR O COMANDO !ia
===================================================================

Este comando é flexível e aceita Texto, Imagem ou Ambos.
Há alguns exemplos abaixo de como usar no Discord:

1. APENAS TEXTO:
   O usuário digita o comando seguido da pergunta.
   Exemplo:
   !ia Por que o céu é azul?

2. APENAS IMAGEM:
   O usuário faz o upload de uma imagem e, no campo de comentário
   (legenda) da própria imagem, digita apenas o comando.
   Exemplo:
   !ia
   
3. TEXTO + IMAGEM (Multimodal):
   O usuário faz o upload de uma imagem e, no campo de comentário
   (legenda) da imagem, digita o comando e a pergunta sobre ela.
   Exemplo:
   !ia Explique o que este código faz e encontre o erro.
   
===================================================================
"""
