#a completely new visualisation
#that uses the old stuff but is just better written
#steps
#read the grid file
#draw the basics: goals,doors,failstates,obstacles,robots
#update the goals from file
#update the robots from sta tra file
#end

#classes
#a class that reads the grid file
#a class that reads an sta tra file
#a class that handles the app stuff
#so we could have two of the same running side by side
#a bigger app which loads the grids etc


from tkinter import *
import Tkinter, Tkconstants, tkFileDialog, tkSimpleDialog

import math
from enum import Enum

import matplotlib.colors as mc
import colorsys

from readStaTra import ReadMDPStaTra

class ShapePoints():
    
    @staticmethod
    def getStarPoints(sxc,syc,p,t):
        points = []
        for i in (1,-1):
            points.extend((sxc,syc+i*p))
            points.extend((sxc+i*t,syc+i*t))
            points.extend((sxc+i*p,syc))
            points.extend((sxc+i*t,syc-i*t))
        return points

    @staticmethod
    def getCrossPoints(sx,sy,ex,ey):
        xlen =abs (ex - sx)
        ylen = abs(ey - sy )
        #cross points
        crosspoints = [(0,0),(0.2,0),(0.5,0.3),(0.8,0),(1,0),(1,0.2),(0.7,0.5),(1,0.8),(1,1),(0.8,1),(0.5,0.7),(0.2,1),(0,1),(0,0.8),(0.3,0.5),(0,0.2)]
        #first we've got to scale all the points
        minscale = min(xlen,ylen)
        mcrosspoints = []
        for t in crosspoints:
            mt = (t[0]*minscale+sx,t[1]*minscale+sy)
            mcrosspoints.append(mt)
        return mcrosspoints

    
class ColourHelper():
    
    @staticmethod
    def mixColor(color1,color2):
        if color1 is None:
            return color2
        if color2 is None:
            return color1
        
        rgbcolor = mc.to_rgb(color1)
        rgbcolor2 = mc.to_rgb(color2)
        mixedcolor = ((rgbcolor2[0]+rgbcolor[0])/2,(rgbcolor2[1]+rgbcolor[1])/2,(rgbcolor2[2]+rgbcolor[2])/2)
        mixedcolorstr = tuple([255*x for x in mixedcolor])
        mixedcolorstr = '#%02x%02x%02x' % mixedcolorstr
        return mixedcolorstr
    
        
    #from https://stackoverflow.com/questions/37765197/darken-or-lighten-a-color-in-matplotlib
    @staticmethod
    def lighten_color(color, amount=0.5):
        """
        Lightens the given color by multiplying (1-luminosity) by the given amount.1
        Input can be matplotlib color string, hex string, or RGB tuple.

        Examples:
        >> lighten_color('g', 0.3)
        >> lighten_color('#F034A3', 0.6)
        >> lighten_color((.3,.55,.1), 0.5)
        """


        #print color
        try:
            c = mc.cnames[color]
        except:
            c = color
        c = colorsys.rgb_to_hls(*mc.to_rgb(c))
        newc=colorsys.hls_to_rgb(c[0], 1 - amount * (1 - c[1]), c[2])
        #print newc
        newc=tuple([255*x for x in newc])
        #print newc
        newcstr= '#%02x%02x%02x' % newc
        #print newcstr
        return newcstr


class CellAttributes(Enum):
    BLOCKED=1
    EMPTY=2
    GOAL=3
    FAILSTATE=4
    DOOR=5
    AVOID=6
    INITIALLOC=7

