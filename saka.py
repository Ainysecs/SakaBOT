import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from keep_alive import keep_alive

load_dotenv()

# --- ---
intents = discord.Intents.all()

class MeuBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Carrega os módulos da pasta cogs
        print("📂 Carregando módulos...")
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                try:
                    await self.load_extension(f'cogs.{filename[:-3]}')
                    print(f"✅ Cog {filename} carregada com sucesso!")
                except Exception as e:
                    print(f"❌ Erro ao carregar {filename}: {e}")
        
        try:
            from cogs.sac import ViewSAC
            self.add_view(ViewSAC())
            print("✅ Saka Persistente Ativada!")
        except Exception as e:
            print(f"⚠️ View da Saka não encontrada ou erro: {e}")

    async def on_ready(self):
        print(f'🚀 {self.user.name} ONLINE e pronta para o deboche!')

# --- INICIALIZAÇÃO ---
keep_alive()

bot = MeuBot()

# Verificação de segurança: print do Token (só os primeiros dígitos para teste)
token = os.getenv('DISCORD_TOKEN')
if token:
    print(f"🪙 Token carregado: {token[:10]}...")
else:
    print("❌ ERRO: Token não encontrado no .env")

bot.run(token)
