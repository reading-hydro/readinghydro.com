#! /usr/bin/python3
import threading
import time

import uvicorn

from alert_web import app
from alert_worker import AlertWorker


def _run_asgi_server():
    uvicorn.run(app, host='0.0.0.0', port=8080, log_config=None)


def main():
    web_thread = threading.Thread(
        target=_run_asgi_server,
        name='alert-asgi-server',
        daemon=True,
    )
    web_thread.start()
    worker = AlertWorker()
    try:
        while True:
            worker.run_once()
            time.sleep(30)
    finally:
        worker.stop()


if __name__ == '__main__':
    main()
