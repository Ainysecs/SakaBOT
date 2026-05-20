import discord
from discord.ext import commands

class Util(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="limpar")
    @commands.guild_only() 
    @commands.has_permissions(manage_messages=True)
    async def limpar(self, ctx, quantidade: int = 20): # Padrão definido para 20 mensagens
        # Garante que o usuário não coloque um número negativo ou zero
        if quantidade <= 0:
            await ctx.send("❌ Por favor, insira um número maior que 0!", delete_after=3)
            try:
                await ctx.message.delete()
            except discord.HTTPException:
                pass
            return

        try:
            # === PROTEÇÃO DE LIMITE DA API DO DISCORD ===
            # Força a quantidade solicitada a nunca passar de 100
            quantidade_segura = min(quantidade, 100)
            
            # Se for exatamente 100, o limite máximo é 100. Se for menor, soma 1 para incluir o comando.
            limite = quantidade_segura if quantidade_segura == 100 else quantidade_segura + 1

            # bulk=True ignora mensagens com mais de 14 dias em vez de crashar o comando
            deleted = await ctx.channel.purge(limit=limite, bulk=True)

            # Evita contadores negativos caso a lista venha vazia por erro do Discord
            mensagens_removidas = max(0, len(deleted) - 1)

            # Resposta rápida que se apaga em 3 segundos
            await ctx.send(
                f"🧹 Limpeza concluída! {mensagens_removidas} mensagens removidas.", 
                delete_after=3
            )
            print(f"✅ Faxina feita no canal: {ctx.channel.name}")

        except discord.Forbidden:
            print(f"❌ Falta de permissão no canal {ctx.channel.name}")
            await ctx.send(
                "🚨 Erro: Eu não tenho a permissão 'Gerenciar Mensagens' neste canal!", 
                delete_after=5
            )
        except Exception as e:
            print(f"❌ Erro ao limpar canal {ctx.channel.name}: {e}")
            await ctx.send(
                "🚨 Ocorreu um erro inesperado ao tentar limpar o canal.", 
                delete_after=5
            )

    # --- TRATAMENTO PARA QUEM NÃO TEM PERMISSÃO ---
    @limpar.error
    async def limpar_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(
                f"💢 {ctx.author.mention}, você não tem moral para limpar este chat! hmph!!", 
                delete_after=5
            )
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send("❌ Este comando só pode ser usado dentro de um servidor!", delete_after=5)
            return  # Não tenta apagar a mensagem se for na DM

        # Tenta apagar a mensagem de comando do engraçadinho
        try:
            if ctx.guild:
                await ctx.message.delete()
        except discord.HTTPException:
            pass

async def setup(bot):
    await bot.add_cog(Util(bot))
    
    

'''
===========================================================
         comando para o utilitário: !limpar
===========================================================
'''
