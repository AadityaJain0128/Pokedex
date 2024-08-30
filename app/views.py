from flask import Blueprint, render_template, redirect, request, flash, url_for, session, current_app
import os
from .pokedex import fetch_response


views = Blueprint("views", __name__)


@views.route("/")
def home():
    return render_template("index.html")


@views.route("/upload", methods=['GET', 'POST'])
def upload():
    if request.method == "POST":
        image = request.files.get("image")
        print(image)
        ext = image.filename.split(".")[-1]
        if ext.lower() not in ["jpg", "jpeg", "png"]:
            flash("Format not supported !", category="danger")
            return redirect(url_for("views.upload"))
        
        counter = os.path.join(current_app.static_folder, "counter.txt")
        with open(counter, "r") as f:
            n = int(f.read())
        with open(counter, "w") as f:
            f.write(str(n + 1))

        image_path = rf"uploaded/{n}.{ext}"
        image.save(os.path.join(current_app.static_folder, image_path))
        response, audio_path = fetch_response(os.path.join(current_app.static_folder, image_path), current_app.static_folder)
        session["data"] = response, image_path, audio_path
        return redirect(url_for("views.details"))
    
    return render_template("upload.html")


@views.route("/details")
def details():
    if not session.get("data", None):
        flash("No Recent Pokemons !", category="warning")
        return redirect("/")
    response, image_path, audio_path = session["data"]
    return render_template("details.html", response=response, image_path=image_path, audio_path=audio_path)