class Path(object):
    def __init__(self,pathNumber,firstState,cell,canvas,color):
        self.pathnum = pathNumber
        self.states = [firstState]
        self.cells = {firstState:cell}
        self.statesDrawn = []
        self.canvas = canvas
        self.color = color
        self.doLines = True

    def fadePath(self,agnum=0,agsize=None):
        self.color = ColourHelper.lighten_color(self.color)
        self.clearPath()
        self.drawPath(agnum,agsize)
    
    def addStateCell(self,state,cell):
        self.states.append(state)
        if state not in self.cells:
            self.cells[state] = cell

    def getAgentCenter(self,cell,agsize,agnum):
        if agsize is None:
            return cell.getCellCoords()
        else:
            (xmin,xmax,ymin,ymax,xc,yc) = cell.getCellCoords()
            agxy = Agent.agnumtoxy[agnum]
            xpos = xmin+agxy[0]*agsize
            ypos = ymin+agxy[1]*agsize
            xposl = xpos+agsize
            yposl = ypos+agsize
            xposc = (xpos+xposl)/2
            yposc = (ypos+yposl)/2

        return (xpos,ypos,xposl,yposl,xposc,yposc)


    def clearPath(self):
        for obj in self.statesDrawn:
            self.canvas.delete(obj)
        self.statesDrawn = [] 

    def shiftPath(self,shiftby):
        #we get the path number
        for obj in self.statesDrawn:
            #shift by x
            if obj is not None:
                #coords = self.canvas.coords(obj)
                #newcoords = (coords[0]+shiftby,coords[1])
                #self.canvas.coords(obj,newcoords)
                self.canvas.move(obj,0,shiftby)

    def drawPath(self,agnum=0,agsize=None):
        if self.doLines:
            self.drawPathLines(agnum,agsize)
        else:
            self.drawPathCircles(agnum,agsize)

    def drawPathCircles(self,agnum=0,agsize=None):
        dotsize = 2
        if agsize is not None:
            dotsize = agsize/10 
        for i in range(len(self.states)):
            if len(self.statesDrawn) < (i+1):
                cs = self.states[i]
                cscell = self.cells[cs]
                csxy=cscell.getXY()
                (xmin,xmax,ymin,ymax,xc,yc) = self.getAgentCenter(cscell,agsize,agnum)
                
                obj = self.canvas.create_oval(xc-dotsize,yc-dotsize,xc+dotsize,yc+dotsize,fill=self.color,outline='white')
                self.statesDrawn.append(obj)
                
    def drawPathLines(self,agnum=0,agsize=None):
        w = 2
        #print ("Moving from states ")
        #print (self.states)
        for i in range(len(self.states)-1):
            #we want to draw a path for each state
            #first we must determine whether we have drawn this state or not
            #print ("Anything we've drawn")
            #print (self.statesDrawn)
            if len(self.statesDrawn) < (i+1):
                #we have not drawn this state
                cs = self.states[i]
                ns = self.states[i+1]
                cscell = self.cells[cs]
                nscell = self.cells[ns]
                csxy = cscell.getXY()
                nsxy = nscell.getXY()
                dir = 'none'
                if (csxy[1] == nsxy[1]):
                    if (csxy[0] < nsxy[0]):
                        dir = 'right'
                    elif (csxy[0]>nsxy[0]):
                        dir = 'left'
                elif (csxy[0] == nsxy[0]):
                    if(csxy[1] < nsxy[1]):
                        dir = 'up'
                    elif (csxy[1] > nsxy[1]):
                        dir = 'down'
                (xmin,xmax,ymin,ymax,xc,yc) = self.getAgentCenter(cscell,agsize,agnum)
                (xminn,xmaxn,yminn,ymaxn,xcn,ycn) = self.getAgentCenter(nscell,agsize,agnum)
                obj = None
                #print ("Direction : "+dir)
                if dir == 'up' or dir == 'down':
                    #draw a line in the middle xc from one yc to the other
                    obj = self.canvas.create_line(xc,yc,xc,ycn,width=w,fill=self.color)
                elif dir == 'right' or dir == 'left':
                    obj = self.canvas.create_line(xc,yc,xcn,yc,width=w,fill=self.color)

                #print ("We've drawn this now ")
                #print (obj)
                self.statesDrawn.append(obj)
                
                
                        
                
        
class Goal(object):
    def __init__(self,canvas,cell,loc):
        self.canvas = canvas
        self.cell = cell
        fill = Cell.FILLCOLOURS[CellAttributes.GOAL]
        self.visitedFill = ColourHelper.mixColor(fill,'red')
        self.visitFill = ColourHelper.mixColor(fill,'yellow')
        self.outline = Cell.BORDERCOLOURS[CellAttributes.GOAL]
        self.drawGoal = True
        self.visited = False
        self.numVisits = 0
        self.maxLen = cell.size/4
        self.maxWid = cell.size/8
        self.canvasobj = None
        self.isHidden = False 
        
        

    def draw(self):
        if self.drawGoal:
            fill = self.visitFill
            if self.visited:
                fill=self.visitedFill
            (xmin,xmax,ymin,ymax,xc,yc) = self.cell.getCellCoords()
            points = ShapePoints.getStarPoints(xc,yc,self.maxLen,self.maxWid)
            if self.canvasobj is not None:
                self.canvas.delete(self.canvasobj)
            self.canvasobj=self.canvas.create_polygon(points,fill=fill,outline=self.outline)
            self.canvas.lift(self.cell.labelObj)
        else:
            if self.canvasobj is not None:
                if not self.isHidden:
                    #hide object from canvas
                    self.canvas.itemconfigure(self.canvasobj, state='hidden')
                    self.isHidden = True

    def hideGoal(self):
        if not self.isHidden:
            self.drawGoal = False
            self.draw()

    def showGoal(self):
        self.drawGoal = True
        self.isHidden = False
        self.draw()

    def setVisited(self):
        if not self.visited:
            self.visited = True
            self.draw()

    def unsetVisited(self):
        if self.visited:
            self.visited = False
            self.draw()
        
    
