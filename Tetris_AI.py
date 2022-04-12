import numpy as np
import random
import pygame as pg
import pandas as pd
import time

class CTetrisException(Exception):
    """
    базовое прерывание от логики тетриса
    """
    pass

class CTetris():
    """
    реализует логику игры тетрис - движение фигур, сжигание линий, проверку логики
    """
    def __init__(self,W=12,H=21):
        self.W = W
        self.H = H
        self.Area = np.zeros((W,H),dtype=np.int8) # игровое поле
        self.Area[0,:]=1 # окаймляем единицами
        self.Area[W-1,:]=1
        self.Area[:,H-1]=1
        self.Figure = np.zeros((4,4),dtype=np.int8) # размер фигуры 4х4
        self.X = 5
        self.Y = 5
        self.Angle = 0
        self.Score = 0
        self.newFigure()
        
    def rotateFigure(self,dAngle):
        rot = np.zeros((4,4),dtype=int)
        for a in range(4):
            for b in range(4):
                if dAngle==1:
                    rot[a,b] = self.Figure[3-b,a]
                else:
                    rot[a,b] = self.Figure[b,3-a] 
                    
        self.Angle += dAngle
        try:
            self.testFigure(self.X,self.Y,rot)
        except CTetrisException:
            return False # тут что-то записать в лог
        else:
            self.Figure[:,:] = rot[:,:]
            return True
        
    def moveFigureX(self,dx):
        try:
            self.testFigure(self.X+dx,self.Y)
        except CTetrisException:
            return False
        else:
            self.X += dx
            return True
        
    def setFigureShiftValue(self,x_shift):
        if self.X>x_shift:
            self.moveFigureX(-1)
        if self.X<x_shift:
            self.moveFigureX(1)
            
        return 
            
    def setFigureRotateValue(self,y_rot):
        r1 = y_rot%4
        r2 = self.Angle%4
        while r1!=r2: # крутим, пока не достигнем нужного поворота
            self.rotateFigure(1)
            r2 = self.Angle%4
            
            
    def moveFigureDown(self,dy):
        try:
            self.testFigure(self.X,self.Y+dy)
        except CTetrisException:
            return False
        else:
            self.Y += dy
            return True
        
    def initFigure(self, figType = None):
        """ инициализировать новую фигуру """
        if figType is None:
            figType = random.randint(0,6)
            
        self.figType = figType
        self.X = 5
        self.Y = 0

        self.Figure[:,:] = 0 # очистка фона фигуры

        if figType == 0: # палка
            self.Figure[:,1] = 1

        elif figType == 1: # куб
            self.Figure[1:3,1:3] = 1

        elif figType == 2: # T
            self.Figure[1:4,0] = 1
            self.Figure[2,1] = 1

        elif figType == 3: # Г 
            self.Figure[1:4,0] = 1
            self.Figure[1,1] = 1

        elif figType == 4: # Г 
            self.Figure[1:4,0] = 1
            self.Figure[3,1] = 1

        elif figType == 5: # Z
            self.Figure[1:3,0] = 1
            self.Figure[2:4,1] = 1

        elif figType == 6: # Z
            self.Figure[1:3,1] = 1
            self.Figure[2:4,0] = 1
        
        self.testFigure(self.X,self.Y)
        

    def getCell(self,i,j):
        """ проверить заполненность ячейки игрового поля """
        a = i-self.X
        b = j-self.Y
        
        # в ячейке сама фигура
        if a>=0 and b>=0 and a<4 and b<4 and self.Figure[a,b]!=0:
            return True
        # в ячейке фон
        if self.Area[i,j]!=0:
            return True
        
        return False


    def testFigure(self,X,Y,testFigure = None):
        """ проверить, можно ли поместить фигуру по координатам X,Y """
        if testFigure is None:
            testFigure = self.Figure
        for a in range(4):
            for b in range(4):
                i = a+X
                j = b+Y
                if testFigure[a,b]!=0 and self.Area[i,j]!=0:
                    raise CTetrisException() # кидаем исключение, совпадение ненулевых ячеек фигуры и поля
                    #return False
        return True
    
    def newFigure(self):
        self.frostFigure(self.X,self.Y) # замораживаем ее на игровом поле
        self.removeLines()  
        self.initFigure()
        
    
    def frostFigure(self,X,Y):
        """ 'заморозить' фигуру на игровом поле """
        for a in range(4):
            for b in range(4):
                i = a+X
                j = b+Y
                if i<self.W and j<self.H:
                    self.Area[i,j] += self.Figure[a,b]
        

    def removeLines(self):
        """ удалить полные линии игрового поля, сдвинуть игровое поле вниз. Возвращает изменение счета"""
        def isFullLine(lineNum):
            for i in range(self.W):
                if self.Area[i,lineNum] == 0:
                    return False
            return True

        repeat_again = True
        score = 0
        while repeat_again:
            repeat_again = False
            for hh in range(self.H-2,1,-1):
                if isFullLine(hh):
                    self.Area[:,1:hh+1] = self.Area[:,0:hh]
                    repeat_again = True
                    score += 1           
        self.Score += score**2
        return score**2
    
    def writeGameEvent(self,annot=''):
        """ записать игровое событие, пригодное для дальнейшего обучения
        модели игрока """
        eventS = pd.Series([self.figType,self.X,self.Y,self.Angle,self.Area,annot])
        eventD = pd.DataFrame((eventS,))
        eventD.columns = ['figType','figX','figY','figRotation','gameArea','annot']
        
        try:
            self.gameEventLog = pd.concat([self.gameEventLog, eventD],ignore_index=True)
        except Exception:
            self.gameEventLog = eventD
        

