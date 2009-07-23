#!/usr/bin/python
#pymates
#ipython -wthread -c "import pymates" -i
#pymates.start()
#pymates.demo()
#pymates.mate_parts()
#optionally, pymates.move(pymates.total_parts[0],x,y,z,i,i,i,j,j,j)

#see ~/local/pythonOCC/samples/Level2/DataExchange/import_step_multi.py
#see ~/local/pythonOCC/samples/Level1/TopologyTransformation/mirror.py

import yaml
import re
import os
#os.environ['CSF_GraphicShr'] = r"/usr/lib/libTKOpenGl.so"
import time
import random
import copy
import numpy
import wx
import OCC.gp
import OCC.BRepPrimAPI
import OCC.BRepBuilderAPI
import OCC.Display.wxSamplesGui
import OCC.Utils.DataExchange.STEP
import geom
import assembly

total_parts = []

# the following aren't our responsibility, actually (pythonOCC?)
#class Circle(yaml.YAMLObject)
#class Cylinder(yaml.YAMLObject)
#class InterfaceGeom(yaml.YAMLObject):

class Part(yaml.YAMLObject):
    '''used for part mating. argh I hope OCC doesn't already implement this and I just don't know it.
    should a part without an interface be invalid?'''
    yaml_tag = '!part'
    def __init__(self, name="part name", description="description", created=time.localtime(), files=[], interfaces={}):
        self.description, self.created, self.files, self.interfaces = description, created, files, interfaces
    def load_CAD(self):
        if len(self.files) == 0: return #no files to load
        #FIXME: assuming STEP
        for file in self.files:
            my_step_importer = OCC.Utils.DataExchange.STEP.STEPImporter(str(file))
            my_step_importer.ReadFile()
            self.shapes = my_step_importer.GetShapes()
            self.compound = my_step_importer.GetCompound()
            result = OCC.Display.wxSamplesGui.display.DisplayShape(self.shapes)
            if type(result) == type([]): self.ais_shapes = result[0]
            else: self.ais_shapes = result
        #i, j, k, point = self.interfaces[0].i, self.interfaces[0].j, self.interfaces[0].k, self.interfaces[0].point
        x,z,point = self.interfaces[0].x,self.interfaces[0].z,self.interfaces[0].point
        return
    def __repr__(self):
        return "%s(name=%s, description=%s, created=%s, files=%s, interfaces=%s)" % (self.__class__.__name__, self.name, self.description, self.created, self.files, self.interfaces)
    def yaml_repr(self):
       return "name: %s\ndescription: %s\ncreated: %s\nfiles: %s\ninterfaces: %s" % (self.name, self.description, self.created, self.files, self.interfaces)
    #def __setstate__(self, attrs):
        ##print "Part.__setstate__ says attrs = ", attrs
        #for (k,v) in attrs.items():
            ##self.__setattr__(each[0],each[1])
            #if type(v) == Interface:
                #v.name = k
                #if hasattr(self, "interfaces"): self.interfaces[k] = v
                #else:
                    #self.interfaces = {}
                    #self.interfaces[k] = v
            #self.__setattr__(k,v)
    #@classmethod
    #def to_yaml(cls, dumper, data):
    #    return dumper.represent_mapping(cls.yaml_tag, cls.yaml_repr(data))
    #@classmethod
    #def from_yaml(cls, loader, node):
    #    print "from_yaml() says that loader = ", loader
    #    data = loader.construct_mapping(node)
    #    print "from_yaml() says that data = ", data
    #    return cls(data)

class Interface(yaml.YAMLObject):
    '''"units" should be what is being transmitted through the interface, not about the structure.
    a screw's head transmits a force (N), but not a pressure (N/m**2) because the m**2 is actually interface geometry'''
    yaml_tag = '!interface'
    def __init__(self, name="generic interface name", units=None, geometry=None, point=[0,0,0], x=0, y=0, z=0):
        self.name, self.units, self.geometry, self.point, self.x, self.y, self.z = name, units, geometry, point, x, y, z
    def __repr__(self):
        return "Interface(name=%s,units=%s,geometry=%s,point=%s,x=%s,y=%s,z=%s)" % (self.name, self.units, self.geometry, self.point, self.x, self.y, self.z)
    def yaml_repr(self):
        return "name: %s\nunits: %s\ngeometry: %s\npoint: %s\nx: %s\ny: %s\nz: %s" % (self.name, self.units, self.geometry, self.point, self.x, self.y, self.z)
    #@classmethod
    #def to_yaml(cls, dumper, data):
    #    return dumper.represent_scalar(cls.yaml_tag, cls.yaml_repr(data))
    #@classmethod
    #def from_yaml(cls, loader, node):
    #    return Interface("node name from from_yaml")

