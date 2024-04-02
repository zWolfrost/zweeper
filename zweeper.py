#! ./env/bin/python

import sys, os
from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtWidgets import QMessageBox, QApplication
from PySide6.QtGui import QFontDatabase, QScreen

from zweeper_engine import Minefield

import timeit


WORKING_DIR = getattr(sys, '_MEIPASS', '.')



def centerWindow(window: QtWidgets.QWidget):
	geo = window.frameGeometry()
	geo.moveCenter(QScreen.availableGeometry(QApplication.primaryScreen()).center())
	window.move(geo.topLeft())

def minmax(num, min, max):
	return max if num > max else min if num < min else num


class zweeper(QtWidgets.QWidget):
	def __init__(self, rows, cols, mines):
		super().__init__()

		self.initUI(rows, cols, mines)
		self.show()

	def initUI(self, rows, cols, mines):
		self.minefield = Minefield(rows, cols, mines)

		cell_size = 1000 // max(rows, cols)
		cell_size = minmax(cell_size, 20, 50)
		self.setGeometry(0, 0, cell_size*cols, cell_size*rows)

		centerWindow(self)

		self.setWindowTitle(f"zweeper - {self.minefield.mines} flags left")

		self.layout = QtWidgets.QGridLayout()
		self.layout.setSpacing(0)
		self.layout.setContentsMargins(0, 0, 0, 0)

		for row in range(self.minefield.rows):
			for col in range(self.minefield.cols):
				cell = QtWidgets.QLabel()
				cell.setMinimumSize(20, 20)
				cell.setAlignment(QtCore.Qt.AlignCenter)

				cell.mousePressEvent = lambda event, row=row, col=col: self.cellPress(event, row, col)
				cell.mouseReleaseEvent = lambda event, row=row, col=col: self.cellRelease(event, row, col)

				cell.setMouseTracking(True)
				cell.mouseMoveEvent = lambda event, row=row, col=col: self.cellMouseMove(event, row, col)

				self.layout.addWidget(cell, row, col)

		self.setLayout(self.layout)

		print(WORKING_DIR)

		id = QFontDatabase.addApplicationFont(os.path.join(WORKING_DIR, "minesweeper.otf"))
		families = QFontDatabase.applicationFontFamilies(id)
		self.minesweeperFontID = families[0]

		self.lastMousePos = (-1, -1)

		self.updateUI()


	def updateUI(self, zone=None, pressed=None):
		scale = (min(self.width()/self.minefield.cols, self.height()/self.minefield.rows))/30

		if (pressed):
			pressed.setStyleSheet(
				"background-color: lightgray;"
				f"border-top: {str(4*scale)}px solid gray;"
				f"border-left: {str(4*scale)}px solid gray;"
				f"border-right: {str(2*scale)}px solid whitesmoke;"
				f"border-bottom: {str(2*scale)}px solid whitesmoke;"
			)
		elif (zone):
			for row, col in zone:
				cell = self.layout.itemAtPosition(row, col).widget()
				self.displayCell(cell, self.minefield.field[row][col], scale)
		else:
			for row in range(self.minefield.rows):
				for col in range(self.minefield.cols):
					cell = self.layout.itemAtPosition(row, col).widget()
					self.displayCell(cell, self.minefield.field[row][col], scale)

	def displayCell(self, cell: QtWidgets.QLabel, cellData: dict, scale=1):
		text = ""
		background_color = ""
		color = ""

		border_topleft = ""
		border_bottomright = ""

		if (cellData["isOpen"]):
			border_topleft = f"{str(0*scale)}px solid gray; padding-top: {str(4*scale)}px; padding-left: {str(4*scale)}px"
			border_bottomright = f"{str(2*scale)}px solid gray; padding-bottom: {str(2*scale)}px; padding-right: {str(2*scale)}px"

			if (cellData["isMine"]):
				text = "X"
				background_color = "crimson"
				color = "black"
			else:
				background_color = "lightgray"

				match cellData["mines"]:
					case 1:
						text = "1"
						color = "blue"
					case 2:
						text = "2"
						color = "green"
					case 3:
						text = "3"
						color = "red"
					case 4:
						text = "4"
						color = "darkblue"
					case 5:
						text = "5"
						color = "brown"
					case 6:
						text = "6"
						color = "darkcyan"
					case 7:
						text = "7"
						color = "black"
					case 8:
						text = "8"
						color = "gray"
		else:
			border_topleft = str(4*scale) + "px solid whitesmoke"
			border_bottomright = str(4*scale) + "px solid gray"

			if (cellData["isFlag"]):
				text = "F"
				background_color = "darkgray"
				color = "crimson"
			else:
				background_color = "lightgray"
				color = "black"

		cell.setText(text)
		cell.setStyleSheet(
			f"background-color: {background_color};"
			f"color: {color};"
			f"border-top: {border_topleft};"
			f"border-left: {border_topleft};"
			f"border-right: {border_bottomright};"
			f"border-bottom: {border_bottomright};"
		)

		cell.setFont(QtGui.QFont(self.minesweeperFontID, 11*scale, QtGui.QFont.Bold))

	def updateCursor(self, row, col):
		cell = self.layout.itemAtPosition(row, col).widget()
		cellData = self.minefield.field[row][col]

		if (self.minefield.open(*cellData["pos"], nearbyOpening=True, nearbyFlagging=True, checkIsActive=True)):
			cell.setCursor(QtCore.Qt.PointingHandCursor)
		else:
			cell.setCursor(QtCore.Qt.ArrowCursor)


	def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
		self.updateUI()
		pass

	def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
		if event.key() == QtCore.Qt.Key_R:
			self.minefield = Minefield(self.minefield.rows, self.minefield.cols, self.minefield.mines)
			self.updateUI()


	def cellPress(self, event: QtGui.QMouseEvent, row: int, col: int):
		cellData = self.minefield.field[row][col]

		if (event.button() == QtCore.Qt.LeftButton and not cellData["isOpen"] and not cellData["isFlag"]):
			self.updateUI(pressed=self.layout.itemAtPosition(row, col).widget())

	def cellRelease(self, event: QtGui.QMouseEvent, row: int, col: int):
		if (self.minefield.isOver()): return

		cellData = self.minefield.field[row][col]

		if (event.button() == QtCore.Qt.LeftButton and not cellData["isFlag"]):
			zone = self.minefield.open(*cellData["pos"], nearbyOpening=True, nearbyFlagging=True)
			self.updateUI(zone=[cell["pos"] for cell in zone])

			if (self.minefield.isOver()):
				self.onGameOver()
				self.minefield = Minefield(self.minefield.rows, self.minefield.cols, self.minefield.mines)
				self.updateUI()

		elif (event.button() == QtCore.Qt.RightButton):
			if (not cellData["isOpen"]):
				if (cellData["isFlag"]):
					cellData["isFlag"] = False
				elif (self.minefield.flags < self.minefield.mines):
					cellData["isFlag"] = True

				self.updateUI(zone=[cellData["pos"]])
				self.setWindowTitle(f"zweeper - {self.minefield.mines - self.minefield.flags} flags left")

		self.updateCursor(row, col)

	def cellMouseMove(self, event: QtGui.QMouseEvent, row: int, col: int):
		if (self.lastMousePos != (row, col)):
			self.lastMousePos = (row, col)

			self.updateCursor(row, col)


	def onGameOver(self):
		msg = QMessageBox()

		msg.setWindowTitle("Game Over")

		if (self.minefield.isCleared()):
			msg.setText("You win!")
		else:
			msg.setText("You lose!")

		msg.move(self.pos() + QtCore.QPoint(self.width()//2 - 50, self.height()//2))

		msg.exec()



class zweeper_size_prompt(QtWidgets.QWidget):
	def __init__(self):
		super().__init__()

		self.initUI()
		self.show()

	def initUI(self):
		self.setFixedSize(300, 125)
		self.setWindowTitle("zweeper")

		centerWindow(self)

		self.layout = QtWidgets.QVBoxLayout()
		self.layout.setSpacing(2)
		self.layout.setContentsMargins(0, 0, 0, 0)

		self.difficultyLabel = QtWidgets.QLabel("")
		self.difficultyLabel.setAlignment(QtCore.Qt.AlignCenter)
		self.layout.addWidget(self.difficultyLabel)

		self.infoLabel = QtWidgets.QLabel("")
		self.infoLabel.setAlignment(QtCore.Qt.AlignCenter)
		self.layout.addWidget(self.infoLabel)

		self.difficulty = QtWidgets.QSlider(QtCore.Qt.Horizontal)
		self.difficulty.setMinimum(1)
		self.difficulty.setMaximum(3)
		self.difficulty.setTickInterval(1)
		self.difficulty.setValue(2)
		self.difficulty.setTickPosition(QtWidgets.QSlider.TicksBelow)
		self.difficulty.valueChanged.connect(self.difficultyChanged)
		self.layout.addWidget(self.difficulty)

		self.button = QtWidgets.QPushButton("Start")
		self.button.clicked.connect(self.startGame)
		self.layout.addWidget(self.button)

		self.difficultyChanged()

		self.setLayout(self.layout)

	def difficultyChanged(self):
		match self.difficulty.value():
			case 1:
				self.rows, self.cols, self.mines = 8, 8, 10
				self.difficultyLabel.setText("Difficulty: Easy")
			case 2:
				self.rows, self.cols, self.mines = 16, 16, 40
				self.difficultyLabel.setText("Difficulty: Normal")
			case 3:
				self.rows, self.cols, self.mines = 16, 30, 99
				self.difficultyLabel.setText("Difficulty: Hard")

		self.infoLabel.setText(f"Rows: {self.rows}, Cols: {self.cols}, Mines: {self.mines}")

	def startGame(self):
		self.game = zweeper(self.rows, self.cols, self.mines)
		self.close()



if __name__ == "__main__":
	app = QtWidgets.QApplication(sys.argv)
	ex = zweeper_size_prompt()
	sys.exit(app.exec())