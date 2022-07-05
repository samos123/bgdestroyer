import argparse
from io import BytesIO
from urllib.parse import quote, unquote_plus
from urllib.request import urlopen

from flask import Flask, request, send_file
from waitress import serve


app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return """
<html>
<body>
<form action="/api/remove-background" method="post" enctype="multipart/form-data">
   <input type="file" name="file"/>
   <input type="submit" value="upload"/>
</form>
</body>
</html>
"""


@app.route("/api/remove-background", methods=["POST"])
def remove_background():
    from rembg.bg import remove
    file_content = ""
    if "file" not in request.files:
        return {"error": "missing post form param 'file'"}, 400

    file_content = request.files["file"].read()

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
            attachment_filename="test.png",
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
