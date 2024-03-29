import argparse
from io import BytesIO
from urllib.parse import quote, unquote_plus
from urllib.request import urlopen
from functools import wraps
import os
import sys
import logging
import traceback

from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from waitress import serve
from rembg.bg import remove
import firebase_admin
from firebase_admin import auth
from firebase_admin import firestore
from firebase_admin.auth import InvalidIdTokenError
import redis

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

RATE_LIMIT = os.getenv('RATE_LIMIT', 5)
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = os.getenv('REDIS_PORT', 6379)
REDIS_SSL = os.getenv("REDIS_SSL", 'False').lower() in ('true', '1', 't', 'yes')
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
r = redis.Redis(host=REDIS_HOST, port=int(REDIS_PORT), db=0, ssl=REDIS_SSL,
        password=REDIS_PASSWORD, socket_connect_timeout=2)
redis_connected = False

app = Flask(__name__)
CORS(app)
db = None

try:
    logging.info("trying to connect to redis %s:%s", REDIS_HOST, REDIS_PORT)
    r.ping()
    redis_connected = True
    logging.info("connection to redis successfull %s:%s", REDIS_HOST, REDIS_PORT)
except Exception as e:
    logging.error("error connecting to redis")
    logging.error(traceback.format_exc())

try:
    logging.info("Initializing firebase default app")
    default_app = firebase_admin.initialize_app()
    db = firestore.client()
except Exception as e:
    logging.error("error connecting to redis")
    logging.error(traceback.format_exc())

def decrease_credit(uid):
    user_ref = db.collection(u'Users').document(uid)
    user_ref.update({"credits": firestore.Increment(-1)})

def get_credits(uid):
    user_ref = db.collection(u'Users').document(uid)
    user = user_ref.get()
    if user.exists:
        return user.get("credits")
    return None

def rate_limit(f):
    @wraps(f)
    def inner(*args, **kwargs):
        if not redis_connected:
            return f(*args, **kwargs)

        rapidapi_secret = request.headers.get("X-RapidAPI-Proxy-Secret")
        if rapidapi_secret and rapidapi_secret == os.Getenv("RAPIDAPI_SECRET"):
            return f(*args, **kwargs)

        auth_header = request.headers.get("Authorization")
        user = None
        if auth_header:
            token = auth_header.split(" ")[1]
            try:
                decoded_token = auth.verify_id_token(token)
                uid = decoded_token['uid']
                user = auth.get_user(uid)
                kwargs["user"] = user
                credits_remaining = get_credits(uid)
                if credits_remaining and credits_remaining <= 0:
                    return jsonify({"error": ("You are out of credits. "
                    "Please purchase more credits or upgrade your subscription.")}), 429
            except (ValueError, InvalidIdTokenError) as e:
                logging.error("Invalid Token:", e)
                logging.error(traceback.format_exc())
                return jsonify({"error": "invalid JWT token"}), 403
            except Exception as e:
                logging.error(traceback.format_exc())
                return jsonify({"error": "Error Validating JWT token: %s" % (e)}), 403
        else:
            forwarded_header = request.headers.get("X-Forwarded-For")
            source_ip = ""
            if forwarded_header:
                source_ip = request.headers.getlist("X-Forwarded-For")[0]
            else:
                source_ip = request.remote_addr
            key = "ip:"+source_ip+":images"
            current_images = r.get(key)
            if current_images and int(current_images) >= RATE_LIMIT:
                app.logger.info("Rate limit exceeded for %s", source_ip)
                return jsonify({"error": ("You've exceeded the rate limit "
                    "of {0} images per month. Register for a free account "
                    "to increase your limit").format(RATE_LIMIT)}), 429
            if current_images == None or int(current_images) == 0:
                r.set(key, 1, ex=2629800) # 1 month expiry
            elif int(current_images) >= 1:
                r.incr(key)

        result = f(*args, **kwargs)
        if user:
            decrease_credit(user.uid)
        return result
    return inner

@app.route("/remove", methods=["POST"])
@rate_limit
def remove_background(user=None):
    file_content = ""
    if "file" not in request.files:
        return {"error": "missing post form param 'file'"}, 400

    file_content = request.files["file"].read()
    app.logger.info('got file %s', request.files["file"].filename)

    if file_content == "":
        return {"error": "File content is empty"}, 400

    alpha_matting = "a" in request.values
    af = request.values.get("af", type=int, default=240)
    ab = request.values.get("ab", type=int, default=10)
    ae = request.values.get("ae", type=int, default=10)
    az = request.values.get("az", type=int, default=1000)

    model = "u2net"
    try:
        return send_file(
            BytesIO(
                remove(
                    file_content,
                    alpha_matting=alpha_matting,
                    alpha_matting_foreground_threshold=af,
                    alpha_matting_background_threshold=ab,
                    alpha_matting_erode_size=ae,
                )
            ),
            mimetype="image/png",
            download_name="test_bgdestroyer.png",
        )
    except Exception as e:
        app.logger.exception(e, exc_info=True)
        return {"error": "oops, something went wrong!"}, 500


def main():
    ap = argparse.ArgumentParser()

    ap.add_argument(
        "-a",
        "--addr",
        default="0.0.0.0",
        type=str,
        help="The IP address to bind to.",
    )

    ap.add_argument(
        "-p",
        "--port",
        default=8080,
        type=int,
        help="The port to bind to.",
    )

    args = ap.parse_args()
    serve(app, host=args.addr, port=args.port)


if __name__ == "__main__":
    main()