class CGameDisplay():
    """
    реализует вывод картинки тетриса на экран 
    """
    def __init__(self,tetris,Width=200,Height=400):
        self.screen = pg.display.set_mode((Width,Height))
        self.tetris = tetris
        self.Width = Width
        self.Height = Height
           
        
    def drawCell(self,i,j):
        """ нарисовать заполненную ячейку игрового поля """
        w = self.Width/(self.tetris.W-2)
        h = self.Height/(self.tetris.H-1)
        x0 = (i-1)*w
        y0 = (j)*h 
        if self.autoPlay:
            color1 = (0,255,0)
        else:
            color1 = (255,0,0)
            
        pg.draw.rect(self.screen,color1,[x0,y0,w,h])
        
    def redraw(self,tetr = None): 
        if tetr is None:
            self.redraw(self.tetris)
        else:
            self.screen.fill((0, 0, 0))
            for i in range(tetr.W):
                for j in range(tetr.H):
                    if tetr.getCell(i,j): 
                        self.drawCell(i,j)
            pg.display.update() 
            

class CUserGame(CGameDisplay):
    """ реализует управление игрой с клавиатуры """
    def __init__(self,tetris,game_ai):
        super().__init__(tetris)        
        self.clock = pg.time.Clock()
        self.game_ai = game_ai
        self.tetris.initFigure()
        self.autoPlay = False # при старте играет человек
    
    def user_loop(self):
        """ бесконечный цикл, обеспечивает вывод картинки и обработку событий управления """
        game_loop = True
        while game_loop:
            self.redraw()  
            self.clock.tick(3)
            
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    game_loop = False
 
                elif event.type == pg.KEYDOWN:
                    if event.key == pg.K_ESCAPE:
                        game_loop = False
                        
                    elif event.key == pg.K_LEFT:
                        self.tetris.moveFigureX(-1)
                        self.redraw()
                        
                    elif event.key == pg.K_RIGHT:
                        self.tetris.moveFigureX(1)
                        self.redraw()
                          
                    elif event.key == pg.K_UP:
                        self.tetris.rotateFigure(-1)
                        
                    elif event.key == pg.K_DOWN:
                        self.tetris.rotateFigure(1)
                        
                    elif event.key == pg.K_F9:
                        self.autoPlay = not self.autoPlay
                        
                    elif event.key == pg.K_SPACE:
                        while self.tetris.moveFigureDown(1):
                            self.redraw()
                            
            if self.autoPlay:
                x_shift,f_rotate,_ = self.game_ai.get_shift_rotate(self.tetris.figType,self.tetris.Area)
                self.tetris.setFigureShiftValue(x_shift)
                self.redraw()
                self.tetris.setFigureRotateValue(f_rotate)
                self.redraw()
            print(self.game_ai.get_shift_rotate(self.tetris.figType,self.tetris.Area))
            print('x:',self.tetris.X,' angl:',self.tetris.Angle%4)
            
            try:
                if self.tetris.testFigure(self.tetris.X,self.tetris.Y+1):
                    self.tetris.moveFigureDown(1)
            except CTetrisException: # фигура не может упасть вниз
                try:
                    self.tetris.writeGameEvent()
                    self.tetris.newFigure()
                except CTetrisException: # не можем расположить новую фигуру, игра закончилась
                    game_loop = False  
        #
        pg.quit()
             
