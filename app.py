from flask import Flask, render_template, request, jsonify
from PIL import Image
import numpy as np
import tensorflow as tf
from openai import OpenAI
from dotenv import load_dotenv
import requests
import os
import json
import re

load_dotenv()

app = Flask(__name__)

# ----------------------------
# 基础配置
# ----------------------------
MODEL_PATH = os.getenv("MODEL_PATH", "final_model.h5")

# 你如果用的是中国大陆平台 key，这里默认用 .cn
# 如果你用的是 .ai 平台的 key，就在 .env 里改成 https://api.moonshot.ai/v1
MOONSHOT_API_KEY = os.getenv("MOONSHOT_API_KEY", "")
MOONSHOT_BASE_URL = os.getenv("MOONSHOT_BASE_URL", "https://api.moonshot.cn/v1")
MOONSHOT_MODEL = os.getenv("MOONSHOT_MODEL", "kimi-k2.5")

class_names = {
    0: "马铃薯早疫病",
    1: "马铃薯晚疫病",
    2: "叶片健康"
}

WEATHER_CODE_MAP = {
    0: "晴朗",
    1: "大部晴朗",
    2: "局部多云",
    3: "阴天",
    45: "有雾",
    48: "冻雾",
    51: "小毛毛雨",
    53: "毛毛雨",
    55: "强毛毛雨",
    56: "冻毛毛雨",
    57: "强冻毛毛雨",
    61: "小雨",
    63: "中雨",
    65: "大雨",
    66: "冻雨",
    67: "强冻雨",
    71: "小雪",
    73: "中雪",
    75: "大雪",
    77: "雪粒",
    80: "阵雨",
    81: "中等阵雨",
    82: "强阵雨",
    85: "阵雪",
    86: "强阵雪",
    95: "雷暴",
    96: "雷暴伴小冰雹",
    99: "雷暴伴强冰雹"
}

model = None
model_load_error = None

try:
    if os.path.exists(MODEL_PATH):
        model = tf.keras.models.load_model(MODEL_PATH, compile=False)
    else:
        model_load_error = f"未找到模型文件：{MODEL_PATH}"
except Exception as e:
    model_load_error = f"模型加载失败：{str(e)}"

# 模型预热，减少首次推理等待
if model is not None:
    try:
        dummy = np.zeros((1, 256, 256, 3), dtype=np.float32)
        model.predict(dummy, verbose=0)
        print("模型预热完成")
    except Exception as e:
        print("模型预热失败：", e)

moonshot_client = None
if MOONSHOT_API_KEY:
    try:
        moonshot_client = OpenAI(
            api_key=MOONSHOT_API_KEY,
            base_url=MOONSHOT_BASE_URL
        )
        print("Moonshot 客户端初始化成功")
    except Exception as e:
        print("Moonshot 客户端初始化失败：", e)
else:
    print("未检测到 MOONSHOT_API_KEY，AI 分析将使用兜底逻辑")


# ----------------------------
# 工具函数
# ----------------------------
def weather_code_to_text(code):
    return WEATHER_CODE_MAP.get(code, "未知天气")


def confidence_label(confidence):
    if confidence >= 0.85:
        return "模型把握较高"
    elif confidence >= 0.60:
        return "模型把握一般"
    return "模型把握较低，建议补充更多清晰图片"


def clean_json_text(text: str):
    if not text:
        return ""

    text = text.strip()

    text = re.sub(r"^```json\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^```", "", text)
    text = re.sub(r"```$", "", text)

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        text = match.group(0)

    return text.strip()


def ensure_list(value, default_text):
    if value is None:
        return [default_text]
    if isinstance(value, list):
        return [str(x) for x in value if str(x).strip()] or [default_text]
    if isinstance(value, str):
        value = value.strip()
        return [value] if value else [default_text]
    return [str(value)]


def parse_kimi_json(content: str):
    text = clean_json_text(content)
    if not text:
        return None

    try:
        data = json.loads(text)
        return {
            "severity": str(data.get("severity", "待确认")),
            "risk_level": str(data.get("risk_level", "中")),
            "reason": ensure_list(data.get("reason"), "暂无 AI 分析内容。"),
            "treatment": ensure_list(data.get("treatment"), "暂无 AI 治理建议。"),
            "weather_advice": ensure_list(data.get("weather_advice"), "暂无天气相关建议。"),
            "warning": ensure_list(data.get("warning"), "请结合更多叶片图片和实际情况继续观察。")
        }
    except Exception:
        return None


