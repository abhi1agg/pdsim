# -*- coding: utf-8 -*-
import pdsim_panels
import wx
import numpy as np
from math import pi
from PDSim.scroll.core import Scroll
import matplotlib as mpl
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as WXCanvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2Wx as WXToolbar
from PDSim.scroll.plots import plotScrollSet, ScrollAnimForm
from PDSim.flow.flow import FlowPath
from PDSim.core.core import Tube
from CoolProp import State as CPState

LabeledItem = pdsim_panels.LabeledItem

class PlotPanel(wx.Panel):
    def __init__(self, parent, **kwargs):
        wx.Panel.__init__(self, parent, size = (300,200), **kwargs)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.figure = mpl.figure.Figure(dpi=100, figsize=(2, 2))
#        self.figure.set_figwidth(2.0)
#        self.figure.set_figheight(2.0)
        self.canvas = WXCanvas(self, -1, self.figure)
#        self.canvas.resize(200,200)
        #self.toolbar = WXToolbar(self.canvas)
        #self.toolbar.Realize()
        sizer.Add(self.canvas)
        #sizer.Add(self.toolbar)
        self.SetSizer(sizer)
        sizer.Layout()
        
class GeometryPanel(pdsim_panels.PDPanel):
    """
    The geometry panel of the reciprocating compressor
    Loads all parameters from the configuration file
    """
    def __init__(self,parent,configfile,**kwargs):
        pdsim_panels.PDPanel.__init__(self,parent,**kwargs)
        
        #Loads all the parameters from the config file
        configdict, descdict = self.get_from_configfile('GeometryPanel')
        
        # Things in self.items are linked through to the module code where 
        # it attempts to set the attribute.  They are also automatically
        # written to configuration file
        self.items = [
        dict(attr='Vdisp'),
        dict(attr='Vratio'),
        dict(attr='t'),
        dict(attr='ro'),
        dict(attr='delta_flank'),
        dict(attr='delta_radial')
        ]
        
        sizerInputs = wx.FlexGridSizer(cols=2, vgap=4, hgap=4)
        
        self.ConstructItems(self.items, sizerInputs, configdict, descdict)
        
        for item in self.items:
            setattr(self,item['attr'],item['textbox'])
        
        kwargs = dict(label = u"\u03D5_i0 [radian]",
                      tooltip = 'Initial involute angle for inner involute'
                      )
        self.phi_i0_label, self.phi_i0 = LabeledItem(self, **kwargs)
        
        self.phi_is_label, self.phi_is= LabeledItem(self,
                                                       label=u"\u03D5_is [radian]")

        width = max([item['label'].GetEffectiveMinSize()[0] for item in self.items])
        self.phi_is_label.SetMinSize((width,-1))
        self.phi_ie_label, self.phi_ie= LabeledItem(self,
                                                       label=u"\u03D5_ie [radian]")
        self.phi_o0_label, self.phi_o0= LabeledItem(self,
                                                       label=u"\u03D5_o0 [radian]")
        self.phi_os_label, self.phi_os= LabeledItem(self,
                                                       label=u"\u03D5_os [radian]")
        self.phi_oe_label, self.phi_oe= LabeledItem(self,
                                                       label=u"\u03D5_oe [radian]")
        self.rb_label, self.rb = LabeledItem(self,
                                             label="rb [m]")
        self.hs_label, self.hs= LabeledItem(self,
                                            label="hs [m]")
        
        self.phi_i0.Enable(False)
        self.phi_is.Enable(False)
        self.phi_ie.Enable(False)
        self.phi_o0.Enable(False)
        self.phi_os.Enable(False)
        self.phi_oe.Enable(False)
        self.rb.Enable(False)
        self.hs.Enable(False)
        
        self.PP = PlotPanel(self)
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.Add(self.PP,0,wx.EXPAND)
        anibutton = wx.Button(self, label = 'Animate')
        anibutton.Bind(wx.EVT_BUTTON,self.OnAnimate)
        hsizer.Add(anibutton,1,wx.EXPAND)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(sizerInputs)
        sizer.AddSpacer(10)
        sizer.Add(hsizer)
        sizer.AddSpacer(10)
        
        self.ax = self.PP.figure.add_axes((0,0,1,1))

        fgsGeoAnglesInputs = wx.FlexGridSizer(cols = 2)
        fgsGeoAnglesInputs.AddMany([
                     self.phi_i0_label,self.phi_i0, 
                     self.phi_is_label,self.phi_is,
                     self.phi_ie_label,self.phi_ie,
                     self.phi_o0_label,self.phi_o0, 
                     self.phi_os_label,self.phi_os,
                     self.phi_oe_label,self.phi_oe,
                     self.rb_label,self.rb,
                     self.hs_label,self.hs
                     ])
        sizer.Add(fgsGeoAnglesInputs)
        
        self.SetSizer(sizer)
        sizer.Layout()
        
        for item in self.items:
            item['textbox'].Bind(wx.EVT_KILL_FOCUS,self.OnChangeParam)
        
        # Keep a local copy of the scroll in order to be able to use the 
        # set_scroll_geo and set_disc_geo functions
        self.Scroll=Scroll()
        
        self.OnChangeParam()
        
    def skip_list(self):
        """
        Returns a list of atttributes to skip setting in set_params() function
        from the base class PDPanel
        """
        return ['Vdisp','Vratio','t','ro']
        
    def OnAnimate(self, event):
        SAF = ScrollAnimForm(self.Scroll.geo)
        SAF.Show()
        
    def OnChangeParam(self, event = None):
        
        Vdisp=float(self.Vdisp.GetValue())
        Vratio=float(self.Vratio.GetValue())
        t=float(self.t.GetValue())
        ro=float(self.ro.GetValue())
        
        self.Scroll.set_scroll_geo(Vdisp,Vratio,t,ro) #Set the scroll wrap geometry
        self.Scroll.set_disc_geo('2Arc', r2='PMP')
        
        self.phi_i0.SetValue(str(self.Scroll.geo.phi_i0))
        self.phi_is.SetValue(str(self.Scroll.geo.phi_is))
        self.phi_ie.SetValue(str(self.Scroll.geo.phi_ie))
        self.phi_o0.SetValue(str(self.Scroll.geo.phi_o0))
        self.phi_os.SetValue(str(self.Scroll.geo.phi_os))
        self.phi_oe.SetValue(str(self.Scroll.geo.phi_oe))
        self.rb.SetValue(str(self.Scroll.geo.rb))
        self.hs.SetValue(str(self.Scroll.geo.h))
        
        self.ax.cla()
        plotScrollSet(pi/4.0, axis = self.ax, geo = self.Scroll.geo)
        self.PP.canvas.draw()
    
    def post_set_params(self, scroll):
        Vdisp=float(self.Vdisp.GetValue())
        Vratio=float(self.Vratio.GetValue())
        t=float(self.t.GetValue())
        ro=float(self.ro.GetValue())
        
        scroll.set_scroll_geo(Vdisp,Vratio,t,ro) #Set the scroll wrap geometry
        scroll.set_disc_geo('2Arc', r2='PMP')
        scroll.geo.delta_flank = float(self.delta_flank.GetValue())
        scroll.geo.delta_radial = float(self.delta_radial.GetValue())
        