class Agent(object):
    agnumtoxy={0:(0,0),1:(0,1),2:(0,2),3:(1,0),4:(1,2),5:(2,0),6:(2,1),7:(2,2),8:(0,0),9:(0,1)}
    def __init__(self,canvas,cell,size,currloc,agcolor,num):
        self.canvas = canvas
        self.currloc = currloc
        self.cell = cell 
        self.size = size
        self.deadCounter = 0
        self.dead = False
        self.drawAgent = True
        self.colour = agcolor
        self.canvasobj = {'shape':None,'number':None}
        self.num = num
        self.paths = {}
        self.hidden = False 

    

    def getAgentCenter(self):
        return self.getAgentCenterCell(self.cell)
        
    def getAgentCenterCell(self,cell):
        agsize = self.size
        (xmin,xmax,ymin,ymax,xc,yc) = cell.getCellCoords()
        agnum = self.num 
        agxy = Agent.agnumtoxy[agnum]
        xpos = xmin+agxy[0]*agsize
        ypos = ymin+agxy[1]*agsize
        xposl = xpos+agsize
        yposl = ypos+agsize
        xposc = (xpos+xposl)/2
        yposc = (ypos+yposl)/2

        return (xpos,ypos,xposl,yposl,xposc,yposc)

    def hide(self):
        if not self.hidden:
            self.drawAgent = False
            self.draw()

    def show(self):
        if self.hidden:
            self.hidden = False
            self.drawAgent()
        if not self.drawAgent:
            self.drawAgent = True
            self.draw()
            
    def draw(self):
        if self.drawAgent:
            if self.hidden:
                self.canvas.itemconfigure(self.canvasobj['shape'],state='normal')
                self.canvas.itemconfigure(self.canvasobj['number'],state='normal')
            else:
                
                (xpos,ypos,xposl,yposl,xposc,yposc) = self.getAgentCenter()
                #agsize = self.size
                #(xmin,xmax,ymin,ymax,xc,yc) = self.cell.getCellCoords()
                #agnum = self.num 
                #agxy = Agent.agnumtoxy[agnum]
                #xpos = xmin+agxy[0]*agsize
                #ypos = ymin+agxy[1]*agsize
                #xposl = xpos+agsize
                #yposl = ypos+agsize
                fill = self.colour #Cell.FILLCOLOURS[CellAttributes.INITIALLOC]
                outline='white'
                if self.dead:
                    crosspoints = ShapePoints.getCrossPoints(xpos,ypos,xposl,yposl)
                    self.canvasobj['shape']=self.canvas.create_polygon(cp,fill=fill,outline=outline)
                else:
                    self.canvasobj['shape']=self.canvas.create_oval(xpos,ypos,xposl,yposl,fill=fill,outline=outline)
                    #xposc = (xpos+xposl)/2
                    #yposc = (ypos+yposl)/2
                    self.canvasobj['number']=self.canvas.create_text((xposc,yposc),text=str(self.deadCounter))
        else:
            if not self.hidden:
                self.hidden = True
                if self.canvasobj['shape'] is not None:
                    self.canvas.itemconfigure(self.canvasobj['shape'],state='hidden')
                if self.canvasobj['number'] is not None:
                    self.canvas.itemconfigure(self.canvasobj['number'],state='hidden')
                

    def getMoveLimits(self,nextcell):
        (xmin,xmax,ymin,ymax,xc,yc) = self.cell.getCellCoords()
        (xminn,xmaxn,yminn,ymaxn,xcn,ycn) = nextcell.getCellCoords()
        xmove = xminn-xmin
        ymove = yminn-ymin
        return (xmove,ymove)
    
    def updateCell(self,nextloc,nextcell,currentPath=0):
        if currentPath not in self.paths:
            self.paths[currentPath] = Path(currentPath,self.currloc,self.cell,self.canvas,self.colour)
        self.paths[currentPath].addStateCell(nextloc,nextcell)
        
        #self.paths[currentPath].append({'loc':self.currloc,'cell':self.currcell,'ncell':nextcell}]
        (xmove,ymove) = self.getMoveLimits(nextcell)
        self.currloc = nextloc
        self.cell = nextcell
        #move the agent
        self.canvas.move(self.canvasobj['shape'],xmove,ymove)
        self.canvas.move(self.canvasobj['number'],xmove,ymove)
        self.drawAllPaths(currentPath,True)

    def drawAllPaths(self,currentPath,removeAllPreviousPaths=False):
        if self.drawAgent:
            for p in self.paths:
                if p == currentPath:
                    self.paths[p].drawPath(self.num,self.size)
                else:
                    if removeAllPreviousPaths:
                        self.paths[p].clearPath()
                    else:
                        if currentPath-p < 10:
                            shiftby = 2
                            self.paths[p].fadePath(self.num,self.size)
                            self.paths[p].shiftPath(shiftby)
                        else:
                            self.paths[p].clearPath()
                            

    def shiftAllPaths(self,shiftby):
        if self.drawAgent:
            for p in self.paths:
                self.paths[p].fadePath(self.num,self.size)
                self.paths[p].shiftPath(shiftby)
            
        
    
        
