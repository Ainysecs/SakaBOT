import os
import discord
from discord.ext import commands
from discord import ui

# 1. Definição da View (Interface dos Botões)
class ViewSAC(ui.View):
    def __init__(self):
        super().__init__(timeout=None) 

    @ui.button(
        label="Falar com Atendente", 
        style=discord.ButtonStyle.green, 
        custom_id="sac_atendente_btn_v1"
    )
    async def confirmar(self, interaction: discord.Interaction, button: ui.Button):
        # Texto da piada
        texto_loop = "Protocolo em processamento. Clique novamente para confirmar sua paciência."
        
        # Se a mensagem de origem NÃO for efêmera (o primeiro clique no canal público)
        if not interaction.message.flags.ephemeral:
            # Responde criando uma nova mensagem privada (Efêmera) com os mesmos botões
            await interaction.response.send_message(
                content=texto_loop,
                view=self,
                ephemeral=True
            )
        else:
            # Se já for a mensagem privada, apenas edita o texto fingindo que recarregou
            await interaction.response.edit_message(
                content=f"{texto_loop} (Tentativa atualizada... 🙄)",
                view=self
            )

    @ui.button(
        label="Desistir", 
        style=discord.ButtonStyle.danger, 
        custom_id="sac_desistir_btn_v1"
    )
    async def desistir(self, interaction: discord.Interaction, button: ui.Button):
        msg = "Processo encerrado. A Saka agradece sua desistência! Volte nunca. 💅"
        
        if not interaction.message.flags.ephemeral:
            await interaction.response.send_message(content=msg, ephemeral=True)
        else:
            # Remove os botões ao desistir para o usuário não clicar de novo
            await interaction.response.edit_message(content=msg, view=None)

# 2. A Engrenagem (Cog)
class SAC(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="sac")
    @commands.guild_only() # Impede de usar na DM do bot
    @commands.has_permissions(manage_messages=True) # Apenas Staff inicia o painel
    async def sac(self, ctx):
        """Inicia o menu da Saka"""
        
        # Pega o ID do canal permitido direto do ambiente (.env / Render)
        canal_configurado = os.getenv('ID_CANAL_SAC')
        canal_permitido_id = int(canal_configurado) if canal_configurado else 0

        # Se a variável existir e o canal estiver errado
        if canal_permitido_id and ctx.channel.id != canal_permitido_id:
            await ctx.send(f"❌ Errou o guichê! Vá para <#{canal_permitido_id}>", delete_after=5)
            try:
                if ctx.guild:
                    await ctx.message.delete()
            except discord.HTTPException:
                pass
            return

        embed = discord.Embed(
            title="🎯 Saka - Sistema de Atendimento ao Corno",
            description="Clique no botão abaixo para ser pessimamente atendido:",
            color=discord.Color.blue()
        )
        
        # Envia o painel fixo
        await ctx.send(embed=embed, view=ViewSAC())
        
        # Apaga o "!sac" do admin para deixar o canal limpo
        try:
            if ctx.guild:
                await ctx.message.delete()
        except discord.HTTPException:
            pass

    # --- TRATAMENTO DE ERRO DO SAC ---
    @sac.error
    async def sac_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(f"⚠️ {ctx.author.mention}, você é um plebeu! Não tente me usar novamente. 😡 hmph!!", delete_after=5)
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send("❌ Este comando só pode ser usado dentro de um servidor!", delete_after=5)
            return

        try:
            if ctx.guild:
                await ctx.message.delete()
        except discord.HTTPException:
            pass

# 3. O Setup para o carregamento automático
async def setup(bot):
    await bot.add_cog(SAC(bot))
    

'''
===========================================================
            comando para o utilitário: !sac
===========================================================
'''
