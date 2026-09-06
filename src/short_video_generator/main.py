import uvicorn

from short_video_generator.api.app import create_app

app = create_app()


def run() -> None:
    uvicorn.run("short_video_generator.main:app", host="127.0.0.1", port=8000)


if __name__ == "__main__":
    run()

