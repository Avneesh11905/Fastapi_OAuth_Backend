import uvicorn
from src.shared.config import app_settings
def main():
    uvicorn.run("src:app", host="0.0.0.0", port=8000,    reload=(app_settings.ENV == "development"),)

if __name__ == "__main__":
    main()
