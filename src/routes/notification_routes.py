import jwt
from flask import Blueprint, jsonify, request

from src.model import *
from src.utils.db import db

notification_routes = Blueprint("notifications", __name__)


@notification_routes.route("/notification_settings", methods=["POST", "GET"])
def notification_settings():
    try:
        SECRET_KEY = "balablu-01101"
        decoded = jwt.decode(
            request.headers.get("Authorization"), SECRET_KEY, algorithms=["HS256"]
        )
        user = decoded
    except:
        return jsonify({"message": "Invalid auth token"})
    if user.get("role") not in ["ADMIN"]:
        return jsonify({"message": "Unauthorized Access"}), 401
    if request.method == "GET":
        notification_setting = Notification_Setting.query.filter_by(
            organization_id=user.get("organization_id")
        ).first()
        if notification_setting:
            return jsonify(
                {
                    "message": "success",
                    "data": {
                        "price": notification_setting.price,
                        "account_id": notification_setting.account_id,
                        "add_notify": True,
                    },
                }
            )
        else:
            return jsonify({"message": "No notification setting"})
    data = request.get_json()
    price = data.get("price")
    add_notify = data.get("add_notify")
    account_id = data.get("account_id")

    if add_notify == False:
        notification_setting = Notification_Setting.query.filter_by(
            organization_id=user.get("organization_id")
        ).first()
        if notification_setting:
            # query = db.session.query(User).join(User_Notification)
            # query = query.filter(User.organization_id == user.get('organization_id'))
            # for q in query:
            #     db.session.delete(q)
            #     db.session.commit()
            db.session.delete(notification_setting)
            db.session.commit()
            return jsonify(
                {
                    "status": "success",
                    "message": "Notification Settings Updated Successfully",
                }
            )

    if price != None or price != 0:
        if not Notification_Setting.query.filter_by(
            organization_id=user.get("organization_id")
        ).first():
            new_notification_setting = Notification_Setting(
                price=price,
                organization_id=user.get("organization_id"),
                account_id=account_id,
            )
            db.session.add(new_notification_setting)
        else:
            notification_setting = Notification_Setting.query.filter_by(
                organization_id=user.get("organization_id")
            ).first()
            notification_setting.price = price
            notification_setting.account_id = account_id
        db.session.commit()

        return jsonify(
            {"status": "success", "message": "notifications updated successfully"}
        )


@notification_routes.route("/use_notifications", methods=["POST", "GET"])
def use_notification():
    try:
        SECRET_KEY = "balablu-01101"
        decoded = jwt.decode(
            request.headers.get("Authorization"), SECRET_KEY, algorithms=["HS256"]
        )
        user = decoded
    except:
        return jsonify({"message": "Invalid auth token"})
    if user.get("role") not in ["STUDENT"]:
        return jsonify({"message": "Unauthorized Access"}), 401
    if request.method == "GET":
        notification_settings = Notification_Setting.query.filter_by(
            organization_id=user.get("organization_id")
        ).first()
        if not notification_settings:
            return jsonify({"message": "No Notify"})
        notification_setting = User_Notification.query.filter_by(
            student_id=user.get("id")
        ).first()
        if notification_setting:
            return jsonify(
                {
                    "message": "success",
                    "data": {
                        "email": notification_setting.email,
                        "phone": notification_setting.phone,
                        "use_notify": True,
                    },
                }
            )
        else:
            return jsonify({"message": "No notification setting"})
    data = request.get_json()
    email = data.get("email")
    phone = data.get("phone")
    use_notify = data.get("use_notify")

    if use_notify == False:
        notification_setting = User_Notification.query.filter_by(
            student_id=user.get("id")
        ).first()
        if notification_setting:
            db.session.delete(notification_setting)
            db.session.commit()
            return jsonify(
                {
                    "status": "success",
                    "message": "Notification Settings Updated Successfully",
                }
            )
    if email != "" and phone != "":
        notification_setting = User_Notification.query.filter_by(
            student_id=user.get("id")
        ).first()
        if notification_setting:
            notification_setting.email = email
            notification_setting.phone = phone
        else:
            new_notification_setting = User_Notification(
                email=email, phone=phone, student_id=user.get("id")
            )
            db.session.add(new_notification_setting)
        db.session.commit()

        return jsonify(
            {"status": "success", "message": "Notifications Updated Successfully"}
        )
