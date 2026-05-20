import discord
from discord.ext import commands
import os
import asyncio

class bt_commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="btcmd")
    async def btcmd(self, ctx):
        # Pega o ID do cargo direto do ambiente (.env / Render)
        id_cargo_env = os.getenv('ROLE_ID')
        
        # === VALIDAÇÃO UNIVERSAL DE CARGO ===
        tem_permissao = False
        if id_cargo_env and hasattr(ctx.author, 'roles'):
            tem_permissao = any(role.id == int(id_cargo_env) for role in ctx.author.roles)

        # --- CASO NÃO TENHA PERMISSÃO (Apaga o erro e o comando em 5 segundos) ---
        if not tem_permissao:
            msg_aviso = await ctx.send("❌ **ERRO:** Você não possui o Cargo de Elite configurado para usar este utilitário! Suma daqui, plebeu! 💢")
            
            await asyncio.sleep(5)
            
            try:
                await msg_aviso.delete()
            except discord.HTTPException:
                pass
                
            try:
                if ctx.guild:
                    await ctx.message.delete()
            except discord.HTTPException:
                pass
            
            return

        # --- CASO TENHA PERMISSÃO ---
        
        # Criando o Embed
        embed = discord.Embed(
            title="Comandos do Brawl Tools",
            url="https://docs.brawltools.net/books/commands", 
            description="Lista oficial de comandos para consulta. Utilize os comandos abaixo diretamente nos canais #arquivo-starr e #buscar-times.",
            color=0xFFCC00 
        )

        # Campos Inline (Grid)
        embed.add_field(name="📋 Estatísticas de Jogadores", value="`/me`\n`/me-battles`\n`/me-winrates`\n`/image-me`\n`/image-chart`\n`/player-rating`\n\u200e", inline=True)
        embed.add_field(name="⚙️ Verificação", value="`/verify-global`\n`/update`\n`/accounts`\n`/delete-me`\n`/find`\n`/watchlist`\n`\u200e`", inline=True)
        embed.add_field(name="💤 Outros", value="`/vote`\n`/vote-reminder`\n`/command stats`\n`/embed-help`\n`/random-brawler`\n`\u200e`", inline=True)
        embed.add_field(name="☝️🤓 Utilidades", value="`/map`\n`/news`\n`/me`\n`/me-live`\n`/me-live-stop`\n`\u200e`", inline=True)
        embed.add_field(name="📊 Estatísticas de Clubes", value="`/club`\n`/image-club`\n`\u200e`", inline=True)
        embed.add_field(name="🔍 Times", value="`/ts post`\n`\u200e`", inline=True)

        embed.set_footer(text="Brawl Tools • Sistema de Consulta")
        embed.set_thumbnail(url="https://brawltools.net/img/brand/bt_logo4.webp")

        # Envia o Embed
        await ctx.send(embed=embed)

        # Apaga o "!btcmd" que o adm digitou para deixar o canal limpo
        try:
            if ctx.guild:
                await ctx.message.delete()
        except discord.HTTPException:
            pass

async def setup(bot):
    await bot.add_cog(bt_commands(bot))

"""
===================================================================
               comando para o utilitário: !btcmd
===================================================================

"""
