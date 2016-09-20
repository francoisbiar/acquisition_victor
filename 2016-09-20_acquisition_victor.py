import time
import crappy2
import numpy as np

crappy2.blocks.MasterBlock.instances = []  # Init masterblock instances

timestamp = time.localtime()
string_stamp = "%i_%i_%i_%ih%i" % (timestamp.tm_year, timestamp.tm_mon,
                                   timestamp.tm_mday, timestamp.tm_hour,
                                   timestamp.tm_min)

path_measures_instron = '/home/francois/Essais/2016-09-20_Victor/'


class EvalStress(crappy2.links.MetaCondition):
    """
    This class returns strain stress related to torque applied by the instron.
    """

    def __init__(self):
        self.section = np.pi * 5 ** 2  # Specimen section in mm^2 (in order to have MPa below)

    def evaluate(self, value):
        value['tau(MPa)'] = value['Force(N)'] / self.section
        return value

class EvalCycles(crappy2.links.MetaCondition):
    def __init__(self):
        self.amplitude = 10  # Amplitude de detection



def eval_offset(device, duration):
    timeout = time.time() + duration  # duration secs from now
    print 'Measuring offset (%d sec), please be patient...' % duration
    offset1 = []
    offset2 = []
    offset3 = []
    while True:
        [chan1, chan2, chan3] = device.get_data('all')[1]
        offset1.append(chan1)
        offset2.append(chan2)
        offset3.append(chan3)
        if time.time() > timeout:
            break
    return [-np.mean(offset1), -np.mean(offset2), -np.mean(offset3)]


try:
    # Creating objects
    comedi_device = crappy2.sensor.ComediSensor(channels=[0, 1, 2], gain=[1, 1, 1], offset=[0, 0, 0])
    offsets = eval_offset(comedi_device, 5)
    comedi_device.close()
    comedi_device = crappy2.sensor.ComediSensor(channels=[0, 1, 2], gain=[1, 1, 1], offset=offsets)

    # Creating blocks
    measurebystep = crappy2.blocks.MeasureByStep(sensor=comedi_device,
                                                 labels=['t(s)', 'Deformation(%)', 'Force(N)', 'Position(mm)'])

    grapher_force = crappy2.blocks.Grapher(('t(s)', 'tau(MPa)'), window_pos=(1920, 0), length=10)
    grapher_deplacement = crappy2.blocks.Grapher(('t(s)', 'Position(mm)'), window_pos=(640, 0), length=10)
    grapher_deformation = crappy2.blocks.Grapher(('t(s)', 'Deformation(%)'), window_pos=(0, 0), length=10)

    saver = crappy2.blocks.Saver(path_measures_instron + string_stamp + '.csv')

    compacter = crappy2.blocks.Compacter(100)

    ## FORCE ET DEPLACEMENT
    link_to_compacter = crappy2.links.Link(name='to_compacter', condition=EvalStress())
    link_to_force = crappy2.links.Link(name='to_force')
    link_to_deplacement = crappy2.links.Link(name='to_dep')
    link_to_deformation = crappy2.links.Link(name='to_deformation')
    link_to_save = crappy2.links.Link(name='to_save')

    measurebystep.add_output(link_to_compacter)  # > Mesures
    compacter.add_input(link_to_compacter)

    compacter.add_output(link_to_force)  # > Vers les graphs
    compacter.add_output(link_to_save)  # > Vers le saver
    compacter.add_output(link_to_deplacement)
    compacter.add_output(link_to_deformation)

    grapher_force.add_input(link_to_force)
    grapher_deplacement.add_input(link_to_deplacement)
    grapher_deformation.add_input(link_to_deformation)
    saver.add_input(link_to_save)

    t0 = time.time()

    for instance in crappy2.blocks.MasterBlock.instances:
        instance.t0 = t0

    for instance in crappy2.blocks.MasterBlock.instances:
        instance.start()  # Waiting for execution

# Stopping objects
except KeyboardInterrupt:
    for instance in crappy2.blocks.MasterBlock.instances:
        instance.stop()
except Exception:
    raise
