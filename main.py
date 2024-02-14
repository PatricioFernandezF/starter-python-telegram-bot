import os
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Depends
from telegram import Update, Bot
from pydantic import BaseModel
from deploy import ComfyDeployAPI


class TelegramUpdate(BaseModel):
    update_id: int
    message: dict

app = FastAPI()

# Load variables from .env file if present
load_dotenv()

# Read the variable from the environment (or .env file)
bot_token = os.getenv('BOT_TOKEN')
secret_token = os.getenv("SECRET_TOKEN")
TOKEN = os.getenv('comfyapi')
WORKFLOW=os.getenv('workflow')
# webhook_url = os.getenv('CYCLIC_URL', 'http://localhost:8181') + "/webhook/"

bot = Bot(token=bot_token)
# bot.set_webhook(url=webhook_url)
# webhook_info = bot.get_webhook_info()
# print(webhook_info)

def auth_telegram_token(x_telegram_bot_api_secret_token: str = Header(None)) -> str:
    # return true # uncomment to disable authentication
    if x_telegram_bot_api_secret_token != secret_token:
        raise HTTPException(status_code=403, detail="Not authenticated")
    return x_telegram_bot_api_secret_token

@app.post("/webhook/")
async def handle_webhook(update: TelegramUpdate, token: str = Depends(auth_telegram_token)):
    chat_id = update.message["chat"]["id"]
    text = update.message["text"]
    # print("Received message:", update.message)

    if text == "/start":
        with open('hello.gif', 'rb') as photo:
            await bot.send_photo(chat_id=chat_id, photo=photo)
        await bot.send_message(chat_id=update.effective_chat.id, text="¡Hola! Soy un bot de Telegram. Pon /prompt + el prompt")
    else:
        if text!="/prompt":
            await bot.send_message(chat_id=update.effective_chat.id, text="Procesando Prompt: "+text)
            api_key = TOKEN
            comfy_api = ComfyDeployAPI(api_key)

            # Ejemplo de cómo desplegar un workflow
            workflow_id = WORKFLOW
            run_response = comfy_api.run_workflow(workflow_id,{"input_text":text})
            print(run_response)

            # Ejemplo de cómo obtener la salida de la ejecución de un workflow
            run_id = run_response["run_id"] # Reemplaza con el run_id real obtenido después de ejecutar el workflow
            if run_id:
                output_response = comfy_api.get_workflow_run_output(run_id)
                print(output_response)

                image_info = output_response.get('outputs', [{}])[0].get('data', {}).get('images', [{}])[0]
                image_url = image_info.get('url')

                if image_url:
                    await bot.send_photo(chat_id=update.effective_chat.id, photo=image_url)
                    return  # Finaliza la función después de enviar la imagen

        else:
            await bot.send_message(chat_id=update.effective_chat.id, text="Recuerda que solo estoy programado para recibir /prompt")


    return {"ok": True}