class FlankLeakageFlowChoice(pdsim_panels.MassFlowOption):
    
    def __init__(self,parent,**kwargs):
        pdsim_panels.MassFlowOption.__init__(self,parent,**kwargs)
    
    def model_options(self):
        return [
                dict(desc = 'Hybrid leakage model',
                     function_name = 'FlankLeakage',)
                ]
        
class RadialLeakageFlowChoice(pdsim_panels.MassFlowOption):
    
    def __init__(self,parent,**kwargs):
        pdsim_panels.MassFlowOption.__init__(self,parent,**kwargs)
    
    def model_options(self):
        return [
                dict(desc = 'Hybrid leakage model',function_name = 'RadialLeakage')
                ]

class SuctionFlowChoice(pdsim_panels.MassFlowOption):
    
    def __init__(self,parent,**kwargs):
        pdsim_panels.MassFlowOption.__init__(self,parent,**kwargs)
    
    def model_options(self):
        return [
                dict(desc = 'Isentropic nozzle',
                     function_name = 'SA_S',
                     params = [dict(attr = 'X_d',
                                    value = 0.3,
                                    desc = 'Tuning factor')]
                     )
                ]
                
class InletFlowChoice(pdsim_panels.MassFlowOption):
    
    def __init__(self,parent,**kwargs):
        pdsim_panels.MassFlowOption.__init__(self,parent,**kwargs)
        
    def model_options(self):
        return [
                dict(desc = 'Isentropic nozzle',
                     function_name = 'Inlet_sa',
                     params = [dict(attr = 'X_d',
                                    value = 0.3,
                                    desc = 'Tuning factor')]
                     )
                ]
                
class MassFlowPanel(pdsim_panels.PDPanel):
    
    def __init__(self, parent, configfile,**kwargs):
    
        pdsim_panels.PDPanel.__init__(self, parent,**kwargs)
        
        #Loads all the parameters from the config file
        self.configdict,self.descdict = self.get_from_configfile('MassFlowPanel')
        
        self.items1 = [
        dict(attr='d_discharge'),
        dict(attr='d_suction'),
        dict(attr='inlet_tube_length'),
        dict(attr='inlet_tube_ID'),
        dict(attr='outlet_tube_length'),
        dict(attr='outlet_tube_ID')
        ]
        box_sizer = wx.BoxSizer(wx.VERTICAL)
        box_sizer.Add(wx.StaticText(self,-1,"Required Inputs"))
        box_sizer.Add(wx.StaticLine(self,-1,(25, 50), (300,1)))
        
        sizer = wx.FlexGridSizer(cols=2, vgap=4, hgap=4)
        self.ConstructItems(self.items1,sizer,self.configdict,self.descdict)

        box_sizer.Add(sizer)  
        
        box_sizer.AddSpacer(10)
        box_sizer.Add(wx.StaticText(self,-1,"Flow Models"))
        box_sizer.Add(wx.StaticLine(self,-1,(25, 50), (300,1)))