class Cell(object):

    FILLCOLOURS = {CellAttributes.BLOCKED:'black',CellAttributes.EMPTY:'white',CellAttributes.GOAL:'green',CellAttributes.AVOID:'red',CellAttributes.FAILSTATE:'lightgrey',CellAttributes.DOOR:'brown',CellAttributes.INITIALLOC:'blue'}

    BORDERCOLOURS={CellAttributes.BLOCKED:'black',CellAttributes.EMPTY:'black',CellAttributes.GOAL:'green',CellAttributes.AVOID:'red',CellAttributes.FAILSTATE:'grey',CellAttributes.DOOR:'purple',CellAttributes.INITIALLOC:'blue'}
        
    def __init__(self,canvas,x,y,size):
        self.canvas = canvas
        self.abs = x
        self.ord = y
        self.size = size

        self.cellAttributes=[]
        
        self.otherDoor = None
        self.label = str(y)+","+str(x)
        self.defaultLabel = str(y)+","+str(x)
        self.rectangle = None
        self.labelObj = None
        

    def getXY(self):
        return (self.abs,self.ord)
    
    def clearAllFlags(self):
        self.cellAttributes=[]
        self.otherDoor = None

    def clearGoal(self):
        self.cellAttributes.remove(CellAttributes.GOAL)

    def clearInitialLocation(self):
        self.cellAttributes.remove(CellAttributes.INITIALLOC)

    def drawAvoid(self,xmin,ymin,xmax,ymax,defaultfill,defaultoutline):
        circlefill = Cell.FILLCOLOURS[CellAttributes.AVOID]
        ovaldist = (xmax-xmin)/10
        
        self.canvas.create_oval(xmin,ymin,xmax,ymax,fill=circlefill,outline=defaultoutline)
        self.canvas.create_oval(xmin+ovaldist,ymin+ovaldist,xmax-ovaldist,ymax-ovaldist,fill=defaultfill,outline=defaultoutline)

        self.canvas.create_line(xmin+2*ovaldist,ymin+2*ovaldist,xmax-2*ovaldist,ymax-2*ovaldist,width=ovaldist,fill=circlefill)

    def drawGoal(self,xc,yc,visited=False):
        starMaxLen = self.size/4
        starTinyLen = self.size/8
        starfill = Cell.FILLCOLOURS[CellAttributes.GOAL]
        staroutline = Cell.BORDERCOLOURS[CellAttributes.GOAL]
        if visited:
            starfill = ColourHelper.mixColor(starfill,'red')
        else:
            starfill = ColourHelper.mixColor(starfill,'yellow')
        starpoints = ShapePoints.getStarPoints(xc,yc,starMaxLen,starTinyLen)
        self.canvas.create_polygon(starpoints,fill=starfill,outline=staroutline)

    def drawAgent(self,xmin,ymin,agnum,deadCounter=0,dead=False):
        agsize = self.size/3
        agnumtoxy={0:(0,0),1:(0,1),2:(0,2),3:(1,0),4:(1,2),5:(2,0),6:(2,1),7:(2,2)}
        agxy = agnumtoxy[agnum]
        xpos = xmin+agxy[0]*agsize
        ypos = ymin+agxy[1]*agsize
        xposl = xpos+agsize
        yposl = ypos+agsize
        fill = Cell.FILLCOLOURS[CellAttributes.INITIALLOC]
        outline=Cell.BORDERCOLOURS[CellAttributes.INITIALLOC]
        if dead:
            crosspoints = ShapePoints.getCrossPoints(xpos,ypos,xposl,yposl)
            self.canvas.create_polygon(cp,fill=fill,outline=outline)
        else:
            self.canvas.create_oval(xpos,ypos,xposl,yposl,fill=fill,outline=outline)
        xposc = (xpos+xposl)/2
        yposc = (ypos+yposl)/2
        self.canvas.create_text((xposc,yposc),text=str(deadCounter))
            
        

    def drawDoor(self,xmin,ymin,xmax,ymax):
        doorwidth = self.size/20
        linew = doorwidth
        fill = Cell.FILLCOLOURS[CellAttributes.DOOR]
        d = self.getXY()
        od = self.otherDoor
        #print (d)
        #print (od)
        if d[1] == od[1]:
            #create door on x
            if d[0] < od[0]:
                self.canvas.create_line(xmax,ymin,xmax,ymax,w=linew,dash=(3,5),fill=fill)
                #self.canvas.create_rectangle(xmax-doorwidth,ymin,xmax,ymax,stipple='gray75',fill=fill)
                #print ("Drawing at xmax,")
            else:
                self.canvas.create_line(xmin,ymin,xmin,ymax,w=linew,dash=(3,5),fill=fill)
                #self.canvas.create_rectangle(xmin,ymin,xmin+doorwidth,ymax,stipple='gray75',fill=fill)
                #print ("Drawing at xmin")
        else:
            if d[1] < od[1]:
                self.canvas.create_line(xmin,ymax,xmax,ymax,w=linew,dash=(3,5),fill=fill)
            else:
                self.canvas.create_line(xmin,ymin,xmax,ymin,w=linew,dash=(3,5),fill=fill)
        #        self.canvas.create_rectangle(xmin,ymax-doorwidth,xmax,ymax,stipple='gray75',fill=fill)
        #    else:
        #        self.canvas.create_rectangle(xmin,ymin,xmax,ymin+doorwidth,stipple='gray75',fill=fill)
        #if d[0] == 1:
        #self.canvas.create_line(xmax,ymin+self.size/4,xmax-self.size/4,ymax-self.size/3,width=2,fill=fill)
        #self.canvas.create_line(xmax-self.size/4,ymax-self.size/3,xmax,ymax-self.size/4,width=2,fill=fill)
        #self.canvas.create_rectangle(
            
            
    def getCellCoords(self):
        xmin = self.abs*self.size
        xmax = xmin + self.size
        ymin = self.ord * self.size
        ymax = ymin + self.size
        xc = (xmax-xmin)/2 + xmin
        yc = (ymax-ymin)/2 + ymin
        return (xmin,xmax,ymin,ymax,xc,yc)
        
    def draw(self):
        (xmin,xmax,ymin,ymax,xc,yc)=self.getCellCoords()


        fillhere = Cell.FILLCOLOURS[CellAttributes.EMPTY]
        outlinehere = Cell.BORDERCOLOURS[CellAttributes.EMPTY]
        stipplehere = ''

        if CellAttributes.BLOCKED in self.cellAttributes:
            fillhere = Cell.FILLCOLOURS[CellAttributes.BLOCKED]
            outlinehere=Cell.BORDERCOLOURS[CellAttributes.BLOCKED]
        else:
            if CellAttributes.FAILSTATE in self.cellAttributes:
                fillhere = Cell.FILLCOLOURS[CellAttributes.FAILSTATE]
                outlinehere=Cell.BORDERCOLOURS[CellAttributes.FAILSTATE]
            
            
        
        self.rectangle=self.canvas.create_rectangle(xmin,ymin,xmax,ymax,fill=fillhere,outline=outlinehere,stipple=stipplehere)
        if CellAttributes.AVOID in self.cellAttributes:
            self.drawAvoid(xmin,ymin,xmax,ymax,fillhere,outlinehere)
        if CellAttributes.DOOR in self.cellAttributes:
            self.drawDoor(xmin,ymin,xmax,ymax)
        #if CellAttributes.GOAL in self.cellAttributes:
        #    self.drawGoal(xc,yc)
        #if CellAttributes.INITIALLOC in self.cellAttributes:
        #    self.drawAgent(xmin,ymin,0)
        
        self.labelObj=self.canvas.create_text((xc,yc),text=self.label)
        
