from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt

def admin_required(fn):
    """Allow only JWTs that have {"is_admin": True}"""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        claims = get_jwt()
        if not claims.get("is_admin"):
            return jsonify({"msg": "Admins only!"}), 403
        return fn(*args, **kwargs)
    return wrapper
