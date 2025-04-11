from rayoptics.optical.opticalmodel import OpticalModel
from rayoptics.gui.appmanager import AppManager

# Initialize optical model
opt_model = OpticalModel()
opt_model.system_spec.title = "Glass-safe Lens System"

# Define dummy glass 'vacuum' with n=1.0
opt_model._model_catalog['glass']['vacuum'] = {
    'disp_fn': 0,
    'coefficients': [1.0]
}

seq_model = opt_model.seq_model

# Use 'vacuum' as medium
seq_model.add_surface([100.0, 0.0, 'vacuum'])      # object to lens
seq_model.add_surface([5.0, 50.0, 'vacuum'])       # front of lens
seq_model.add_surface([100.0, -50.0, 'vacuum'])    # back of lens to image

# Set aperture and field
opt_model.sys_aperture = 10.0
opt_model.system_spec.field_of_view = [(0.0, 5.0)]

# Update model and trace
opt_model.update_model()
opt_model.raytrace()

# Show GUI
app = AppManager()
app.model = opt_model
app.refresh_gui()