def preprocess_image(image: Image.Image):
    image = image.convert("RGB")
    image = image.resize((256, 256))
    image = tf.keras.utils.img_to_array(image)
    image = image / 255.0
    image = np.expand_dims(image, axis=0)
    return image


def predict_image(image: Image.Image):
    if model is None:
        raise RuntimeError(model_load_error or "模型未成功加载")

    input_data = preprocess_image(image)
    prediction = model.predict(input_data, verbose=0)[0]

    result_index = int(np.argmax(prediction))
    result_text = class_names[result_index]
    confidence = float(prediction[result_index])

    confidence_detail = {}
    for idx, prob in enumerate(prediction):
        confidence_detail[class_names[idx]] = round(float(prob) * 100, 2)

    return result_text, confidence, confidence_detail


def fallback_ai_analysis(result_text, confidence, weather=None):
    weather_advice = []
    risk_level = "中"

    if weather:
        humidity = weather.get("humidity")
        condition = weather.get("condition", "")
        temp = weather.get("temperature")

        if isinstance(humidity, (int, float)) and humidity >= 80:
            weather_advice.append("当前湿度较高，叶面长时间潮湿时病斑更容易扩展。")
            risk_level = "中高"

        if "雨" in str(condition) or "雷" in str(condition):
            weather_advice.append("当前或近期有降水特征时，建议加强巡查，留意新叶是否继续出现病斑。")
            risk_level = "高" if risk_level == "中高" else "中高"

        if isinstance(temp, (int, float)) and 15 <= temp <= 25:
            weather_advice.append("当前温度条件对部分叶部病害扩展相对有利，应提高观察频率。")

    if result_text == "叶片健康":
        return {
            "severity": "无明显病害",
            "risk_level": "低",
            "reason": [
                "当前图片中未见明显典型病斑，整体更接近健康叶片表现。",
                f"本次识别置信度约为 {round(confidence * 100, 1)}%，结果偏向健康。"
            ],
            "treatment": [
                "继续保持通风、合理浇水和日常巡查。",
                "若后续出现斑点、萎蔫或扩散迹象，建议重新拍照识别。"
            ],
            "weather_advice": weather_advice or ["当前无明显病害，但仍建议结合天气变化进行日常观察。"],
            "warning": [
                "单张图片只能辅助判断，不能替代田间连续观察。",
                "建议多角度、多叶片拍摄以提高稳定性。"
            ]
        }

    if result_text == "马铃薯晚疫病":
        default_reason = [
            "叶片病斑形态与晚疫病常见表现较为接近。",
            f"本次识别置信度约为 {round(confidence * 100, 1)}%，模型更倾向于晚疫病。"
        ]
        default_treatment = [
            "及时清理明显病叶，减少继续扩散的机会。",
            "尽量保持通风，避免叶面长时间潮湿和田间积水。",
            "连续阴雨或湿度偏高时，应增加巡查频率。"
        ]
    else:
        default_reason = [
            "叶片斑点特征与早疫病常见表现较为接近。",
            f"本次识别置信度约为 {round(confidence * 100, 1)}%，模型更倾向于早疫病。"
        ]
        default_treatment = [
            "及时剪除明显病斑叶片并清理残叶。",
            "保持种植区通风，避免密植和叶面长期潮湿。",
            "后续重点观察病斑是否继续扩大或增多。"
        ]

    return {
        "severity": "中度",
        "risk_level": risk_level,
        "reason": default_reason,
        "treatment": default_treatment,
        "weather_advice": weather_advice or ["建议结合当前天气条件持续观察叶片变化。"],
        "warning": [
            "AI 结果仅供辅助参考，请结合多张图片和实际田间情况判断。",
            "若病斑扩展较快，建议尽快咨询当地农技人员。"
        ]
    }


def build_weather_summary(weather):
    if not weather:
        return "未提供天气信息"

    location = weather.get("location", "未知地区")
    temperature = weather.get("temperature", "未知")
    condition = weather.get("condition", "未知")
    humidity = weather.get("humidity", "未知")
    wind_speed = weather.get("wind_speed", "未知")

    return (
        f"地区：{location}；"
        f"温度：{temperature}℃；"
        f"天气：{condition}；"
        f"湿度：{humidity}%；"
        f"风速：{wind_speed} km/h。"
    )


