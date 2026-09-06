from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(title="Short Video Generator", version="0.1.0")

    @app.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app

