from flask import Flask, jsonify

app = Flask(__name__)


@app.get("/")
def index():
    return jsonify(
        {
            "message": "secure-by-default demo is running",
            "service": "secure-by-default-demo",
            "status": "ok",
        }
    )


@app.get("/healthz")
def healthz():
    return jsonify({"status": "healthy"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)