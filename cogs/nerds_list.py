import discord
from discord.ext import commands
import os
import asyncio

class NerdsModulo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="nerdscmd")
    @commands.guild_only() # Impede que o comando seja usado na DM do bot
    async def nerds_list(self, ctx):
        # Pega o ID do cargo direto do ambiente (.env / Render)
        id_cargo_env = os.getenv('ROLE_ID')
        
        # === VALIDAÇÃO DE CARGO ===
        tem_permissao = False
        if id_cargo_env and hasattr(ctx.author, 'roles'):
            tem_permissao = any(role.id == int(id_cargo_env) for role in ctx.author.roles)

        # --- CASO NÃO TENHA PERMISSÃO ---
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
        embed = discord.Embed(
            title="☝️🤓 Os Nerds do Grupo",
            description="Tabela oficial de membros e suas respectivas ocupações.",
            color=0x3498DB
        )
        embed.set_thumbnail(url="https://i.pinimg.com/736x/30/e1/1c/30e11c78a6661cd42dd1f5390aa4bbd3.jpg")
        
        # 1. Categoria: Tecnologia
        embed.add_field(
            name="💻 Tecnologia", 
            value="**Rodrigo**\n*Nerd de Programação*\n\u200e\n**Bagriel**\n*Nerd de Tecnologia*\n\u200e", 
            inline=True
        )
        
        # 2. Categoria: Estratégia & Arte
        embed.add_field(
            name="⚔️ Estratégia & Arte", 
            value="**Luqueta**\n*Nerd de Táticas*\n\u200e\n**Victor (~)**\n*Nerd de Animes*\n\u200e", 
            inline=True
        )

        # 3. Categoria: Social
        embed.add_field(
            name="💎 Social", 
            value="**Maurício**\n*Nerd de Riquezas*\n\u200e\n**Lucas 2.0**\n*Simplesmente um Nerd*\n\u200e", 
            inline=True
        )

        # 4. Categoria: O Topo
        embed.add_field(
            name="👑 O Topo", 
            value="**Kauan**\n*Nerd dos Nerds*\n\u200e", 
            inline=True
        )

        # 5. Categoria: Estilo de Vida
        embed.add_field(
            name="🍔 Estilo de Vida", 
            value="**Vinícius (original)**\n*Nerd dos Fast-Foods*\n\u200e", 
            inline=True
        )

        # 6. Categoria: Vinny
        embed.add_field(
            name="👤 Vinny", 
            value="**Vinny**\n*Vinny*", 
            inline=True
        )

        embed.set_footer(text="SAKAnagem Enterprise • 2026")
        
        # Envia o Embed fixo para o canal
        await ctx.send(embed=embed)

        # Apaga o comando "!nerdscmd" do administrador para manter a ordem no chat
        try:
            if ctx.guild:
                await ctx.message.delete()
        except discord.HTTPException:
            pass

async def setup(bot):
    await bot.add_cog(NerdsModulo(bot))

'''
===========================================================
        comando para o utilitário: !nerdscmd
===========================================================
'''
