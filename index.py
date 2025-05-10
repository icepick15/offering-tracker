from app import create_app
from waitress import serve

app = create_app()
# Render looks for a variable named `app` (already correct)

if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=10000)  # or port=8000; Render overrides it anyway
