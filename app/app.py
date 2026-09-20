import os
import sys
from datetime import datetime
from pathlib import Path

import pytz
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from utils.clean_client_data import clean_client_data
from utils.llm_extract import extract_content
from utils.message_queue import SchedulerMessage

# from tests.data.created_content_data import LLM_RETURN
from werkzeug.utils import secure_filename

from shared.images import UPLOAD_FOLDER
from shared.message_queue import END_OF_JOBS
from utils_main.chatgpt_undetected import ChatGPT

sys.path.append(str(Path(__file__).resolve().parent.parent))

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///social_comms.db"
app.config["UPLOAD_FOLDER"] = (
    Path(__file__).resolve().parent.parent / UPLOAD_FOLDER
)
app.config["ALLOWED_EXTENSIONS"] = {"png", "jpg", "jpeg", "gif"}
db = SQLAlchemy(app)

media_folder = Path(__file__).resolve().parent.parent / "media"
client_folder = Path(__file__).resolve().parent.parent / "comms"


class SubmittedData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    long_blurb = db.Column(db.Text, nullable=False)
    short_blurb = db.Column(db.Text, nullable=False)
    selected_clients = db.Column(db.String(200), nullable=False)
    image = db.Column(db.String(100), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.astimezone)


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in app.config["ALLOWED_EXTENSIONS"]
    )


PROMPT_OUTLINE = """You will be creating social comms pushes. Read the information below. From this text, create a title, LinkedIn blurb (named long_blurb) and twitter blurb (named short_blurb). Wrap each section in triple single quotation marks, as below. Do not add a colon after the title, long_blurb or short_blurb. Use British English.

'''title: A title'''
'''long_blurb: A long blurb'''
'''short_blurb: A short blurb'''

Information:

"""


@app.route("/")
def index():
    return render_template("gather-content-info.html")


@app.route(
    "/created-content",
    methods=["GET", "POST"],
)
def created_context():
    if request.method == "GET":
        context = {}
        return render_template("created-content.html", context=context)

    try:
        chatgpt_client = ChatGPT()
        message = request.form["prompt"]
        prompt = f"{PROMPT_OUTLINE}{message}"
        llm_response = chatgpt_client.query(prompt)
        # llm_response = LLM_RETURN
        context = extract_content(llm_response)
    except ValueError as e:
        context = {"error": str(e)}
        return render_template("llm-return-error.html", context=context)

    return render_template("created-content.html", context=context)


@app.route("/schedule-post", methods=["POST"])
def schedule_post():
    context = {
        "title": request.form["title"],
        "long_blurb": request.form["long_blurb"],
        "short_blurb": request.form["short_blurb"],
    }

    uk_timezone = pytz.timezone("Europe/London")
    context["current_time"] = datetime.now(uk_timezone)

    image_names = [f.name for f in media_folder.iterdir() if f.is_file()]

    context["image_names"] = image_names

    # Look up all files in the subfolders of ../comms that have an ending of
    # _client.py
    comms_folder = Path(__file__).resolve().parent.parent / "comms"
    client_files = comms_folder.rglob("*_client.py")
    client_files = sorted(client_files)

    context["comms_clients"] = [
        {
            "value": file.name,
            "name": file.name.replace("_client.py", "").capitalize(),
            "selected": True,
        }
        for file in client_files
    ]

    return render_template("schedule.html", **context)


@app.route("/submit", methods=["POST"])
def submit():
    data = request.form.to_dict(flat=False)
    image_filename: str = ""

    # Handle file upload
    if "image" in request.files:
        file = request.files["image"]
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            image_filename = os.path.join(
                app.config["UPLOAD_FOLDER"], filename
            )
            file.save(image_filename)
            data["image"] = [image_filename]

    cleaned_data = clean_client_data(data)

    # Store data in the database
    timestamp_str = (
        f"{cleaned_data.get('post_date', [''])} "
        f"{cleaned_data.get('post_time', [''])}"
    )
    timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M")

    submitted_data = SubmittedData(
        title=cleaned_data.get("title", ""),
        long_blurb=cleaned_data.get("long_blurb", ""),
        short_blurb=cleaned_data.get("short_blurb", ""),
        selected_clients=",".join(cleaned_data.get("selected_clients[]", [])),
        image=image_filename,
        timestamp=timestamp,
    )

    db.session.add(submitted_data)
    db.session.commit()

    context = {"cleaned_data": cleaned_data}
    message = [
        {"jobs": cleaned_data},
        {"jobs": END_OF_JOBS},
    ]

    scheduler_message = SchedulerMessage()
    return_message = scheduler_message.scheduler_message(message)

    if return_message["status"] == "error":
        context = {"message": return_message}
        return render_template(
            "scheduler-error.html", context=context, status=500
        )

    context["return_message"] = return_message

    return render_template("submitted.html", context=context)


@app.route("/entries")
def show_entries():
    entries = SubmittedData.query.all()
    context = {"entries": entries}
    return render_template("entries.html", **context)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Create database tables
    app.run(debug=True)
