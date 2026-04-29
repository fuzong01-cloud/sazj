from flask import Flask, jsonify


app = Flask(__name__)


@app.get("/")
def legacy_root():
    return jsonify(
        {
            "ok": False,
            "message": "旧 Flask 页面已下线，请使用 frontend/ 和 backend/ 启动新版本。",
            "frontend": "http://127.0.0.1:5173",
            "backend_docs": "http://127.0.0.1:8000/docs",
            "predict_api": "POST http://127.0.0.1:8000/api/predict",
        }
    )


if __name__ == "__main__":
    app.run(debug=False)
