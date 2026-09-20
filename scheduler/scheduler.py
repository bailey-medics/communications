"""Run scheduled events

Run events at specific times. Exits the script when all jobs are complete.
"""

import importlib
import math
import os
import signal
import sys
import threading
import uuid
from datetime import datetime, timedelta
from pathlib import Path

import zmq
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from dotenv import load_dotenv
from PIL import Image

from comms.email.email_client_hold import EmailClient
from shared.message_queue import URL


class Scheduler:
    client_folder = Path(__file__).resolve().parent.parent / "comms"
    jobs_to_run = []
    job_outputs: list[str] = []
    all_jobs_status: str = "PASS"

    def __init__(self) -> None:
        self.scheduler = BackgroundScheduler()
        self.all_jobs_completed = threading.Event()
        self.context = zmq.Context()
        self.stop_signal = self.context.socket(zmq.PAIR)
        self.stop_signal.bind("inproc://stop")
        self.stop_after_all_jobs = False

        self.stop_signal_receiver = self.context.socket(zmq.PAIR)
        self.stop_signal_receiver.connect("inproc://stop")

    def job_test(self) -> None:
        print("Hello world")

    def schedule_job(self, func, run_time, platform, id, *args, **kwargs):
        testing = False

        if testing:
            trigger = DateTrigger(
                run_date=(datetime.now() + timedelta(seconds=5))
            )
            self.scheduler.add_job(
                self.job_test,
                trigger=trigger,
                id=id,
                name=platform,
            )
        else:
            trigger = DateTrigger(run_date=run_time)
            self.scheduler.add_job(
                func,
                trigger,
                args=args,
                kwargs=kwargs,
                replace_existing=True,
                misfire_grace_time=120,
                id=id,
                name=platform,
            )
        print("Job scheduled")

    def shutdown(self, signum=None, frame=None) -> None:
        print("closing down via self.shutdown")
        self.scheduler.shutdown(wait=False)
        sys.exit(0)

    def data_validation(self, data: list) -> str:
        return_message = ""

        if not isinstance(data, list):
            return_message += f"Invalid variable type {type(data).__name__}\n"

        if not all(isinstance(element, dict) for element in data):
            invalid_elements = [
                type(element).__name__
                for element in data
                if not isinstance(element, dict)
            ]
            return_message += "Invalid element type(s) in list:"
            f"{', '.join(invalid_elements)}\n"

        return return_message

    def message_queue(self):
        socket = self.context.socket(zmq.REP)
        socket.bind(URL)

        poller = zmq.Poller()
        poller.register(socket, zmq.POLLIN)
        poller.register(self.stop_signal_receiver, zmq.POLLIN)

        while True:
            socks = dict(poller.poll())

            if (
                self.stop_signal_receiver in socks
                and socks[self.stop_signal_receiver] == zmq.POLLIN
            ):
                break

            if socket in socks and socks[socket] == zmq.POLLIN:
                message = socket.recv_json()
                data_assessment = self.data_validation(message)

                if data_assessment:
                    socket.send_json({"status": data_assessment})
                else:
                    return_message = ""
                    error_message = ""
                    for element in message:
                        for key, value in element.items():
                            if key == "jobs" and value == "END_OF_JOBS":
                                return_message += (
                                    "Will end scheduler after last job\n"
                                )
                                self.stop_after_all_jobs = True
                            elif key == "jobs":
                                error_message = self.schedule_post(value)
                                if not error_message:
                                    return_message += "Scheduled job\n"
                            else:
                                return_message += "Unknown message\n"

                    if error_message:
                        socket.send_json(
                            {"status": "error", "message": error_message}
                        )
                    else:
                        socket.send_json(
                            {"status": "ok", "message": return_message}
                        )

        print("Shutting down scheduler")
        return

    def schedule_post(self, job: dict) -> str:
        """Schedule a post

        Schedule a post to be made on a social media platform

        Args:
            job (dict): A dictionary containing the post details
        Returns:
            str: A message indicating the success or failure of the scheduling
        """
        job_date: str | None = job.get("post_date")
        job_time: str | None = job.get("post_time")

        if not (job_time and job_date):
            return "No date and / or time specified\n"

        selected_clients: list[str] = job.get("selected_clients[]", [])
        failure_message = ""

        for client_file in selected_clients:
            module_name = client_file.replace(".py", "")
            class_name = (
                module_name.replace("_client", "").capitalize() + "Client"
            )

            sub_folder = client_file.replace("_client.py", "")
            module_path = (
                Path(self.client_folder).resolve().parent
                / "comms"
                / sub_folder
                / client_file
            )
            spec = importlib.util.spec_from_file_location(
                module_name, module_path
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            client_class = getattr(module, class_name)
            client_instance = client_class()
            requirements = client_instance.requirements()

            if (
                len(job[requirements["post"][0]])
                > requirements["max_text_length"]
            ):
                failure_message += f"Text too long for {class_name}\n"
                continue

            if "max_image_size" in requirements:
                if "image" in job:
                    image_path = job["image"]
                    image_size = os.path.getsize(image_path) / 1024

                    if image_size > requirements["max_image_size"]:
                        # Compress the image to be 10% smaller than the
                        # required size
                        max_size_kb = requirements["max_image_size"]
                        target_size_kb = max_size_kb * 0.9
                        self.compress_image(image_path, target_size_kb)

            run_time_str = f"{job_date} {job_time}"
            run_time = datetime.strptime(run_time_str, "%Y-%m-%d %H:%M")
            post_args = {
                key: job[key] for key in requirements["post"] if key in job
            }

            name = client_instance.name()

            self.jobs_to_run.append(
                (
                    client_instance.post,
                    run_time,
                    post_args,
                    class_name,
                    str(uuid.uuid4()),
                    name,
                )
            )

        if failure_message:
            self.scheduler.shutdown(wait=False)
            return failure_message

        for func, run_time, kwargs, platform, id, name in self.jobs_to_run:
            self.schedule_job(func, run_time, platform, id, **kwargs)

        return ""

    def compress_image(
        self,
        image_path: str,
        target_size_kb: float,
        reduction_factor: float = 0.75,
    ) -> None:
        """Compress an image

        Args:
            image_path (str): The path to the image file.
            target_size_kb (float): The target size in kilobytes.
        """
        with Image.open(image_path) as img:
            iteration_count = 0
            max_iterations = 20

            while iteration_count < max_iterations:
                current_size_kb = os.path.getsize(image_path) / 1024
                print(f"Current image size: {current_size_kb} KB")

                if current_size_kb <= target_size_kb:
                    break

                new_width = int(img.width * reduction_factor)
                new_height = int(img.height * reduction_factor)
                img = img.resize((new_width, new_height), Image.LANCZOS)
                img.save(image_path, optimize=True, quality=85)
                iteration_count += 1

    def job_listener(self, event):
        name = next(
            (job[5] for job in self.jobs_to_run if job[4] == event.job_id),
            "Unknown name",
        )

        if event.exception:
            exc_info = [
                str(event.exception.__class__),
                str(event.exception),
                str(event.traceback),
            ]
            full_traceback = "\n".join(exc_info)
            output = {
                "outcome": "fail",
                "message": f"{name} job, id {event.job_id}, failed:\n "
                f"{event.exception}\n"
                f"Full traceback:\n```{full_traceback}```",
            }
            self.all_jobs_status = "FAIL"
        else:
            output = {"outcome": "pass", "message": f"{name}"}

        # Store the output in the job_outputs list
        self.job_outputs.append(output)

        self.jobs_to_run = [
            job for job in self.jobs_to_run if job[4] != event.job_id
        ]
        if not self.jobs_to_run and self.stop_after_all_jobs:
            self.all_jobs_completed.set()
            self.stop_signal.send(b"STOP")
        if not self.jobs_to_run:
            self.email_results()

    def email_results(self):
        email = EmailClient()
        load_dotenv

        passed_outputs = []
        failed_outputs = []

        for output in self.job_outputs:
            if output["outcome"] == "pass":
                passed_outputs.append(output["message"])
            else:
                failed_outputs.append(output["message"])

        passed_outputs = [
            output.replace("Client", "") for output in passed_outputs
        ]
        if not passed_outputs:
            passed_outputs_html = '<div class="fail">No jobs passed</div>'
        else:
            passed_outputs_html = (
                '<div class="pass">'
                + "</br>".join(passed_outputs)
                + "</br></div>"
            )

        if not failed_outputs:
            failed_outputs_html = '<div class="pass">No jobs failed</div>'
        else:
            failed_outputs_html = (
                '<div class="fail">'
                + "</br>".join(failed_outputs)
                + "</br></div>"
            )

        passed_outputs_html = passed_outputs_html.replace("\n", "</br>")

        body = (
            "Below is the output from the social media post scheduler\n"
            "<h3>Passed</h3>"
            f"{passed_outputs_html}"
            "<h3>Failed</h3>"
            f"{failed_outputs_html}"
        )

        email.send_email(
            subject=f"{self.all_jobs_status} - Social Media Post Scheduler",
            body=body,
            to_email=os.getenv("EMAIL_ADMIN"),
        )

    def start(self):
        signal.signal(signal.SIGINT, self.scheduler.shutdown)
        signal.signal(signal.SIGTERM, self.scheduler.shutdown)

        self.scheduler.add_listener(
            self.job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR
        )
        self.scheduler.start()
        self.message_queue()
        self.scheduler.shutdown()


if __name__ == "__main__":
    scheduler = Scheduler()
    scheduler.start()