class GridFileReader(object):
    def readGridFile(self,fn):
        with open(fn) as gfile:
            lines = gfile.readlines()

            rowcolumnsize = lines[0].replace('\n','')
            rowcolumnsize = rowcolumnsize.split(',')
            
            row = int(rowcolumnsize[0])
            column = int(rowcolumnsize[1])
            size = int(rowcolumnsize[2])
            rowNumber = row
            columnNumber = column
            cellSize = size
            xydict = {}
            for i in range(1,len(lines)):
                line = lines[i].replace('\n','')
                xys = line.split('*')
                flags = xys[1].replace(']','')
                xys = xys[0]
                xys = xys.replace('[','')
                xys = xys.replace('(','')
                xys = xys.replace(')','')
                xys = xys.split(',')
                
                xydict[(int(xys[0]),int(xys[1]))] = eval(flags)
                
        return (row,column,size,xydict)

            

class CanvasWorld(object):
    MAXSIZE=(18.0*18.0*50.0*50.0)
    ROBOT_COLORS_LIST=[mc.XKCD_COLORS['xkcd:aqua'],mc.XKCD_COLORS['xkcd:beige'],mc.XKCD_COLORS['xkcd:coral'],mc.XKCD_COLORS['xkcd:fuchsia'],mc.XKCD_COLORS['xkcd:indigo'],mc.XKCD_COLORS['xkcd:goldenrod'],mc.XKCD_COLORS['xkcd:khaki'],mc.XKCD_COLORS['xkcd:lavender'],mc.XKCD_COLORS['xkcd:lightblue'],mc.XKCD_COLORS['xkcd:tomato'],mc.XKCD_COLORS['xkcd:pink'],mc.XKCD_COLORS['xkcd:teal']]
    
    def calculateDimensions(self,size=50,ncols=10,nrows=10):
        maxCellsSide = max(ncols,nrows)
        numCells = maxCellsSide*maxCellsSide
        #print ("Num Cells: "+str(numCells))
        newsize = CanvasWorld.MAXSIZE/float(numCells)
        #print ("New cell area "+str(newsize))
        newsize = math.sqrt(newsize)
        #print ("One side "+str(newsize))
        newsize = int(newsize)
        #print ("Max Area = "+str(CanvasWorld.MAXSIZE))
        #print ("Original Size = "+str(size)+" New Size = "+str(newsize))
        return newsize

    def __init__(self,name):
        self.canvas = None
        self.cellsize = None
        self.rows = None
        self.cols = None
        self.name = name
        self.goals = None
        self.agents = None
        self.grid = None
        self.goalNumbersDict = None
        self.currentGoals = None
        self.policyObj = None
        self.currentAgents = None
        

    def initialiseOrResetCanvas(self,app,size=50,ncols=10,nrows=10):
        size = self.calculateDimensions(size,ncols,nrows)
        w = ncols*size
        h = nrows*size
        self.rows = nrows
        self.cols = ncols
        
        if self.canvas is not None:
            self.canvas.delete('all')
        else:
            self.canvas = Canvas(app,width=w, height=h)
        self.cellsize = size 

    def fillCanvasWithCells(self,xydict=None):
        self.agents = {}
        self.grid = []
        self.goals = {}
        doorsList = {}
        agsize = self.cellsize/3
        labelsmap = {}
        for row in range(self.rows):
            line = []
            for col in range(self.cols):
                cell = Cell(self.canvas,col,row,self.cellsize)
                if xydict is not None:
                    if (row,col) in xydict:
                        flagsHere = xydict[(row,col)]
                        if flagsHere['fill']:
                            cell.cellAttributes.append(CellAttributes.BLOCKED)


                        if flagsHere['isFailState']:
                            cell.cellAttributes.append(CellAttributes.FAILSTATE)
                        if flagsHere['isAvoidState']:
                            cell.cellAttributes.append(CellAttributes.AVOID)
                        if flagsHere['isDoor']:
                            cell.cellAttributes.append(CellAttributes.DOOR)
                            cell.otherDoor = flagsHere['otherDoor']
                            doorsList[(row,col)]=cell
                            #see if we have a corresponding door
                            doorOptions = [(row-1,col),(row,col-1),(row+1,col),(row,col+1)]
                            #doorFound = False 
                            for doorOption in doorOptions:
                                if doorOption in doorsList:
                                    cell.otherDoor = doorsList[doorOption].getXY()
                                    doorsList[doorOption].otherDoor = cell.getXY()
                                    #print (doorOption)
                                    #print ((row,col))
                                    #raw_input(doorsList)
                                    #doorFound = True
                                    #del doorsList[doorOption]
                                    break
                            #if not doorFound:
                                
                                    
                                    
                            
                        cell.label = flagsHere['label']
                        if not "," in cell.label:
                            labelint = int(cell.label)
                            if labelint not in labelsmap:
                                labelsmap[labelint]=cell

                        if flagsHere['isGoalPos']:
                            cell.cellAttributes.append(CellAttributes.GOAL)
                            goal = Goal(self.canvas,cell,labelint)
                            self.goals[labelint] = goal
                            
                        if flagsHere['isInitPos']:
                            cell.cellAttributes.append(CellAttributes.INITIALLOC)
                            #theres an agent here
                            agnum = len(self.agents)
                            agcolor = CanvasWorld.ROBOT_COLORS_LIST[agnum]
                            agent = Agent(self.canvas,cell,agsize,labelint,agcolor,agnum)
                            agent.drawAgent = True 
                            self.agents[agnum]=agent
                            
                        
                                
                line.append(cell)
            self.grid.append(line)
        #self.drawCells()
        self.labelsmap=labelsmap

    def moveAgents(self):
        if self.currentAgents is None:
            for ag in self.agents:
                agent = self.agents[ag]
                currloc = agent.currloc
                if (currloc+1) in self.labelsmap:
                    agent.updateCell(currloc+1,self.labelsmap[currloc+1])
                    if (currloc+1) in self.goals:
                        self.goals[currloc+1].setVisited()
        else:
            if self.policyObj is not None:
                if self.currentJointState is not None:
                    self.moveAgentsFromPolicy()
                    if self.currentJointState is not None:
                        agentsLocDict = self.policyObj.getAgentStatesFromState(self.currentJointState)
                        for agnum in agentsLocDict:
                            coragnum = self.currentAgents[agnum]
                            agent = self.agents[coragnum]
                            currloc = agent.currloc
                            nextloc = agentsLocDict[agnum]
                            if nextloc in self.labelsmap:
                                agent.updateCell(nextloc,self.labelsmap[nextloc],self.pathNumber)
                                if nextloc in self.goals:
                                    self.goals[nextloc].setVisited()
                        

        
    def drawAgents(self):
        if self.currentAgents is None:
            for ag in self.agents:
                self.agents[ag].draw()
        else:
            for ag in self.agents:
                if ag in self.currentAgentsList:
                    self.agents[ag].show()
                else:
                    self.agents[ag].hide()
                    
                    
                


    def drawGoals(self):
        if self.currentGoals is None:
            for gl in self.goals:
                self.goals[gl].draw()
        else:
            for gl in self.goals:
                if gl in self.currentGoals:
                    self.goals[gl].showGoal()
                else:
                    self.goals[gl].hideGoal()
                    
            
    def drawCells(self):
        for row in self.grid:
            for cell in row:
                cell.draw()

        #last cell
        centerx = self.rows*self.cellsize/2

        edgey = self.cols*self.cellsize+self.cellsize/2

        self.canvas.create_text((centerx,edgey),text=self.name)

    def packCanvas(self,side):
        self.canvas.pack(side=side,expand=True,fill='both')
        self.drawCells()
        self.drawGoals()
        self.drawAgents()


    def shiftAgentPaths(self,shiftby):
        for ag in self.agents:
            self.agents[ag].shiftAllPaths(shiftby)


    def setCurrentGoalsAndGoalDict(self,goalDict,goalNumbers):
        if goalDict is not None:
            self.goalNumbersDict = goalDict
        if goalNumbers is not None:
            self.currentGoals = [goalDict[i] for i in goalNumbers]
            #redraw goals
            self.drawGoals()

    def setPolicyObj(self,staname,traname):
        print ("Reading Policy From File: "+staname+"\n"+traname)
        self.policyObj = ReadMDPStaTra(staname,traname)
        self.policyObj.readsta()
        self.policyObj.readtra()
        startState = 0
        self.setAgents(startState)
        self.currentJointState = startState
        self.pathNumber = 0
        self.statesToExploreLater=[]
        self.parentStates={}
        self.parentPaths={}
        

    def setAgents(self,state):
        agentsLocDict = self.policyObj.getAgentStatesFromState(state)
        if self.currentAgents is None:
            self.currentAgents = {}
            self.currentAgentsList=[]
            #we need to set the current Agents
            #just do all new agents
            for ag in self.agents:
                agloc = self.agents[ag].currloc
                for aag in agentsLocDict:
                    aagloc = agentsLocDict[aag]
                    if aagloc == agloc:
                        self.currentAgents[aag]=ag
                        self.currentAgentsList.append(ag)
            self.drawAgents()


    def moveAgentsFromPolicy(self):
        nextJSes=self.policyObj.getMostProbableStateReactive(self.currentJointState)
        if nextJSes is not None:
            mostProbableNextJS = nextJSes[0]
            for js in nextJSes[1]:
                if js not in self.statesToExploreLater:
                    self.statesToExploreLater.append(js)
                    self.parentStates[js]=self.currentJointState
                    self.parentPaths[js]=self.pathNumber
            agentsLocDict = self.policyObj.getAgentStatesFromState(mostProbableNextJS)
            self.currentJointState = mostProbableNextJS
        else:
            if len(self.statesToExploreLater) > 0:
                self.currentJointState = self.statesToExploreLater.pop()
                self.pathNumber = self.pathNumber + 1
                print (self.currentJointState)
                print (self.pathNumber)
                raw_input("Exploring new trajectory")
        
            
            
                    
            
        

