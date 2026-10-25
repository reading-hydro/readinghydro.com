#! /usr/bin/python3
import threading

import uvicorn

from alert_web import app
from mqtt_worker import run_worker


def _run_asgi_server():
    uvicorn.run(app, host='0.0.0.0', port=8080, log_config=None)


def main():
    web_thread = threading.Thread(
        target=_run_asgi_server,
        name='alert-asgi-server',
        daemon=True,
    )
    web_thread.start()
    run_worker()


if __name__ == '__main__':
    main()
