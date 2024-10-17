import httpx
import base64
from telegram import Update
from telegram.ext import CallbackContext

async def request_image(update: Update, context: CallbackContext):
    await update.message.reply_text("Пожалуйста, отправьте изображение для описания.")


async def handle_image_description(update: Update, context: CallbackContext):
    if update.message.photo:
        # Get the highest resolution photo
        photo = update.message.photo[-1]
        file = await photo.get_file()
        file_path = f"images/{photo.file_id}.jpg"
        await file.download_to_drive(file_path)
        description = await describe_image_with_chatgpt(file_path)
        await update.message.reply_text(description)


async def describe_image_with_chatgpt(image_path):
    # Prepare the API request
    headers = {
        # 'Authorization': f'Bearer {OPENAI_API_KEY}',
        'Content-Type': 'application/json'
    }

    # Open the image and encode it as base64
    with open(image_path, 'rb') as image_file:
        image_data = base64.b64encode(image_file.read()).decode('utf-8')

    # Prepare the JSON payload
    json_payload = {
        'model': 'image-alpha-001',
        'image': image_data  # Include the base64-encoded image
    }

    # Send the request
    async with httpx.AsyncClient() as client:
        response = await client.post("OPENAI_API_URL", headers=headers, json=json_payload)

    # Handle the response
    if response.status_code == 200:
        data = response.json()
        description = data.get('description', 'Описание не доступно.')
    else:
        # Log error details and prepare user-friendly error message
        try:
            error_data = response.json()
            error_message = error_data.get('error', {}).get('message', 'Произошла ошибка при описании изображения.')
        except Exception:
            error_message = "Произошла ошибка при описании изображения. Неверный формат ответа от сервера."

        description = f"Ошибка: {error_message} (Код {response.status_code})"

    return description
