from flask import Flask, request, jsonify
from io import BytesIO
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import openai
import re
import base64
from flask_cors import CORS
import os
from rayoptics.environment import *

app = Flask(__name__)
CORS(app)
openai.api_key = os.getenv("OPENAI_API_KEY")

isdark = True

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

def extract_params(prompt):
    completion = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Extract these 6 float values from the text: curve1, curve2, width, diameter, dist_object_lens, dist_lens_image. Return only a Python dictionary."},
            {"role": "user", "content": prompt}
        ]
    )
    reply = completion.choices[0].message["content"]
    match = re.search(r'\{.*\}', reply, re.DOTALL)
    if match:
        try:
            return eval(match.group(0))
        except:
            return None
    return None

@app.route("/api/simulate", methods=["POST"])
def simulate():
    data = request.get_json()
    prompt = data.get("prompt", "")
    print(prompt)
    params = extract_params(prompt)
    if not params:
        return jsonify({"error": "Failed to extract lens parameters."}), 400

    try:
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
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
