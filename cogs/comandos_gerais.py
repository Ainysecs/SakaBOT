import discord
from discord.ext import commands
import os
import asyncio

class GeraisCmd(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="gcmd")
    async def comandos_gerais(self, ctx):
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
        embed = discord.Embed(
            title="Comandos do Servidor",
            description="Tabela oficial de comandos, apenas os mais úteis.",
            color=0x3498DB
        )
        embed.set_thumbnail(url="https://images.emojiterra.com/google/android-nougat/512px/2699.png")
        
        embed.add_field(
            name="💻 Sesh", 
            value="*/create*\n*/poll*\n*/list*\n*/remind*\n*/delete*\n*/link*\n*/ai*\n\u200e", 
            inline=True
        )
        
        embed.add_field(
            name="🎤 Craig", 
            value="*/join*\n*/stop*\n*/note*\n*/recordings*\n*/info*\n*/webapp*\n\u200e", 
            inline=True
        )
        
        embed.add_field(
            name="📈 Simple Poll", 
            value="*/poll*\n\u200e", 
            inline=True
        )
     
        embed.add_field(
            name="🤖 SakaIA", 
            value="*!ia [texto opcional]*", 
            inline=True
        )

        embed.set_footer(text="SAKAnagem Enterprise • 2026")
        
        # Envia o Embed
        await ctx.send(embed=embed)

        # Apaga o "!gcmd" que o administrador digitou para manter a organização
        try:
            if ctx.guild:
                await ctx.message.delete()
        except discord.HTTPException:
            pass

async def setup(bot):
    await bot.add_cog(GeraisCmd(bot))

"""
===================================================================
               comando para o utilitário: !gcmd
===================================================================

"""
