"""Run separately for WSGI deployments: python -m services.deadline_worker."""
from services import email_service


def main():
    email_service.start_deadline_worker()
    if email_service._worker is None:
        return
    try:
        email_service._worker.join()
    except KeyboardInterrupt:
        email_service._worker_stop.set()
        email_service._worker.join(timeout=5)


if __name__ == '__main__':
    main()
