isdark = True

from rayoptics.environment import *
def gen_sim(curve1,curve2,width,diameter,dist_object_lens,dist_lens_image):
    opm = OpticalModel()
    sm  = opm['seq_model']
    osp = opm['optical_spec']
    pm = opm['parax_model']
    em = opm['ele_model']
    pt = opm['part_tree']
    ar = opm['analysis_results']
    osp['pupil'] = PupilSpec(osp, key=['object', 'epd'], value=diameter)
    osp['fov'] = FieldSpec(osp, key=['object', 'angle'], value=1, flds=[ 0.], is_relative=True)
    opm.radius_mode = True
    sm.gaps[0].thi=dist_object_lens
    sm.add_surface([curve1, width, 'N-LAK9', 'Schott'])
    sm.add_surface([-curve2, dist_lens_image])
    sm.set_stop()
    '''sm.add_surface([-24.456, .975, 'N-SF5,Schott'])
    #sm.set_stop()
    sm.add_surface([21.896, 4.822])
    sm.add_surface([86.759, 3.127, 'N-LAK9', 'Schott'])
    sm.add_surface([-20.4942, 41.2365])'''
    opm.update_model()
    #sm.list_model()
    layout_plt = plt.figure(FigureClass=InteractiveLayout, opt_model=opm, is_dark=isdark).plot()
    plt.show()


curve1=20
curve2=20
width=6
diameter=15
dist_object_lens=80
dist_lens_image=40
gen_sim(curve1,curve2,width,diameter,dist_object_lens,dist_lens_image)