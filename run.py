from app import app
from waitress import serve

serve(app, host="127.0.0.1", port=5000, max_request_body_size=100 * 1024 * 1024)


if __name__ == "__main__":
    app.run(debug=True)