#for cls in [Part, Interface]:
#    yaml.add_implicit_resolver(cls.yaml_tag, cls.yaml_pattern)

def compatibility(part1, part2):
    '''find all possible combinations of part1 and part2 (for each interface/port) and check each compatibility'''
    return []
def compatibility(part1port, part2port):
    '''note that an interface/port object refers to what it is on. so you don't have to pass the parts.'''
    return []

def load(foo):
    return yaml.load(foo)

def dump(foo):
    return yaml.dump(foo, default_flow_style=False)

def demo(event=None):
    print "loading the file .. it looks like this:"
    blockhole = load(open("models/blockhole.yaml"))["blockhole"]
    peg = load(open("models/peg.yaml"))["peg"]
    print "blockhole is = ", dump(blockhole)
    print "peg is = ", dump(peg)
    #load the CAD?
    #load_cad_file(filename=blockhole.files[0])
    blockhole.load_CAD()
    peg.load_CAD()
    total_parts.append(blockhole)
    total_parts.append(peg)

def demo2(event=None, part=Part()):
    '''reposition the part to be at one of the interfaces of the part. this replaces move_parts().'''
    if not part.interfaces or len(part.interfaces) == 0:
        if len(total_parts) == 0: return #can't do anything about that, can we
        part = total_parts[0]
        if len(part.interfaces) == 0: return #ok I give up
    #select the first interface
    interface = part.interfaces[part.interfaces.keys()[0]][0]
    point = interface[part.interfaces.keys()[0]][0].point
    i = interface.i
    j = interface.j
    k = interface.k
    o_point = OCC.gp.gp_Pnt(point[0], point[1], point[2])
    o_n_vec = OCC.gp.gp_Dir(i[0], i[1], i[2])
    o_vx_vec = OCC.gp.gp_Dir(j[0], j[1], j[2])
    ax3 = OCC.gp.gp_Ax3(o_point, o_n_vec, o_vx_vec)
    the_transform = OCC.gp.gp_Trsf()
    #myax = OCC.gp.gp_Ax3( blah )
    #myax.Transform(the_transform)
    the_transform.SetTransformation(ax3)
    the_toploc = OCC.TopLoc.TopLoc_Location(the_transform)
    #import OCC.AIS
    #OCC.AIS.Handle_AIS_InteractiveObject()
    OCC.Display.wxSamplesGui.display.Context.SetLocation(part.ais_shapes, the_toploc)
    OCC.Display.wxSamplesGui.display.Context.UpdateCurrentViewer()
    return

def load_cad_file(event=None, filename=""):
    '''deprecated'''
    pass
    if not filename or filename == "":
        #popup menu selector for finding a filename
        filename = wx.FileSelector()
        #FIXME: this assumes that the path is relative to the curdir- i.e. in skdb/pymates/models/ or at least skdb/pymates/
        #figure out relative path for STEPImporter
        fullpath = os.path.realpath(os.path.curdir)
        filename = filename.replace(fullpath + "/","")
    #load the STEP file
    my_step_importer = OCC.Utils.DataExchange.STEP.STEPImporter(str(filename))
    my_step_importer.ReadFile()
    the_shapes = my_step_importer.GetShapes()
    the_compound = my_step_importer.GetCompound()
    #don't forget to get the return value and append it to total_shapes
    #FIXME: don't be so lame re: use of globals.
    ais_shapes = OCC.Display.wxSamplesGui.display.DisplayShape(the_shapes)
    total_parts.append(ais_shapes[0]) #sorry

