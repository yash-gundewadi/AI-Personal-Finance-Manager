from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def dashboard():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)

@app.route("/income")
def income():
    return render_template("income.html")

@app.route("/expense")
def expense():
    return render_template("expense.html")

@app.route("/budget")
def budget():
    return render_template("budget.html")

@app.route("/goal")
def goal():
    return render_template("goal.html")

@app.route("/report")
def report():
    return render_template("report.html")
