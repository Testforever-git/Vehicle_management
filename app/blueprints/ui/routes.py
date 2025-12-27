# app/blueprints/ui/routes.py
from flask import render_template, redirect, url_for, abort, request
from . import bp
from ...security.mock_users import get_current_user
from ...utils.masking import mask_plate
from ...repositories.vehicle_repo import list_vehicles, get_vehicle, get_status, update_vehicle, ensure_dirs_saved

def _require_login():
    u = get_current_user()
    return u.is_authenticated

@bp.get("/")
def home():
    return redirect(url_for("ui.dashboard"))

@bp.get("/dashboard")
def dashboard():
    if not _require_login():
        return redirect(url_for("auth.login"))
    vehicles = list_vehicles()
    total = len(vehicles)
    return render_template("dashboard.html", active_menu="dashboard", total=total)

@bp.get("/vehicle/list")
def vehicle_list():
    if not _require_login():
        return redirect(url_for("auth.login"))

    rows = list_vehicles()
    vehicles = []
    for v in rows:
        vv = dict(v)
        vv["masked_plate_no"] = mask_plate(v.get("plate_no", ""))
        # status 可选：如果你没建 vehicle_status 表，这里可以先不显示
        try:
            st = get_status(v["id"])
            vv["status"] = st["status"] if st else "unknown"
        except Exception:
            vv["status"] = "unknown"
        vehicles.append(vv)

    status_options = [("available","available"), ("rented","rented"), ("maintenance","maintenance")]

    class P:
        total = len(vehicles)

    return render_template(
        "vehicle/list.html",
        active_menu="vehicle",
        vehicles=vehicles,
        pagination=P(),
        status_options=status_options,
    )

@bp.get("/vehicle/<int:vehicle_id>")
def vehicle_detail(vehicle_id: int):
    if not _require_login():
        return redirect(url_for("auth.login"))

    vehicle = get_vehicle(vehicle_id)
    if not vehicle:
        abort(404)

    # 可选：把默认目录写回 DB（你不想自动写回就删掉这一行）
    ensure_dirs_saved(vehicle_id)

    vehicle_vm = dict(vehicle)
    vehicle_vm["masked_plate_no"] = mask_plate(vehicle.get("plate_no", ""))

    status = None
    try:
        status = get_status(vehicle_id)
    except Exception:
        status = None

    return render_template(
        "vehicle/detail.html",
        active_menu="vehicle",
        vehicle=vehicle_vm,
        status=status,
        recent_logs=[],
    )

@bp.route("/vehicle/<int:vehicle_id>/edit", methods=["GET","POST"])
def vehicle_edit(vehicle_id: int):
    if not _require_login():
        return redirect(url_for("auth.login"))

    vehicle = get_vehicle(vehicle_id)
    if not vehicle:
        abort(404)

    if request.method == "POST":
        payload = {
            "brand_jp": request.form.get("brand_jp"),
            "model_jp": request.form.get("model_jp"),
            "type_designation_code": request.form.get("type_designation_code"),
            "garage_name": request.form.get("garage_name"),
            "garage_address_jp": request.form.get("garage_address_jp"),
            "purchase_price": request.form.get("purchase_price"),
        }
        update_vehicle(vehicle_id, payload)
        return redirect(url_for("ui.vehicle_detail", vehicle_id=vehicle_id, lang=request.args.get("lang")))

    return render_template("vehicle/edit.html", active_menu="vehicle", vehicle=vehicle)