class GridGuiGoalsDialog(tkSimpleDialog.Dialog):

    def body(self,master):
        self.goalsList = '0,1,2,3,4,5,6,7,8,9'
        defaultGoalsList = StringVar(master,value=self.goalsList)
        Label(master,text="Goals List:").grid(row=0,sticky=W)
        self.gl=Entry(master,textvariable=defaultGoalsList)
        self.gl.grid(row=0,column=1)
        self.goalsArray = None 

    def apply(self):
        goalsList = self.gl.get()
        
        #validating
        import re
        pattern = re.compile(r"[\d\s?,]*")
        if not pattern.match(goalsList):
            print ("Invalid goals list pattern. Expected 1,2,3,4,5... Got "+goalsList+". Reverting to default "+self.goalsList)
            goalsList = self.goalsList
        goalsArray = eval('['+goalsList+']')
        self.goalsArray = goalsArray
        

class GridGuiStaTraDialog(tkSimpleDialog.Dialog):
    defaultAddress = "/home/fatma/Data/PhD/code/prism_ws/prism-svn/prism/tests/wkspace/smallerwhdoors/results/logs/debugRes/extras"
    
    def body(self,master):
        self.stapustaname = None
        self.staputraname = None
        self.ssistaname = None
        self.ssitraname = None
        self.addressToOpen = GridGuiStaTraDialog.defaultAddress
        
        #self.addressToOpen = defaultAddress 
        defaultAddressVar = StringVar(master,value=self.addressToOpen)
        
        Label(master,text="STAPU File:").grid(row=0,sticky=W)
        self.stapufilebox = Entry(master,textvariable=defaultAddressVar)
        self.stapufilebox.grid(row=0,column=1)
        self.stapufilebutton = Button(master,text='Open Folder',command=self.openStapuFile)
        self.stapufilebutton.grid(row=0,column=2)
        
        Label(master,text="Auctioning File:").grid(row=1,sticky=W)
        self.ssifilebox = Entry(master,textvariable=defaultAddressVar)
        self.ssifilebox.grid(row=1,column=1)
        self.ssifilebutton = Button(master,text='Open Folder',command=self.openSsiFile)
        self.ssifilebutton.grid(row=1,column=2)
        
        

    def openFile(self):
        fn = tkFileDialog.askopenfilename(initialdir=self.addressToOpen,title="Open sta/tra File", filetypes=(("sta",".sta"),("tra",".tra"),("all files","*.*")))
        staname = None
        traname = None
        
        if '.sta' in fn:
            staname = fn
            traname = fn.replace('.sta','.tra')
        elif '.tra' in fn:
            traname = fn
            staname = fn.replace('.tra','.sta')
        else:
            print("Invalid file extension")
        return (staname,traname)

    def openStapuFile(self):
        (staname,traname) = self.openFile()
        if staname is not None:
            address = staname[0:staname.rfind('/')]
            self.addressToOpen = address
            self.stapustaname = staname
            self.staputraname = traname
            self.stapufilebox.delete(0,END)
            self.stapufilebox.insert(0,staname)


    def openSsiFile(self):
        (staname,traname) = self.openFile()
        if staname is not None:
            address = staname[0:staname.rfind('/')]
            self.addressToOpen = address
            self.ssistaname = staname
            self.ssitraname = traname
            self.ssifilebox.delete(0,END)
            self.ssifilebox.insert(0,staname)
            

    def apply(self):
        print ("STAPU:\n"+self.stapustaname+"\n"+self.staputraname)
        print ("Auctioning:\n"+self.ssistaname+"\n"+self.ssitraname)
        print ("All Done")
            
        
        

