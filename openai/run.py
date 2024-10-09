from app import create_app
from app.routes import iniciar_bot_telegram
import os
from dotenv import load_dotenv

load_dotenv()

app = create_app()

if __name__ == "__main__":
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
    WEBHOOK_URL = 'https://af51-187-32-212-210.ngrok-free.app/telegram_webhook'  # Substitua pelo URL do seu webhook
    
    if TELEGRAM_TOKEN and WEBHOOK_URL:
        iniciar_bot_telegram(TELEGRAM_TOKEN, WEBHOOK_URL)
    else:
        print("O TOKEN do Telegram ou a URL do webhook não foi encontrada no ambiente.")
    
    app.run(debug=True)
