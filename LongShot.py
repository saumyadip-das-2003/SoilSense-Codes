import pandas as pd
from io import StringIO, BytesIO
from joblib import load
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

BOT_TOKEN = '7927790533:AAGeonbnjCnl9LIom9rYflf-O7EsJQMir90'
MODEL = load('npk_ph_predictor.pkl')
MODEL_FEATURES = MODEL.feature_names_in_

def classify(val, thres):
    if val < thres[0]: return 'খুব কম'
    elif val < thres[1]: return 'কম'
    elif val < thres[2]: return 'মাঝারি'
    elif val < thres[3]: return 'উচ্চ'
    else: return 'খুব উচ্চ'

def suggest(row):
    tips = []
    if classify(row['N(kg/ha)'], [50,90,130,170]) in ['খুব কম','কম']: tips.append("ইউরিয়া")
    if classify(row['P(kg/ha)'], [20,40,60,80]) in ['খুব কম','কম']: tips.append("TSP")
    if classify(row['K(kg/ha)'], [40,80,120,160]) in ['খুব কম','কম']: tips.append("MOP")
    if row['pH'] < 5.5: tips.append("চুন")
    elif row['pH'] > 8: tips.append("সালফার/জৈব সার")
    return " | ".join(tips) if tips else "সুষম অবস্থা"

async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    # Remove code block markers if present
    if text.startswith("```") and text.endswith("```"):
        text = text.strip("`").lstrip("csv").strip()
    try:
        df = pd.read_csv(StringIO(text))
        # Standardize columns: lowercase, remove spaces, replace with underscores
        df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]
        # Try to match model features to input columns
        feature_mapping = {}
        for feat in MODEL_FEATURES:
            candidates = [c for c in df.columns if c.replace('_', '').replace('-', '') == feat.replace('_', '').replace('-', '')]
            if candidates:
                feature_mapping[feat] = candidates[0]
            else:
                await update.message.reply_text(f"❌ Column missing for model input: {feat}")
                return
        input_features = df[[feature_mapping[feat] for feat in MODEL_FEATURES]]
        preds = MODEL.predict(input_features)
        df[['N(kg/ha)', 'P(kg/ha)', 'K(kg/ha)', 'pH']] = preds
        df['Suggestion (Bangla)'] = df.apply(suggest, axis=1)
        bio = BytesIO()
        df.to_csv(bio, index=False, encoding='utf-8-sig')
        bio.seek(0)
        await update.message.reply_document(
            InputFile(bio, filename='SoilSense_Prediction.csv'),
            caption="✅ Predicted NPK, pH and suggestions attached."
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Invalid CSV data or internal error: {e}")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handler))
app.run_polling()
