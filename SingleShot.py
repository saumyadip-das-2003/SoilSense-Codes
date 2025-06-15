import re
from joblib import load
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

BOT_TOKEN = '7927790533:AAGeonbnjCnl9LIom9rYflf-O7EsJQMir90'
MODEL = load('npk_ph_predictor.pkl')

def classify(val, thres):
    if val < thres[0]: return 'খুব কম'
    elif val < thres[1]: return 'কম'
    elif val < thres[2]: return 'মাঝারি'
    elif val < thres[3]: return 'উচ্চ'
    else: return 'খুব উচ্চ'

def generate_advice(n, p, k, ph):
    msg = f"""📊 *Prediction:*
N = {n:.0f} kg/ha
P = {p:.0f} kg/ha
K = {k:.0f} kg/ha
pH = {ph:.1f}

📌 সুপারিশ:"""
    tips = []
    if classify(n, [50, 90, 130, 170]) in ['খুব কম', 'কম']:
        tips.append("• ইউরিয়া/কম্পোস্ট সার প্রয়োগ করুন।")
    if classify(p, [20, 40, 60, 80]) in ['খুব কম', 'কম']:
        tips.append("• TSP বা ডিএপি সার দিন।")
    if classify(k, [40, 80, 120, 160]) in ['খুব কম', 'কম']:
        tips.append("• এমওপি বা ছাই প্রয়োগ করুন।")
    if ph < 5.5:
        tips.append("• চুন প্রয়োগ করে পিএইচ বাড়ান।")
    elif ph > 8:
        tips.append("• সালফার বা জৈব সার দিয়ে পিএইচ কমান।")
    if not tips:
        tips.append("• মাটি সুষম আছে, অতিরিক্ত কিছু প্রয়োজন নেই।")
    return msg + "\n" + "\n".join(tips)

async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Expect 4 comma-separated numbers
    m = re.search(r"(-?\d+\.?\d*),\s*(-?\d+\.?\d*),\s*(-?\d+\.?\d*),\s*(-?\d+\.?\d*)", update.message.text)
    if not m:
        await update.message.reply_text(
            "⚠️ Input format: Temp,Humidity,Rain,Moisture\n"
            "Example: 27.5,75.0,1423,3850"
        )
        return
    try:
        t, h, r, moisture = map(float, m.groups())
        # Use only the first 3 values for the model
        n, p, k, ph = MODEL.predict([[t, h, r]])[0]
    except Exception as e:
        await update.message.reply_text(f"❌ Prediction failed: {str(e)}")
        return

    msg = (
        "*SoilSense Data*\n"
        "`Temp(°C),Humidity(%),Rain(mm),Moisture`\n"
        f"{t},{h},{r},{moisture}\n"
        "\n*Predicted [N, P, K, pH]*\n"
        f"`N = {n:.0f}, P = {p:.0f}, K = {k:.0f}, pH = {ph:.2f}`\n\n"
        + generate_advice(n, p, k, ph)
    )
    await update.message.reply_text(msg, parse_mode='Markdown')

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handler))
    print("Bot is running...")
    app.run_polling()
