from flask import Flask, render_template, request
import subprocess

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    output = ""
    if request.method == "POST":
        result = subprocess.run(["python3", "hotrun.py"], capture_output=True, text=True)
        output = result.stdout or result.stderr
    return render_template("index.html", output=output)

if __name__ == "__main__":
    app.run(debug=True)
