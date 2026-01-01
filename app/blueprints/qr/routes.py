# app/blueprints/qr/routes.py
from flask import render_template, abort, redirect, url_for, session, request
from . import bp
from ...utils.masking import mask_plate
from ...repositories.vehicle_repo import get_status
from ...repositories.qr_repo import get_vehicle_by_qr_slug, get_vehicle_id_by_qr_slug
from ...security.users import get_current_user

@bp.get("/v/<string:qr_slug>")
def qr_public(qr_slug: str):
    vehicle_id = get_vehicle_id_by_qr_slug(qr_slug)
    if not vehicle_id:
        abort(404)
    if not get_current_user().is_authenticated:
        session["next_url"] = url_for("ui.vehicle_edit", vehicle_id=vehicle_id, lang=request.args.get("lang"))
        return redirect(url_for("auth.login", lang=request.args.get("lang")))
    return redirect(url_for("ui.vehicle_edit", vehicle_id=vehicle_id, lang=request.args.get("lang")))


@bp.get("/v/<string:qr_slug>/detail")
def qr_detail(qr_slug: str):
    vehicle = get_vehicle_by_qr_slug(qr_slug)
    if not vehicle:
        abort(404)

    vehicle_vm = dict(vehicle)
    vehicle_vm["masked_plate_no"] = mask_plate(vehicle.get("plate_no", ""))

    status = None
    try:
        status = get_status(vehicle_vm["id"])
    except Exception:
        status = None

    return render_template(
        "qr/public.html",
        qr_slug=qr_slug,
        vehicle=vehicle_vm,
        status=status,
        scanned_at="now",
    )
