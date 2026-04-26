from flask import Blueprint, redirect, render_template

bp = Blueprint("pages", __name__)


@bp.route("/")
def home():
    return render_template("index.html")


@bp.route("/candidate")
def candidate_root():
    return redirect("/candidate/jobs")


@bp.route("/recruiter")
def recruiter_root():
    return redirect("/recruiter/dashboard")


@bp.route("/candidate/<path:page>")
def candidate_page(page: str):
    allowed = {"register.html", "login.html", "jobs.html", "apply.html", "applications.html"}
    name = page if page.endswith(".html") else f"{page}.html"
    if name not in allowed:
        name = "jobs.html"
    return render_template(f"candidate/{name}")


@bp.route("/recruiter/<path:page>")
def recruiter_page(page: str):
    allowed = {"register.html", "login.html", "dashboard.html", "create-job.html", "rankings.html"}
    name = page if page.endswith(".html") else f"{page}.html"
    if name not in allowed:
        name = "dashboard.html"
    return render_template(f"recruiter/{name}")


@bp.route("/admin/<path:page>")
def admin_page(page: str):
    allowed = {"login.html", "panel.html"}
    name = page if page.endswith(".html") else f"{page}.html"
    if name not in allowed:
        name = "panel.html"
    return render_template(f"admin/{name}")
