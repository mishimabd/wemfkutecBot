import os
import aiohttp
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

class_translation = {
    'glioma': 'Глиома',
    'meningioma': 'Менингиома',
    'pituitary': 'Аденома гипофиза',
    'no tumor': 'Отсутствие опухоли',
    'Pneumonia': 'Пневмония',
    'COVID-19': 'COVID-19',
    'Normal': 'Нормально'
}


async def handle_image_upload(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Get the photo
    photo = update.message.photo[-1]  # Get the highest resolution photo
    file = await context.bot.get_file(photo.file_id)

    # Download the image as a byte array
    image_data = await file.download_as_bytearray()

    # Determine the analysis type based on context
    analysis_type = context.user_data.get('analysis_type', 'ecg')  # Default to ECG if not set

    # Define the prediction endpoint based on analysis type
    endpoint = {
        'ecg': 'http://91.147.92.32:9999/predict/ecg',
        'mri': 'http://91.147.92.32:9999/predict/mri',
        'xray': 'http://91.147.92.32:9999/predict/xray',
    }.get(analysis_type)

    # Send the image to the prediction endpoint
    if endpoint:
        async with aiohttp.ClientSession() as session:
            form_data = aiohttp.FormData()
            form_data.add_field('file', image_data, filename='image.jpg')

            async with session.post(endpoint, data=form_data) as response:
                if response.status == 200:
                    json_response = await response.json()
                    print(json_response)

                    # Handle ECG results
                    if analysis_type == 'ecg':
                        predicted_description = json_response.get('predicted_class_description', 'Описание недоступно')
                        confidence = json_response.get('confidence', 'Неизвестно')

                        readable_message = (
                            f"🔍 *Ваш анализ готов!*\n\n"
                            f"На основании предоставленного изображения:\n\n"
                            f"- Мы обнаружили: *{predicted_description}*.\n"
                            f"- Вероятность в этом результате составляет *{confidence}*.\n\n"
                            f"Спасибо, что доверяете нам для анализа ваших данных! Если у вас есть вопросы, пожалуйста, обращайтесь."
                        )

                    # Handle MRI-specific result with class confidences
                    elif analysis_type == 'mri':
                        predicted_class = json_response.get('predicted_class', 'Неизвестно')
                        confidence = json_response.get('confidence', 'Неизвестно')
                        class_confidences = json_response.get('class_confidences', {})

                        # Translate classes into Russian terms
                        translated_predicted_class = class_translation.get(predicted_class, predicted_class)
                        translated_confidences = {
                            class_translation.get(cls, cls): conf for cls, conf in class_confidences.items()
                        }

                        # Construct a message showing all the class confidences
                        class_confidences_str = '\n'.join(
                            [f"- {cls}: {conf}%" for cls, conf in translated_confidences.items()])

                        readable_message = (
                            f"🔍 *Ваш анализ МРТ готов!*\n\n"
                            f"На основании предоставленного изображения:\n\n"
                            f"- Мы обнаружили: *{translated_predicted_class}*.\n"
                            f"- Вероятность в этом результате составляет *{confidence}%*.\n\n"
                            f"Другие возможные диагнозы и их вероятности:\n"
                            f"{class_confidences_str}\n\n"
                            f"Спасибо, что доверяете нам для анализа ваших данных! Если у вас есть вопросы, пожалуйста, обращайтесь."
                        )

                    # Handle X-ray specific result
                    elif analysis_type == 'xray':
                        predicted_class = json_response.get('predicted_class', 'Неизвестно')
                        confidence = json_response.get('confidence', 'Неизвестно')
                        class_confidences = json_response.get('class_confidences', {})

                        # Translate classes into Russian terms
                        translated_predicted_class = class_translation.get(predicted_class, predicted_class)
                        translated_confidences = {
                            class_translation.get(cls, cls): conf for cls, conf in class_confidences.items()
                        }

                        # Construct a message showing all the class confidences
                        class_confidences_str = '\n'.join(
                            [f"- {cls}: {conf}%" for cls, conf in translated_confidences.items()])

                        readable_message = (
                            f"🔍 *Ваш анализ Рентгена готов!*\n\n"
                            f"На основании предоставленного изображения:\n\n"
                            f"- Мы обнаружили: *{translated_predicted_class}*.\n"
                            f"- Вероятность в этом результате составляет *{confidence}%*.\n\n"
                            f"Другие возможные диагнозы и их вероятности:\n"
                            f"{class_confidences_str}\n\n"
                            f"Спасибо, что доверяете нам для анализа ваших данных! Если у вас есть вопросы, пожалуйста, обращайтесь."
                        )

                    # Send the response message
                    await update.message.reply_text(readable_message, parse_mode='Markdown')

                else:
                    # Handle non-200 response
                    await update.message.reply_text(
                        "Извините, произошла ошибка при анализе изображения. Пожалуйста, попробуйте снова.")
    else:
        # Handle missing analysis type case
        await update.message.reply_text("Анализ не был выбран. Пожалуйста, выберите один из анализов.")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Обработка отменена.")
    return ConversationHandler.END


async def ecg(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data['analysis_type'] = 'ecg'  # Set the analysis type to ECG
    await update.message.reply_text(
        "Отправьте, пожалуйста, фото ЭКГ (жкг). Вот пример фотки: 🏥"
    )
    photo_path = "example.jpeg"  # Replace with the actual path to your example photo
    await update.message.reply_photo(open(photo_path, 'rb'))


async def mri(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data['analysis_type'] = 'mri'  # Set the analysis type to MRI
    await update.message.reply_text(
        "Отправьте, пожалуйста, фото МРТ. Вот пример фотки: 🏥"
    )
    photo_path = "example_mri.jpg"  # Replace with the actual path to your example photo
    await update.message.reply_photo(open(photo_path, 'rb'))


async def xray(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data['analysis_type'] = 'xray'  # Set the analysis type to X-Ray
    await update.message.reply_text(
        "Отправьте, пожалуйста, фото ХРЕЙ легких. Вот пример фотки: 🏥"
    )
    photo_path = "example_xray.jpeg"  # Replace with the actual path to your example photo
    await update.message.reply_photo(open(photo_path, 'rb'))

