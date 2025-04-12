from flask import Flask, request, jsonify
from flask_cors import CORS
from io import BytesIO
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from openai import OpenAI
import re
import base64
import os

from rayoptics.environment import *

# Initialize Flask app and enable CORS
app = Flask(__name__)
CORS(app)

# Initialize OpenAI client using environment variable
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

isdark = True  # For plot appearance

# Test endpoint to verify logging
@app.route("/test", methods=["POST"])
def test():
    data = request.get_json()
    app.logger.info("✅ /test called")
    app.logger.info("📦 Payload: %s", data)
    return jsonify({"status": "received", "data": data}), 200

# Simulation function: builds and renders the optical model
def gen_sim(curve1, curve2, width, diameter, dist_object_lens, dist_lens_image):
    opm = OpticalModel()
    sm = opm['seq_model']
    osp = opm['optical_spec']

    osp['pupil'] = PupilSpec(osp, key=['object', 'epd'], value=diameter)
    osp['fov'] = FieldSpec(osp, key=['object', 'angle'], value=1, flds=[0.], is_relative=True)
    opm.radius_mode = True

    sm.gaps[0].thi = dist_object_lens
    sm.add_surface([curve1, width, 'N-LAK9', 'Schott'])
    sm.add_surface([-curve2, dist_lens_image])
    sm.set_stop()

    opm.update_model()
    fig = plt.figure(FigureClass=InteractiveLayout, opt_model=opm, is_dark=isdark).plot()
    buf = BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)
    return buf

# Use GPT-4 to extract float parameters from natural language
def extract_params(prompt):
    try:
        app.logger.info("🔁 Calling extract_params with prompt: %s", prompt)

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "Extract these 6 float values from the text: curve1, curve2, width, diameter, dist_object_lens, dist_lens_image. Return only a Python dictionary."
                },
                {"role": "user", "content": prompt}
            ]
        )
        reply = response.choices[0].message.content
        app.logger.info("🧠 GPT-4 raw reply: %s", reply)

        match = re.search(r'\{.*\}', reply, re.DOTALL)
        if match:
            return eval(match.group(0))  # Simple dictionary parsing
    except Exception as e:
        app.logger.error("❌ Error in extract_params: %s", str(e))

    return None

# API endpoint to trigger simulation
@app.route("/api/simulate", methods=["POST"])
def simulate():
    try:
        data = request.get_json()
        prompt = data.get("prompt", "")
        app.logger.info("📨 Received prompt: %s", prompt)

        params = extract_params(prompt)
        app.logger.info("📐 Extracted parameters: %s", params)

        if not params:
            return jsonify({"error": "Failed to extract lens parameters."}), 400

        img_buf = gen_sim(
            params["curve1"],
            params["curve2"],
            params["width"],
            params["diameter"],
            params["dist_object_lens"],
            params["dist_lens_image"]
        )

        img_base64 = base64.b64encode(img_buf.read()).decode("utf-8")

        return jsonify({
            "image": img_base64,
            "parameters": params
        })

    except Exception as e:
        app.logger.error("💥 Unhandled error in /api/simulate: %s", str(e))
        return jsonify({"error": str(e)}), 500

# Root route just for health check
@app.route("/", methods=["GET"])
def index():
    return "Lens Whisperer is live!", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