#        self.flankflow = FlankLeakageFlowChoice(parent = self,
#                                           label = 'Flank leakage')
#        self.radialflow = RadialLeakageFlowChoice(parent = self,
#                                           label = 'Radial leakage')
        self.suctionflow1 = SuctionFlowChoice(parent = self,
                                              key1 = 'sa',
                                              key2 = 's1',
                                              label = 'Flow to suction chamber #1')
        self.suctionflow2 = SuctionFlowChoice(parent = self,
                                              key1 = 'sa',
                                              key2 = 's2',
                                              label = 'Flow to suction chamber #2')    
        self.inletflow = InletFlowChoice(parent = self,
                                         key1 = 'inlet.2',
                                         key2 = 'sa',
                                         label = 'Flow into shell',
                                         )
        
        self.flows = [self.suctionflow1, self.suctionflow2, self.inletflow]
#        self.flows = [self.flankflow,self.radialflow,self.suctionflow,self.inletflow]
        
        box_sizer.AddMany(self.flows)
        
        self.resize_flows(self.flows)
        
        self.SetSizer(box_sizer)
        box_sizer.Layout()
        
        self.items=self.items1
        
    def resize_flows(self, flows):
        min_width = max([flow.label.GetSize()[0] for flow in flows])
        for flow in flows:
            flow.label.SetMinSize((min_width,-1))
            
    def post_set_params(self, simulation):
        #Create and add each of the flow paths
        for flow in self.flows:
            func_name = flow.get_function_name()
            func = getattr(simulation, func_name)
            
            param_dict = {p['attr']:p['value'] for p in flow.params_dict}
            simulation.add_flow(FlowPath(key1 = flow.key1,
                                         key2 = flow.key2,
                                         MdotFcn = func,
                                         MdotFcn_kwargs = param_dict)
                                )
            
        if callable(simulation.Vdisp):
            Vdisp = simulation.Vdisp()
        else:
            Vdisp = simulation.Vdisp
        
        #Set omega and inlet state 
        parent = self.GetParent() #InputsToolBook
        for child in parent.GetChildren():
            if hasattr(child,'Name') and child.Name == 'StatePanel':
                child.set_params(simulation)
                child.post_set_params(simulation)
                        
        Vdot = Vdisp*simulation.omega/(2*pi)
        
        outletState=CPState.State(simulation.inletState.Fluid,{'T':400,'P':simulation.discharge_pressure})
        
        simulation.auto_add_leakage(flankFunc = simulation.FlankLeakage, 
                                    radialFunc = simulation.RadialLeakage)
            
        #Create and add each of the inlet and outlet tubes
        simulation.add_tube( Tube(key1='inlet.1',
                                  key2='inlet.2',
                                  L=simulation.inlet_tube_length, 
                                  ID=simulation.inlet_tube_ID,
                                  mdot=simulation.inletState.copy().rho*Vdot, 
                                  State1=simulation.inletState.copy(),
                                  fixed=1, 
                                  TubeFcn=simulation.TubeCode) )
    
        simulation.add_tube( Tube(key1='outlet.1',
                                  key2='outlet.2',
                                  L=simulation.outlet_tube_length,
                                  ID=simulation.outlet_tube_ID,
                                  mdot=outletState.copy().rho*Vdot, 
                                  State2=outletState.copy(),
                                  fixed=2,
                                  TubeFcn=simulation.TubeCode) )
        
        
class MechanicalLossesPanel(pdsim_panels.PDPanel):
    
    def __init__(self, parent, configfile,**kwargs):
    
        pdsim_panels.PDPanel.__init__(self, parent, **kwargs)
        
        #Loads all the parameters from the config file (case-sensitive)
        self.configdict, self.descdict = self.get_from_configfile('MechanicalLossesPanel')
        
        self.items = [
        dict(attr='eta_motor'),
        dict(attr='h_shell'),
        dict(attr='A_shell'),
        dict(attr='Tamb'),
        ]
        
        sizer = wx.FlexGridSizer(cols=2, vgap=4, hgap=4)
        
        self.ConstructItems(self.items,sizer,self.configdict,self.descdict)

        self.SetSizer(sizer)
        sizer.Layout()