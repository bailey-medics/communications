import threading
import time


def test():
    def worker():
        while True:
            print("Thread is running...")
            time.sleep(1)

    # Create a non-daemon thread
    thread = threading.Thread(target=worker, daemon=False)
    thread.start()

    print("Main thread ending, but worker thread will keep running.")