#######################################################################
import pickle
import os

WORK_DIR = 'e:\\tetris_ai'

def get_Fmodel_fileName(figType,figRotate):
    fileName = 'F'+str(figType)+'R'+str(figRotate)+'.Fpickle'
    return os.path.join(WORK_DIR,fileName)

def get_Fmodel(figType,figRotate):
    """ возвращает модель для конкретной фигуры и поворота. Пробует загрузить с диска,
    при необходимости перестраивает, и сохраняет на диск. """
    
    fileName = get_Fmodel_fileName(figType,figRotate)
    try:
        with open(fileName, "rb") as f:
            F = pickle.load(f)
        return F # успешно загрузили, что нам нужно
    except Exception as e:
        print(e)
        
    print('rebuild model, please wait..')
    F0 = rebuild_Fmodel(figType,figRotate)
    # сохраняем на диск и загружаем с него
    with open(fileName, "wb") as f:
        pickle.dump(F0, f)
    with open(fileName, "rb") as f:
        F = pickle.load(f)
    
    return F

class Tetris_Fmodels():
    def __init__(self):
        self.Fmodels = [[None]*4]*7
        for figType in range(7):
            for figRotate in range(4):
                self.Fmodels[figType][figRotate] = get_Fmodel(figType,figRotate)
    
    def get_shift_rotate(self,figType,gameArea):
        """ выдать управляющие сигналы -сдвиг и поворот для заданной фигуры
        и конфигурации игрового поля """
        x1= gameArea.reshape(1,-1)
        #px.imshow(gameArea.reshape(12,-1).transpose()).show()
        best_shift = 0
        best_rot = 0
        best_pp = 0.
        
        #print(figType)
        for r in range(4):
            p1 = self.Fmodels[figType][r].predict(x1)
            pp = self.Fmodels[figType][r].predict_proba(x1)[0]
            pp_i = np.max(pp)
            if pp_i> best_pp:
                best_pp= pp_i
                best_shift = p1.item()
                best_rot = r
            #print('predicted shift',p1.item(),'proba',np.max(pp))
            #print('predict_proba',pp)   
        #print(' best_shift',best_shift,'best r',best_rot,' best_pp',best_pp)
        return best_shift,best_rot,best_pp
            
#######################################################################       
def main():
    random.seed()
    userGame = CUserGame(CTetris(),Tetris_Fmodels())
    userGame.user_loop()
    fileName = time.strftime("%Y_%m_%d_%H%M%S")+'.json'
    userGame.tetris.gameEventLog.to_json(fileName)
    return 
    
if __name__=='__main__':
    main()
