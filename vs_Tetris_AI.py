import numpy as np
import random
import sys
import pygame

class CTetrisException(Exception):
    """
    базовое прерывание от логики тетриса
    """
    pass

class CTetrisExceptionMoveX(CTetrisException):
    """ 
    невозможно двинуть фигуру вбок
    """
    def __init__(self,X):
        #super().__init__(self)
        self.X = X

class CTetrisExceptionMoveDown(CTetrisException):
    """
    невозможно двинуть фигуру вниз
    """
    pass 

class CTetrisExceptionScoreChange(CTetrisException):
    """
    cгорели строки, изменился счет
    """
    def __init__(self,scoreChange):
        #super().__init__(self)
        self.scoreChange = scoreChange


class CTetrisExceptionGameOver(CTetrisException):
    """
    игра закончилась, невозможно расположить новую фигуру
    """
    pass

class CTetris():
    """
    реализует логику игры тетрис - движение фигур, сжигание линий, проверку логики
    """
    def __init__(self,W=12,H=21):
        self.W = W
        self.H = H
        self.Area = np.zeros((W,H),dtype=int) # игровое поле
        self.Area[0,:]=1
        self.Area[W-1,:]=1
        self.Area[:,H-1]=1
        self.Figure = np.zeros((4,4),dtype=int) # размер фигуры 4х4
        self.X = 5
        self.Y = 5
        self.Score = 0
        self.initFigure()


    def rotateFigure(self,rightAngle=True):
        rot = np.zeros((4,4),dtype=int)
        for a in range(4):
            for b in range(4):
                if rightAngle:
                    rot[a,b] = self.Figure[3-b,a]
                else:
                    rot[a,b] = self.Figure[b,3-a]
        try:
            self.testFigure(self.X,self.Y,rot)
        except CTetrisException:
            pass
        else:
            self.Figure[:,:] = rot[:,:]


    def initFigure(self, figType = None):
        """ инициализировать новую фигуру """
        if figType is None:
            figType = random.randint(0,6)

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

        elif figType == 5:
            self.Figure[1:3,0] = 1
            self.Figure[2:4,1] = 1

        elif figType == 6:
            self.Figure[1:3,1] = 1
            self.Figure[2:4,0] = 1


    def getCell(self,i,j):
        """ проверить заполненность ячейки игрового поля """
        a = i-self.X
        b = j-self.Y
        if a>=0 and b>=0 and a<4 and b<4 and self.Figure[a,b]!=0:
            return True
        
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
        

    def frostFigure(self,X,Y):
        """ 'заморозить' фигуру на игровом поле """
        for a in range(4):
            for b in range(4):
                i = a+X
                j = b+Y
                if i<self.W and j<self.H:
                    self.Area[i,j] += self.Figure[a,b]
        

    def removeLines(self):
        """ удалить полные линии игрового поля, сдвинуть игровое поле вниз"""
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


class CUserGame():
    """
    реализует интерфейс пользователя к игре тетрис - 1.вывод картинки на экран 2.  события нажатия кнопок 
    """
    def __init__(self,tetris,Width=200,Height=400):
        self.screen = pygame.display.set_mode((Width,Height))
        self.tetris = tetris
        self.Width = Width
        self.Height = Height
        self.clock = pygame.time.Clock()   
        self.game_over = False
        self.tetris.initFigure(0)
        
    def drawCell(self,i,j):
        """ нарисовать заполненную ячейку игрового поля """
        w = self.Width/(self.tetris.W-2)
        h = self.Height/(self.tetris.H-1)
        x0 = (i-1)*w
        y0 = (j)*h 
        pygame.draw.rect(self.screen,(255,0,0),[x0,y0,w,h])
        
    def redraw(self): 
        self.screen.fill((0, 0, 0))
        for i in range(self.tetris.W):
            for j in range(self.tetris.H):
                if self.tetris.getCell(i,j): 
                    self.drawCell(i,j)

        pygame.display.update()

    def main_loop(self):
        """ бесконечный цикл, обеспечивает вывод картинки и обработку событий управления"""
        while not self.game_over:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        sys.exit(0)

                    elif event.key == pygame.K_LEFT:
                        try:
                            self.tetris.testFigure(self.tetris.X-1,self.tetris.Y)
                        except CTetrisException:
                            pass
                        else:
                            self.tetris.X -= 1

                    elif event.key == pygame.K_RIGHT:
                        try:
                            self.tetris.testFigure(self.tetris.X+1,self.tetris.Y)
                        except CTetrisException:
                            pass
                        else:
                            self.tetris.X += 1
                    
                    elif event.key == pygame.K_UP:
                        self.tetris.rotateFigure(False)
                        
                    elif event.key == pygame.K_DOWN:
                        self.tetris.rotateFigure(True)
            try:
                self.tetris.testFigure(self.tetris.X,self.tetris.Y+1)
            except CTetrisException: # фигура не может упасть вниз
                self.tetris.frostFigure(self.tetris.X,self.tetris.Y) # замораживаем ее на игровом поле
                self.tetris.removeLines()
                try:
                    self.tetris.initFigure()
                    self.tetris.testFigure(self.tetris.X,self.tetris.Y)
                except CTetrisException:
                    game_over = True
            else:
                self.tetris.Y += 1
            finally:
                self.redraw()

            self.clock.tick(6)


def main():
    random.seed()
    userGame = CUserGame(CTetris())
    userGame.main_loop()


if __name__=='__main__':
    main()