def mate_parts(event=None):
    #mate all of the parts in the workspace
    #see transform_point()
    if len(total_parts) < 1: return #meh
    part1 = total_parts[0]
    part2 = total_parts[1]
    interface1 = part1.interfaces[0]
    interface2 = part2.interfaces[0]
    point1 = interface1.point
    point2 = interface2.point
    occ_point1 = OCC.gp.gp_Pnt(point1[0], point1[1], point1[2])
    occ_point2 = OCC.gp.gp_Pnt(point2[0], point2[1], point2[2])
    
    pivot_point = OCC.gp.gp_Pnt(0,0,0) #rotate about the origin, right?
    x_rotation = OCC.gp.gp_Dir(1,0,0) #OCC.gp.gp_Dir(interface2.x[0], interface2.x[1], interface2.x[2])
    y_rotation = OCC.gp.gp_Dir(0,1,0) #OCC.gp.gp_Dir(interface2.j[0], interface2.j[1], interface2.j[2])
    z_rotation = OCC.gp.gp_Dir(0,0,1) #OCC.gp.gp_Dir(interface2.k[0], interface2.k[1], interface2.k[2])
    transformation = OCC.gp.gp_Trsf()
    transformation.SetRotation(OCC.gp.gp_Ax1(pivot_point, x_rotation),interface2.x)
    #transformation.SetRotation(OCC.gp.gp_Ax1(pivot_point, y_rotation),180)
    transformation.SetRotation(OCC.gp.gp_Ax1(pivot_point, z_rotation),interface2.z)
    transformation.SetTranslation(occ_point2, occ_point1)

    brep_transform = OCC.BRepBuilderAPI.BRepBuilderAPI_Transform(transformation)
    brep_transform.Perform(part2.shapes[0])
    resulting_shape = brep_transform.Shape()

    OCC.Display.wxSamplesGui.display.DisplayShape(resulting_shape)
    return brep_transform

def move(my_part, x, y, z, i1, i2, i3, j1, j2, j3):
    o_point = OCC.gp.gp_Pnt(x,y,z)
    o_n_vec = OCC.gp.gp_Dir(i1,i2,i3)
    o_vx_vec = OCC.gp.gp_Dir(j1,j2,j3)
    ax3 = OCC.gp.gp_Ax3(o_point, o_n_vec, o_vx_vec)
    transform = OCC.gp.gp_Trsf()
    transform.SetTransformation(ax3)
    toploc = OCC.TopLoc.TopLoc_Location(transform)
    OCC.Display.wxSamplesGui.display.Context.SetLocation(my_part.ais_shapes, toploc)
    OCC.Display.wxSamplesGui.display.Context.UpdateCurrentViewer()
    return

def move_parts(event=None):
    if len(total_parts) == 0: return
    if len(total_parts) == 1: working_part = total_parts[0]
    else: working_part = total_parts[random.randrange(0,len(total_parts))]

    #gp_Dir, gce_MakeDir, Geom_Direction: http://adl.serveftp.org/lab/opencascade/doc/ReferenceDocumentation/FoundationClasses/html/classgp__Dir.html
    #gp_Ax3: http://adl.serveftp.org/lab/opencascade/doc/ReferenceDocumentation/FoundationClasses/html/classgp__Ax3.html
    #gp_Ax3 (const gp_Pnt &P, const gp_Dir &N, const gp_Dir &Vx)
    #gp_Ax3 (const gp_Pnt &P, const gp_Dir &V)
    #see pythonOCC/samples/Level1/Animation/animation.py

    point = OCC.gp.gp_Pnt(0,0,0)
    n_vec = OCC.gp.gp_Dir(0,0,1)
    tempvar = [1,1,1] #[-1,0,0] #[0,-1,0]
    #TODO: check whether or not tempvar is valid
    vx_vec = OCC.gp.gp_Dir(tempvar[0],tempvar[1],tempvar[1])
    ax3 = OCC.gp.gp_Ax3(point, n_vec, vx_vec)
    the_transform = OCC.gp.gp_Trsf()
    the_transform.SetTransformation(ax3)
    the_toploc = OCC.TopLoc.TopLoc_Location(the_transform)
    OCC.Display.wxSamplesGui.display.Context.SetLocation(working_shape, the_toploc)
    OCC.Display.wxSamplesGui.display.Context.UpdateCurrentViewer()
    return

def show_interface_points():
    for each in total_parts:
        interface = each.interfaces[0]
        mysphere = OCC.BRepPrimAPI.BRepPrimAPI_MakeSphere(OCC.gp.gp_Pnt(interface.point[0], interface.point[1], interface.point[2]), 2.0)
        OCC.Display.wxSamplesGui.display.DisplayColoredShape(mysphere.Shape(), color='RED')
    OCC.Display.wxSamplesGui.display.Context.UpdateCurrentViewer()
    return

