import io
import logging
import os
import sys
from pathlib import Path

import discord
from discord.ext import commands
from dotenv import load_dotenv

from config.config import bot_config
from keep_alive import keep_alive

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('saka.core')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
# intents.members = True # rastreia quem entra/sai, dar cargos automáticos, etc (sla, opção nova para quem quiser)

class SakaBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=commands.when_mentioned_or("!"),
            intents=intents,
            help_command=None
        )
        self.config = bot_config

    async def setup_hook(self):
        chaves = len(self.config.get_all())
        logger.info(f"⚙️ Configurações prontas! {chaves} chaves carregadas.")

        logger.info("📂 Escaneando diretório 'cogs'...")
        cogs_dir = Path("cogs")
        cogs_dir.mkdir(exist_ok=True)

        for py_file in cogs_dir.rglob("*.py"):
            if py_file.name.startswith("__"): 
                continue

            cog_path = ".".join(py_file.with_suffix("").parts)
            try:
                await self.load_extension(cog_path)
                logger.info(f"✅ Módulo carregado: {cog_path}")
            except Exception as e:
                logger.error(f"❌ Falha crítica ao carregar {cog_path}: {e}", exc_info=True)

    async def on_ready(self):
        logger.info(f"🚀 {self.user.name} is now ONLINE! 💅")
        
        atividade = discord.Game(name="Julgando plebeus no SEO 💅")
        
        await self.change_presence(status=discord.Status.online, activity=atividade)

def main():
    if os.getenv("RENDER"):
        try:
            keep_alive()
            logger.info("🌐 Ambiente de produção detectado no Render. keep_alive ativado.")
        except Exception as e:
            logger.error(f"❌ Erro crítico ao iniciar o servidor keep_alive: {e}")
    else:
        logger.info("💻 Ambiente local detectado. keep_alive ignorado.")

    bot = SakaBot()
    token = os.getenv('DISCORD_TOKEN')

    if not token:
        logger.critical("❌ Falha de Autenticação: DISCORD_TOKEN não encontrado no .env")
        sys.exit(1)

    bot.run(token, log_handler=None)

if __name__ == "__main__":
    main()