class GoalsFileReader(object):
    
    def getLines(self,fn):
        lines = None
        with open(fn) as f:
            lines = f.readlines()
        return lines

    def propRegex(self,propBit):
        import re
        res=[]
        regex = ur"F \(\"s(\d*)\"\)"


        matches = re.finditer(regex, propBit)

        for matchNum, match in enumerate(matches, start=1):

            #print ("Match {matchNum} was found at {start}-{end}: {match}".format(matchNum = matchNum, start = match.start(), end = match.end(), match = match.group()))

            for groupNum in range(0, len(match.groups())):
                groupNum = groupNum + 1

                #print ("Group {groupNum} found at {start}-{end}: {group}".format(groupNum = groupNum, start = match.start(groupNum), end = match.end(groupNum), group = match.group(groupNum)))
                res.append(int(match.group(groupNum)))
        return res
                

    def readPropsFile(self,propsFile):
        lines = self.getLines(propsFile)
        goals = {}
        for line in lines:
            pline = line.strip()
            pline = pline.split(',')
            for i in range(len(pline)):
                p = pline[i]
                print(p)
                res=self.propRegex(p)
                if(len(res)>0):
                    #print(res)
                    goals[i] = res[0]
        print(goals)
        return goals
    
class MainApp(object):

    StapuCanvasSide = 'left'
    SsiCanvasSide = 'right'
    def loadGridFile(self):
        fn = tkFileDialog.askopenfilename(initialdir="/home/fatma/Data/PhD/code/prism_ws/prism-svn/prism/tests/wkspace/smallerwhdoors/",title="Open Grid File", filetypes=(("grid",".grid"),("all files","*.*")))
        filename = fn[fn.rfind("/")+1:]
        filename = filename.replace('.grid','')
        self.fnguide = filename 
        print ("Loading "+ filename)
        gfr = GridFileReader()
        (row,column,size,xydict)=gfr.readGridFile(fn)
        self.initialiseStapuSsiCanvases(size,column,row)
        #so now we can fill a canvas with xy dict
        self.stapucanvas.fillCanvasWithCells(xydict)
        self.stapucanvas.packCanvas(MainApp.StapuCanvasSide)
        self.ssicanvas.fillCanvasWithCells(xydict)
        self.ssicanvas.packCanvas(MainApp.SsiCanvasSide)


    def loadGoalsFile(self):
        fn = tkFileDialog.askdirectory(initialdir="/home/fatma/Data/PhD/code/prism_ws/prism-svn/prism/tests/wkspace/smallerwhdoors/",title="Open Properties File Directory")
        folder = fn +'/'
        if self.fnguide is None:
            fn = tkFileDialog.askopenfilename(initialdir="/home/fatma/Data/PhD/code/prism_ws/prism-svn/prism/tests/wkspace/smallerwhdoors/",title="Open Goals File", filetypes=(("prop",".prop"),("all files","*.*")))
            filename = fn 
        else:
            filename = folder + self.fnguide+'.prop'
        print ("Loading file "+filename)
        gfr = GoalsFileReader()
        goals = gfr.readPropsFile(filename)
        print ("Goals "+str(goals))
        if self.fnguide is None:
            fnguide = filename[filename.rfind('/')+1:filename.rfind('.prop')]
        else:
            fnguide = self.fnguide
        print (fnguide)

        #you can either enter the goals by hand or select a file for them
        
        goalsHere = None
        
        #if(d.goalsArray is None):
        fn = tkFileDialog.askopenfilename(initialdir="/home/fatma/Data/PhD/code/prism_ws/prism-svn/prism/tests/wkspace/smallerwhdoors/results/logs/",title="Open Goals File", filetypes=(("stapu",fnguide+"*_stapu.txt"),("all files","*.*")))
            #we just parse the filename
        if fn:
            import re
            regex = ur"_G:\d-\[([\d\s?,]*)\]"
            matches = re.findall(regex,fn)
            print (matches)
            matches = '['+matches[0]+']'
            goalsHere = eval(matches)
        else:
            d = GridGuiGoalsDialog(self.app)
            goalsHere = d.goalsArray

        #now we just do the goals
        #set the goals for both stapu and ssi
        self.stapucanvas.setCurrentGoalsAndGoalDict(goals,goalsHere)
        self.ssicanvas.setCurrentGoalsAndGoalDict(goals,goalsHere)
        #now we've got all the goals
        #now we set them up
        #we just update the canvas with them 
                
        #print(d.goalsArray)
        
    def loadStaTra(self):
        d = GridGuiStaTraDialog(self.app)
        staputraname = d.staputraname
        stapustaname = d.stapustaname
        ssitraname = d.ssitraname
        ssistaname = d.ssistaname
        if(stapustaname is not None):
            self.stapucanvas.setPolicyObj(stapustaname,staputraname)
        if ssistaname is not None:
            self.ssicanvas.setPolicyObj(ssistaname,ssitraname)
        
    def initialiseStapuSsiCanvases(self,updatedSize=50,column=10,row=10):
        self.stapucanvas.initialiseOrResetCanvas(self.app,updatedSize,column,row)
        self.ssicanvas.initialiseOrResetCanvas(self.app,updatedSize,column,row)
        self.stapucanvas.fillCanvasWithCells()
        self.ssicanvas.fillCanvasWithCells()
        self.stapucanvas.packCanvas(MainApp.StapuCanvasSide)
        self.ssicanvas.packCanvas(MainApp.SsiCanvasSide)

    
    def exitApp(self):
        self.app.destroy()
        
    def generateMenu(self):
        menu = Menu(self.app)
        menu.add_command(label='Grid File',command=self.loadGridFile)
        menu.add_command(label='Goals File',command=self.loadGoalsFile)
        menu.add_command(label='Policy Files',command=self.loadStaTra)
        
        menu.add_command(label='Move Agents',command=self.moveAgentsOnBothCanvases)
        menu.add_command(label='Start Animation',command=self.animateAgentsOnBothCanvases)
        menu.add_command(label='Stop Animation',command=self.stopAnimationOnBothCanvases)
        menu.add_command(label='Shift Path', command=self.shiftPaths)
        menu.add_command(label='Exit',command=self.exitApp)
        self.app.config(menu=menu)

        

    def shiftPaths(self):
        self.stapucanvas.shiftAgentPaths(10)
    
        
    def moveAgentsOnBothCanvases(self):
        if self.animateBothCanvases:
            self.stapucanvas.moveAgents()
            self.ssicanvas.moveAgents()
            self.app.after(100,self.moveAgentsOnBothCanvases)
        else:
            self.stapucanvas.moveAgents()
            self.ssicanvas.moveAgents()


    def animateAgentsOnBothCanvases(self):
        self.animateBothCanvases = True


    def stopAnimationOnBothCanvases(self):
        self.animateBothCanvases = False
            

        
    def __init__(self):
        self.animateBothCanvases = False
        self.fnguide = None 
        self.app = Tk()
        self.stapucanvas = CanvasWorld('STAPU')
        self.ssicanvas = CanvasWorld('Auctioning')
        #lets load the main window
        self.initialiseStapuSsiCanvases()
        self.generateMenu()
        self.app.title('STAPU/Auctioning Visualiser')

        
        self.app.mainloop()

    
        
        


if __name__=="__main__":
    ma = MainApp()
    
