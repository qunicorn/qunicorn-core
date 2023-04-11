from qunicorn_core.celery import CELERY
import time

@CELERY.task()
def createJob():
    print("Job Registered")
    time.sleep(5)
    print("Job complete")
    return 0
