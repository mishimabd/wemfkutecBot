import io
import matplotlib
from matplotlib import pyplot as plt
from telegram import Update, InputFile
from telegram.ext import CallbackContext
from ai_assistent import ai_assistant, USER_DATA


async def ask_gfr(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    context.user_data["is_gfr_active"] = True
    USER_DATA[user.id] = {}
    await update.message.reply_text("Пожалуйста, введите ваш вес в килограммах (например, 70):")


async def handle_gfr_input(update: Update, context: CallbackContext) -> None:
    from bmi_calculator import handle_bmi_input
    user_id = update.message.from_user.id
    user_input = update.message.text
    if context.user_data.get("is_bmi_active", False):
        await handle_bmi_input(update, context)
        return
    if not context.user_data.get("is_gfr_active", False):
        await ai_assistant(update, context)
        return

    # Collect user inputs
    if "weight" not in USER_DATA[user_id]:
        try:
            USER_DATA[user_id]["weight"] = float(user_input)
            await update.message.reply_text("Теперь введите ваш возраст в годах (например, 30):")
        except ValueError:
            await update.message.reply_text("Пожалуйста, введите корректное значение веса.")
    elif "age" not in USER_DATA[user_id]:
        try:
            USER_DATA[user_id]["age"] = int(user_input)
            await update.message.reply_text("Теперь введите уровень креатинина в сыворотке (например, 1.2):")
        except ValueError:
            await update.message.reply_text("Пожалуйста, введите корректное значение возраста.")
    elif "serum_creatinine" not in USER_DATA[user_id]:
        try:
            USER_DATA[user_id]["serum_creatinine"] = float(user_input)
            await update.message.reply_text("Укажите ваш пол (мужчина/женщина):")
        except ValueError:
            await update.message.reply_text("Пожалуйста, введите корректное значение креатинина.")
    elif "gender" not in USER_DATA[user_id]:
        gender = user_input.lower()
        if gender not in ["мужчина", "женщина"]:
            await update.message.reply_text("Пожалуйста, введите корректный пол (мужчина/женщина).")
            return

        USER_DATA[user_id]["gender"] = gender

        # Calculate GFR
        weight = USER_DATA[user_id]["weight"]
        age = USER_DATA[user_id]["age"]
        serum_creatinine = USER_DATA[user_id]["serum_creatinine"]
        gfr = calculate_gfr(age, weight, serum_creatinine, gender)

        # Generate GFR chart image
        chart_image = generate_gfr_chart(gfr)

        # Reset GFR flag after calculation is complete
        context.user_data["is_gfr_active"] = False

        # Send the GFR chart as an image
        await context.bot.send_photo(chat_id=update.message.chat_id, photo=InputFile(chart_image),
                                     caption=f"Ваш GFR: {gfr:.2f} мл/мин/1.73 м²")


def calculate_gfr(age, weight, serum_creatinine, gender):
    if gender == "male":
        return ((140 - age) * weight) / (72 * serum_creatinine)
    else:  # female
        return ((140 - age) * weight) / (72 * serum_creatinine) * 0.85


def generate_gfr_chart(gfr):
    plt.rcParams['font.family'] = 'DejaVu Sans'
    plt.rcParams['font.size'] = 12
    plt.rcParams['axes.linewidth'] = 1.5
    plt.rcParams['lines.antialiased'] = True

    categories = [
        "Нормальная функция",
        "Снижение функции",
        "Тяжелое снижение функции",
        "Хроническая почечная недостаточность"
    ]

    # Thresholds for each category
    gfr_ranges = [90, 60, 30, 0]
    min_gfr_range = [0, 30, 60, 90]  # Starting point for each category
    colors = ["#2ca02c", "#ff7f0e", "#d62728", "#1f77b4"]  # Colors for the categories

    print(f"gfr_ranges: {gfr_ranges}")
    print(f"min_gfr_range: {min_gfr_range}")

    # Create the figure
    fig, ax = plt.subplots(figsize=(12, 4))
    plt.subplots_adjust(top=1.2, bottom=0.4)

    # Draw GFR ranges
    for i in range(len(categories)):
        width = gfr_ranges[i] - (gfr_ranges[i + 1] if i + 1 < len(gfr_ranges) else 0)  # Width of the bar
        if width > 0:  # Only draw if width is positive
            ax.barh("GFR", width,
                    color=colors[i],  # Use the color from the list
                    left=min_gfr_range[i],  # Starting position
                    edgecolor='black',
                    linewidth=1.2,
                    label=categories[i])

    ax.axvline(gfr, color="black", linestyle="--", linewidth=2, label=f"Ваш GFR: {gfr:.2f}")
    ax.set_xlim(0, 120)
    ax.set_xlabel("Скорость клубочковой фильтрации (GFR) (мл/мин/1.73 м²)", fontsize=14)
    ax.set_title("Ваш GFR", fontsize=16, fontweight='bold')
    ax.grid(True, which='both', axis='x', linestyle='--', linewidth=0.5)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=4, fontsize=12)

    buffer = io.BytesIO()
    plt.savefig(buffer, format="png", dpi=200, bbox_inches='tight')
    buffer.seek(0)
    plt.close(fig)
    return buffer