def show_new_interface_point(x,y,z,color='RED'):
    mysphere = OCC.BRepPrimAPI.BRepPrimAPI_MakeSphere(OCC.gp.gp_Pnt(x,y,z), 2.0)
    OCC.Display.wxSamplesGui.display.DisplayColoredShape(mysphere.Shape(), color=color)
    OCC.Display.wxSamplesGui.display.Context.UpdateCurrentViewer()
    return

def show_cone_at(x,y,z,color='YELLOW'):
    mycone = OCC.BRepPrimAPI.BRepPrimAPI_MakeCone(x,y,z)
    OCC.Display.wxSamplesGui.display.DisplayColoredShape(mycone.Shape(), color=color)
    #OCC.Display.wxSamplesGui.display.Context.UpdateCurrentViewer()
    return

def add_part_mate(part_1_interface, part_2_interface):
    #mate interface 1 to interface 2 (move part 1)
    #return the ID of the shape transformation added to the part object
    return

def show_part_mate(part_mate_object):
    #look at the part_mate_object and DisplayShape() the shape with the right coordinate system
    return

def start():
    OCC.Display.wxSamplesGui.display.Create()

def restart(): #EraseAll
    '''EraseAll'''
    OCC.Display.wxSamplesGui.display.EraseAll()
    return

def nontransform_point(x,y,z,color='YELLOW'):
    return show_new_interface_point(x,y,z,color=color)

def transform_point(x,y,z,color='YELLOW'):
    #draw a (small) sphere (maybe eventually a cone to show direction if I figure out the correct parameters to OCC.BRepPrimAPI.BRepPrimAPI_MakeCone())
    #then transform it in the same way that mate_parts() transforms everything
    mysphere = OCC.BRepPrimAPI.BRepPrimAPI_MakeSphere(OCC.gp.gp_Pnt(x,y,z), 1.0)
    transformation = OCC.gp.gp_Trsf()
    interface1 = total_parts[0].interfaces[0]
    interface2 = total_parts[1].interfaces[0]
    point1 = interface1.point
    point2 = interface2.point
    i1, j1, k1 = interface1.i, interface1.j, interface1.k
    i2, j2, k2 = interface2.i, interface2.j, interface2.k
    #fromCoordinateSystem1 = OCC.gp.gp_Ax3(OCC.gp.gp_Pnt(point1[0],point1[1],point1[2]), OCC.gp.gp_Dir(i1[0],i1[1],i1[2]), OCC.gp.gp_Dir(k1[0],k1[1],k1[2]))
    #toCoordinateSystem2 = OCC.gp.gp_Ax3(OCC.gp.gp_Pnt(point2[0],point2[1],point2[2]), OCC.gp.gp_Dir(i2[0],i2[1],i2[2]), OCC.gp.gp_Dir(k2[0],k2[1],k2[2]))
    #transformation.SetTransformation(fromCoordinateSystem1, toCoordinateSystem2)
    #now try: pymates.transform_point(0,0,0)
    occ_point1 = OCC.gp.gp_Pnt(point1[0],point1[1],point1[2])
    occ_point2 = OCC.gp.gp_Pnt(point2[0],point2[1],point2[2])
    transformation.SetTranslation(occ_point2, occ_point1)
    brep_transform = OCC.BRepBuilderAPI.BRepBuilderAPI_Transform(transformation)
    brep_transform.Perform(mysphere.Shape())  #(total_parts[1].shapes[0])
    resulting_shape = brep_transform.Shape()
    OCC.Display.wxSamplesGui.display.DisplayShape(resulting_shape)
    return brep_transform

def supermate_parts():
    restart()
    demo()
    mate_parts()
    return

def exit(event=None):
    import sys; sys.exit()

if __name__ == '__main__':
    OCC.Display.wxSamplesGui.add_menu("do stuff")
    OCC.Display.wxSamplesGui.add_function_to_menu('do stuff', demo)
    OCC.Display.wxSamplesGui.add_function_to_menu('do stuff', demo2)
    OCC.Display.wxSamplesGui.add_function_to_menu('do stuff', load_cad_file)
    OCC.Display.wxSamplesGui.add_function_to_menu('do stuff', mate_parts)
    OCC.Display.wxSamplesGui.add_function_to_menu('do stuff', move_parts)
    OCC.Display.wxSamplesGui.add_function_to_menu('do stuff', exit)
    OCC.Display.wxSamplesGui.start_display()
