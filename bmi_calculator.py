import io
import matplotlib
from matplotlib import pyplot as plt
from telegram import Update, InputFile
from telegram.ext import CallbackContext
from ai_assistent import USER_DATA, ai_assistant
from gfr_calculator import handle_gfr_input


async def ask_weight(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    context.user_data["is_bmi_active"] = True  # Set BMI active flag to True when button is pressed
    USER_DATA[user.id] = {}  # Initialize user data for BMI
    await update.message.reply_text("Пожалуйста, введите ваш вес в килограммах (например, 70):")


# Function to handle BMI inputs for both weight and height (height in centimeters)
def generate_bmi_chart(bmi):
    # Настройка шрифтов и сглаживания
    matplotlib.rcParams['font.family'] = 'DejaVu Sans'
    matplotlib.rcParams['font.size'] = 12
    matplotlib.rcParams['axes.linewidth'] = 1.5
    matplotlib.rcParams['lines.antialiased'] = True

    categories = ["Недостаточный вес", "Нормальный вес", "Избыточный вес", "Ожирение"]
    bmi_ranges = [18.5, 24.9, 29.9, 40]  # Максимальные значения для каждой категории
    min_bmi_range = [0, 18.5, 24.9, 29.9]  # Минимальные значения для каждой категории
    colors = ["#1f77b4", "#2ca02c", "#ff7f0e", "#d62728"]  # Более приятные цвета

    # Создаем график с увеличенным размером
    fig, ax = plt.subplots(figsize=(12, 4))  # Увеличиваем ширину и высоту графика

    # Добавляем отступы сверху и снизу
    plt.subplots_adjust(top=1.2, bottom=0.4)  # Отступ сверху 15%, снизу 25%

    # Рисуем диапазоны ИМТ для каждой категории
    for i in range(len(categories)):
        ax.barh("ИМТ", bmi_ranges[i] - min_bmi_range[i],
                color=colors[i],
                left=min_bmi_range[i],
                edgecolor='black',
                linewidth=1.2,
                label=categories[i])
    ax.axvline(bmi, color="black", linestyle="--", linewidth=2, label=f"Ваш ИМТ: {bmi:.2f}")
    ax.set_xlim(0, 40)  # Устанавливаем диапазон оси X от 0 до 40
    ax.set_xlabel("Индекс Массы Тела (ИМТ)", fontsize=14)
    ax.set_title("Ваш Индекс Массы Тела", fontsize=16, fontweight='bold')
    ax.grid(True, which='both', axis='x', linestyle='--', linewidth=0.5)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=4, fontsize=12)
    buffer = io.BytesIO()
    plt.savefig(buffer, format="png", dpi=200, bbox_inches='tight')
    buffer.seek(0)
    plt.close(fig)
    return buffer


async def handle_bmi_input(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    user_input = update.message.text
    if context.user_data.get("is_gfr_active", False):
        await handle_gfr_input(update, context)
        return

    if not context.user_data.get("is_bmi_active", False):
        await ai_assistant(update, context)
        return

    # Proceed with BMI logic if the flag is set to True
    if "weight" not in USER_DATA[user_id]:
        try:
            weight = float(user_input)
            USER_DATA[user_id]["weight"] = weight
            await update.message.reply_text("Теперь введите ваш рост в сантиметрах (например, 175):")
        except ValueError:
            await update.message.reply_text("Пожалуйста, введите корректное значение веса.")
    else:
        try:
            height_cm = float(user_input)
            USER_DATA[user_id]["height"] = height_cm

            weight = USER_DATA[user_id]["weight"]
            if height_cm <= 0:
                await update.message.reply_text("Пожалуйста, введите положительное значение роста.")
                return

            # Convert height from centimeters to meters
            height_m = height_cm / 100.0

            # Calculate BMI
            bmi = calculate_bmi(weight, height_m)
            category = bmi_category(bmi)

            # Generate BMI chart image
            chart_image = generate_bmi_chart(bmi)

            # Reset BMI flag after calculation is complete
            context.user_data["is_bmi_active"] = False

            # Send the BMI chart as an image
            await context.bot.send_photo(chat_id=update.message.chat_id, photo=InputFile(chart_image), caption=f"Ваш ИМТ: {bmi:.2f}\nКатегория: {category}")

        except ValueError:
            await update.message.reply_text("Пожалуйста, введите корректное значение роста.")


# BMI calculation functions
def calculate_bmi(weight, height):
    """ Calculate BMI from weight (kg) and height (m). """
    return weight / (height ** 2)


def bmi_category(bmi):
    """ Determine the BMI category based on the calculated BMI. """
    if bmi < 18.5:
        return "Недостаточный вес"
    elif 18.5 <= bmi < 24.9:
        return "Нормальный вес"
    elif 25 <= bmi < 29.9:
        return "Избыточный вес"
    else:
        return "Ожирение"