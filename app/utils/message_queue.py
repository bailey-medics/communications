import os
import subprocess

import zmq

from shared.message_queue import URL


class SchedulerMessage:
    def __init__(self) -> None:
        if not self.is_scheduler_running():
            print("Scheduler is not running. Starting scheduler...")
            self.start_scheduler()
        else:
            print("Scheduler is already running.")

    def is_scheduler_running(self) -> bool:
        try:
            # Check if the scheduler process is running
            output = subprocess.check_output(
                ["pgrep", "-f", "scheduler/scheduler.py"]
            )
            return bool(output.strip())
        except subprocess.CalledProcessError:
            # pgrep returns non-zero exit status if no process is found
            return False

    def start_scheduler(self):
        current_dir = os.path.dirname(__file__)
        scheduler_path = os.path.join(
            current_dir, "../../scheduler/scheduler.py"
        )
        subprocess.Popen(["python3", scheduler_path], start_new_session=True)

    def scheduler_message(self, message) -> dict[str, str]:
        context = zmq.Context()
        socket = context.socket(zmq.REQ)
        socket.connect(URL)
        socket.setsockopt(zmq.RCVTIMEO, 20000)
        socket.setsockopt(zmq.LINGER, 0)

        try:
            socket.send_json(message)
            response = socket.recv_json()
            print(f"Received reply: {response}")
            return response
        except zmq.error.Again:
            print("No response from scheduler")
        finally:
            socket.close()
            context.term()

        return {"status": "error", "message": "No response from scheduler"}
