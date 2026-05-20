import discord
from discord.ext import commands
import aiohttp
import os
import asyncio

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.render_key = os.getenv('RENDER_API_KEY')
        self.uptime_key = os.getenv('UPTIMEROBOT_API_KEY')
        self.service_id = os.getenv('RENDER_SERVICE_ID')

    # === VERIFICAÇÃO NATIVA DE CARGO ===
    @commands.command(name='status')
    async def status_sistema(self, ctx):
        id_cargo_env = os.getenv('ROLE_ID')
        
        # Validação prévia do cargo
        tem_permissao = False
        if id_cargo_env and hasattr(ctx.author, 'roles'):
            tem_permissao = any(role.id == int(id_cargo_env) for role in ctx.author.roles)

        # --- CASO NÃO TENHA PERMISSÃO (Apaga em 5 segundos) ---
        if not tem_permissao:
            msg_aviso = await ctx.send("❌ **ERRO:** Você não possui o Cargo de Elite configurado para monitorar meus sinais vitais! Suma daqui, plebeu! 💢")
            
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

        # --- CASO TENHA PERMISSÃO (O código legítimo roda aqui) ---
        msg_aguarde = await ctx.send("🔍 Verificando sinais vitais da mana... aguarde.")
        
        relatorio = "📝 **RELATÓRIO DE SAÚDE - V1.2**\n\n"
        
        # Usando aiohttp para chamadas assíncronas
        async with aiohttp.ClientSession() as session:
            
            # --- Verificação RENDER ---
            try:
                headers = {"Authorization": f"Bearer {self.render_key}"}
                async with session.get(f"https://api.render.com/v1/services/{self.service_id}", headers=headers) as r:
                    if r.status == 200:
                        data = await r.json()
                        status = data.get('suspended', 'Ativo')
                        relatorio += f"🟢 **Render:** {'Suspenso' if status == 'suspended' else 'Rodando Liso'}\n"
                    else:
                        relatorio += f"🔴 **Render:** Erro na comunicação (Status: {r.status})\n"
            except Exception:
                relatorio += "⚠️ **Render:** Fora de alcance.\n"

            # --- Verificação UPTIME ROBOT ---
            try:
                payload = {"api_key": self.uptime_key, "format": "json"}
                async with session.post("https://api.uptimerobot.com/v2/getMonitors", data=payload) as u:
                    if u.status == 200:
                        data = await u.json()
                        monitor = data['monitors'][0]
                        status_up = "Online" if monitor['status'] == 2 else "Offline/Pausado"
                        relatorio += f"🟢 **UptimeRobot:** {status_up} (Monitor: {monitor['friendly_name']})\n"
                    else:
                        relatorio += f"🔴 **UptimeRobot:** Erro na API (Status: {u.status}).\n"
            except Exception:
                relatorio += "⚠️ **UptimeRobot:** Sem resposta.\n"

        # Envia o relatório final e guarda a mensagem na variável
        msg_relatorio = await ctx.send(relatorio)

        # Espera os 15 segundos solicitados com o relatório na tela
        await asyncio.sleep(15)

        # --- Faxina no Chat (Apaga tudo do caso de sucesso) ---
        try:
            await msg_aguarde.delete() # Apaga o "Verificando..."
        except discord.HTTPException:
            pass

        try:
            await msg_relatorio.delete() # Apaga o Relatório
        except discord.HTTPException:
            pass
            
        try:
            if ctx.guild:
                await ctx.message.delete() # Apaga o "!status" enviado pelo usuário
        except discord.HTTPException:
            pass

async def setup(bot):
    await bot.add_cog(Admin(bot))
             
"""
===================================================================
           comando para usar este utilitário: !status
===================================================================

"""