def get_kimi_advice(result_text, confidence, weather=None):
    if moonshot_client is None:
        return fallback_ai_analysis(result_text, confidence, weather)

    weather_summary = build_weather_summary(weather)
    confidence_percent = round(confidence * 100, 1)

    prompt = f"""
识别结果：{result_text}
识别置信度：{confidence_percent}%
天气信息：{weather_summary}

请你输出一个严格的 JSON 对象，只能返回 JSON，不要返回多余文字。
JSON 必须包含以下字段：
severity: 字符串，取值示例：轻度 / 中度 / 重度 / 无明显病害 / 待确认
risk_level: 字符串，取值示例：低 / 中 / 中高 / 高
reason: 字符串数组，2到3条，简要说明为什么可能判断为这个结果
treatment: 字符串数组，3到4条，简要说明怎么处理
weather_advice: 字符串数组，2到3条，结合天气给建议
warning: 字符串数组，1到2条，提醒用户注意事项

要求：
1. 用中文
2. 简洁、实用、适合页面展示
3. 不要输出具体农药剂量
4. 不要夸大结论
5. 单张图片只能辅助判断，要体现谨慎表达
"""

    try:
        completion = moonshot_client.chat.completions.create(
            model=MOONSHOT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "你是农业病害识别助手，擅长把识别结果和天气信息转换成简洁中文说明与处理建议。你必须严格返回 JSON。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        content = completion.choices[0].message.content if completion.choices else ""
        parsed = parse_kimi_json(content)

        if parsed:
            return parsed

        return fallback_ai_analysis(result_text, confidence, weather)

    except Exception as e:
        print("Kimi 调用失败：", e)
        return fallback_ai_analysis(result_text, confidence, weather)


def chat_with_kimi(question, context):
    if not question.strip():
        return "请输入问题后再发送。"

    if moonshot_client is None:
        result = context.get("result", "未知结果")
        severity = context.get("severity", "待确认")
        risk_level = context.get("risk_level", "中")
        return (
            f"当前识别结果更偏向“{result}”，严重程度参考为“{severity}”，环境风险大致为“{risk_level}”。"
            " 当前没有可用的 Kimi API，我只能基于现有识别结果给出简单回答。"
        )

    short_context = {
        "result": context.get("result"),
        "confidence_percent": context.get("confidence_percent"),
        "severity": context.get("severity"),
        "risk_level": context.get("risk_level"),
        "weather": context.get("weather"),
    }

    prompt = f"""
当前上下文：
{json.dumps(short_context, ensure_ascii=False)}

用户问题：
{question}

请基于以上信息用中文简洁回答，控制在120字以内，实用、谨慎、易懂。
"""

    try:
        completion = moonshot_client.chat.completions.create(
            model=MOONSHOT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "你是农业病害智能助手，请基于上下文简洁回答。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        answer = completion.choices[0].message.content if completion.choices else ""
        answer = (answer or "").strip()

        if not answer:
            return "AI 暂时没有生成回答，请稍后重试。"

        return answer

    except Exception as e:
        print("聊天调用失败：", e)
        return "AI 问答暂时不可用，请检查 API Key 或网络后重试。"


def fetch_weather_by_coords(latitude, longitude, location_name="自动定位"):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
        "forecast_days": 3,
        "timezone": "auto"
    }

    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    current = data.get("current", {})
    daily = data.get("daily", {})

    forecast_list = []
    dates = daily.get("time", [])
    codes = daily.get("weather_code", [])
    max_temps = daily.get("temperature_2m_max", [])
    min_temps = daily.get("temperature_2m_min", [])
    pops = daily.get("precipitation_probability_max", [])

    for i in range(min(len(dates), len(codes), len(max_temps), len(min_temps))):
        forecast_list.append({
            "date": dates[i],
            "condition": weather_code_to_text(codes[i]),
            "temp_max": max_temps[i],
            "temp_min": min_temps[i],
            "precipitation_probability": pops[i] if i < len(pops) else None
        })

    result = {
        "location": location_name,
        "latitude": latitude,
        "longitude": longitude,
        "temperature": current.get("temperature_2m"),
        "humidity": current.get("relative_humidity_2m"),
        "weather_code": current.get("weather_code"),
        "condition": weather_code_to_text(current.get("weather_code")),
        "wind_speed": current.get("wind_speed_10m"),
        "forecast": forecast_list
    }
    return result


def fetch_weather_by_city(city_name):
    geo_url = "https://geocoding-api.open-meteo.com/v1/search"
    geo_params = {
        "name": city_name,
        "count": 1,
        "language": "zh",
        "format": "json"
    }

    geo_resp = requests.get(geo_url, params=geo_params, timeout=15)
    geo_resp.raise_for_status()
    geo_data = geo_resp.json()

    results = geo_data.get("results", [])
    if not results:
        raise ValueError("未找到该城市，请换一个城市名试试")

    loc = results[0]
    name = loc.get("name", city_name)
    admin1 = loc.get("admin1", "")
    country = loc.get("country", "")
    display_name = " / ".join([x for x in [name, admin1, country] if x])

    latitude = loc["latitude"]
    longitude = loc["longitude"]

    weather = fetch_weather_by_coords(latitude, longitude, display_name)
    weather["city_query"] = city_name
    return weather


# ----------------------------
# 路由
# ----------------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/weather/by-coords", methods=["POST"])
def weather_by_coords():
    try:
        data = request.get_json(silent=True) or {}
        latitude = data.get("latitude", data.get("lat"))
        longitude = data.get("longitude", data.get("lon"))

        if latitude is None or longitude is None:
            return jsonify({
                "ok": False,
                "message": "缺少经纬度参数"
            }), 400

        weather = fetch_weather_by_coords(float(latitude), float(longitude), "自动定位")
        return jsonify({
            "ok": True,
            "weather": weather
        })
    except Exception as e:
        return jsonify({
            "ok": False,
            "message": f"获取本地天气失败：{str(e)}"
        }), 500


@app.route("/weather/by-city", methods=["POST"])
def weather_by_city():
    try:
        data = request.get_json(silent=True) or {}
        city = (data.get("city") or "").strip()

        if not city:
            return jsonify({
                "ok": False,
                "message": "请输入城市名"
            }), 400

        weather = fetch_weather_by_city(city)
        return jsonify({
            "ok": True,
            "weather": weather
        })
    except Exception as e:
        return jsonify({
            "ok": False,
            "message": f"获取城市天气失败：{str(e)}"
        }), 500


# 只做模型识别，先快速返回
@app.route("/predict", methods=["POST"])
def predict():
    try:
        if model is None:
            return jsonify({
                "ok": False,
                "message": model_load_error or "模型未加载成功"
            }), 500

        file = request.files.get("file")
        if not file or not file.filename:
            return jsonify({
                "ok": False,
                "message": "请先选择一张图片"
            }), 400

        weather_json = request.form.get("weather_json", "")
        weather = None
        if weather_json:
            try:
                weather = json.loads(weather_json)
            except Exception:
                weather = None

        image = Image.open(file.stream)
        result_text, confidence, confidence_detail = predict_image(image)

        return jsonify({
            "ok": True,
            "result": result_text,
            "confidence": round(confidence, 4),
            "confidence_percent": round(confidence * 100, 2),
            "confidence_label": confidence_label(confidence),
            "confidence_detail": confidence_detail,
            "weather": weather
        })
    except Exception as e:
        return jsonify({
            "ok": False,
            "message": f"识别失败：{str(e)}"
        }), 500


# 单独做 AI 分析，后加载
@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        data = request.get_json(silent=True) or {}
        result_text = data.get("result")
        confidence = float(data.get("confidence", 0))
        weather = data.get("weather")

        if not result_text:
            return jsonify({
                "ok": False,
                "message": "缺少识别结果"
            }), 400

        ai_data = get_kimi_advice(result_text, confidence, weather)

        return jsonify({
            "ok": True,
            "severity": ai_data.get("severity", "待确认"),
            "risk_level": ai_data.get("risk_level", "中"),
            "reason": ai_data.get("reason", []),
            "treatment": ai_data.get("treatment", []),
            "weather_advice": ai_data.get("weather_advice", []),
            "warning": ai_data.get("warning", [])
        })
    except Exception as e:
        return jsonify({
            "ok": False,
            "message": f"AI 分析失败：{str(e)}"
        }), 500


@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json(silent=True) or {}
        question = (data.get("question") or "").strip()
        context = data.get("context") or {}

        if not question:
            return jsonify({
                "ok": False,
                "message": "请输入问题"
            }), 400

        answer = chat_with_kimi(question, context)

        return jsonify({
            "ok": True,
            "answer": answer
        })
    except Exception as e:
        return jsonify({
            "ok": False,
            "message": f"问答失败：{str(e)}"
        }), 500


if __name__ == "__main__":
    app.run(debug=False)