#! ./venv/bin/python

import sys, os
from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtWidgets import QMessageBox, QApplication
from PySide6.QtGui import QFontDatabase, QScreen

from zweeper_engine import Minefield



WORKING_DIR = getattr(sys, '_MEIPASS', '.')

options = {
	"rows": 16,
	"cols": 16,
	"mines": 40,
	"autoMode": True,
	"noGuessMode": True,

	"seed": None,

	"windowToScreenSizeRatio": 0.8,
	"cellSizeInterval": (20, 40),
}



def centerWindow(window: QtWidgets.QWidget):
	geo = window.frameGeometry()
	geo.moveCenter(QScreen.availableGeometry(QApplication.primaryScreen()).center())
	window.move(geo.topLeft())

def minmax(num, min, max):
	return max if num > max else min if num < min else num

def showMessageBox(title, text):
	msg = QMessageBox()
	msg.setWindowTitle(title)
	msg.setText(text)
	msg.exec()



class zweeper(QtWidgets.QWidget):
	def __init__(self):
		super().__init__()

		self.initUI()
		self.show()

	def initUI(self):
		self.minefield = Minefield(options["rows"], options["cols"], options["mines"], seed=options["seed"])

		max_window_width  = QScreen.availableGeometry(QApplication.primaryScreen()).width()  * options["windowToScreenSizeRatio"]
		max_window_height = QScreen.availableGeometry(QApplication.primaryScreen()).height() * options["windowToScreenSizeRatio"]

		self.cell_size = int(min(max_window_width/self.minefield.cols, max_window_height/self.minefield.rows))
		self.cell_size = minmax(self.cell_size, *options["cellSizeInterval"])

		self.setFixedSize(self.cell_size*self.minefield.cols, self.cell_size*self.minefield.rows)
		self.updateTitle()

		self.layout = QtWidgets.QGridLayout()
		self.layout.setSpacing(0)
		self.layout.setContentsMargins(0, 0, 0, 0)

		centerWindow(self)

		for row in range(self.minefield.rows):
			for col in range(self.minefield.cols):
				cell = QtWidgets.QLabel()
				cell.setMinimumSize(20, 20)
				cell.setAlignment(QtCore.Qt.AlignCenter)
				cell.setFixedSize(self.cell_size, self.cell_size)

				cell.mousePressEvent = lambda event, row=row, col=col: self.cellPress(event, row, col)
				cell.mouseReleaseEvent = lambda event, row=row, col=col: self.cellRelease(event, row, col)

				cell.setMouseTracking(True)
				cell.mouseMoveEvent = lambda event, row=row, col=col: self.cellMouseMove(event, row, col)

				self.layout.addWidget(cell, row, col)

		self.setLayout(self.layout)

		id = QFontDatabase.addApplicationFont(os.path.join(WORKING_DIR, "minesweeper.otf"))
		families = QFontDatabase.applicationFontFamilies(id)
		self.minesweeperFontID = families[0]

		self.lastMousePos = (-1, -1)

		self.updateUI(True)



	def updateUI(self, all=False, zone=[], pressed=[], highlight=[]):
		scale = (min(self.width()/self.minefield.cols, self.height()/self.minefield.rows))/30
		game_lost = self.minefield.isLost()

		if (all):
			zone = [(row, col) for row in range(self.minefield.rows) for col in range(self.minefield.cols)]
		elif (hasattr(self, "highlighted_cells") and self.highlighted_cells):
			zone.extend(self.highlighted_cells)
			self.highlighted_cells = []

		for row, col in zone:
			cell = self.layout.itemAtPosition(row, col).widget()

			self.displayCell(
				cell,
				self.minefield.field[row][col],
				highlight=((row, col) in highlight),
				scale=scale,
				game_lost=game_lost
			)

		if (highlight):
			self.highlighted_cells = highlight

		if (pressed):
			for row, col in pressed:
				cell = self.layout.itemAtPosition(row, col).widget()
				cell.setStyleSheet(
					"background-color: lightgray;"
					f"border-top: {str(4*scale)}px solid gray;"
					f"border-left: {str(4*scale)}px solid gray;"
					f"border-right: {str(2*scale)}px solid whitesmoke;"
					f"border-bottom: {str(2*scale)}px solid whitesmoke;"
				)



	def displayCell(self, cell: QtWidgets.QLabel, cell_data: dict, highlight=False, scale=1, game_lost=False):
		text = ""
		background_color = ""
		color = ""

		border_topleft = ""
		border_bottomright = ""

		font_size = 12

		if (cell_data["isOpen"]):
			border_topleft = f"{str(0*scale)}px solid gray; padding-top: {str(4*scale)}px; padding-left: {str(4*scale)}px"
			border_bottomright = f"{str(2*scale)}px solid gray; padding-bottom: {str(2*scale)}px; padding-right: {str(2*scale)}px"
			if (cell_data["isMine"]):
				text = "*"
				background_color = "red"
				color = "black"
			else:
				font_size = 14
				background_color = "lightgray"

				match cell_data["mines"]:
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

			if (cell_data["isFlag"]):
				text = "`"
				background_color = "lightgray"
				color = "crimson"
			elif (cell_data["isMine"] and game_lost):
				text = "*"
				background_color = "lightgray"
				color = "black"
			else:
				background_color = "lightgray"
				color = "black"

		if (highlight):
			background_color = "palegoldenrod"

		cell.setText(text)
		cell.setStyleSheet(
			f"background-color: {background_color};"
			f"color: {color};"
			f"border-top: {border_topleft};"
			f"border-left: {border_topleft};"
			f"border-right: {border_bottomright};"
			f"border-bottom: {border_bottomright};"
		)

		cell.setFont(QtGui.QFont(self.minesweeperFontID, font_size*scale))

	def updateCursor(self, row, col):
		cell = self.layout.itemAtPosition(row, col).widget()
		cellData = self.minefield.field[row][col]

		if (self.minefield.open(*cellData["pos"], nearbyOpening=options["autoMode"], nearbyFlagging=options["autoMode"], checkIsActive=True)):
			cell.setCursor(QtCore.Qt.PointingHandCursor)
		else:
			cell.setCursor(QtCore.Qt.ArrowCursor)

	def updateTitle(self):
		self.setWindowTitle(f"zweeper - {self.minefield.mines - self.minefield.flags} flags left - press K for keybinds")



	def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
		self.updateUI(True)

	def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
		match event.key():
			case QtCore.Qt.Key_R:
				self.minefield.initialize()
				#while (self.minefield.field[0][0]["mines"] != 0 or self.minefield.isSolvableFrom(0, 0, restore=False)):
				#	self.minefield.initialize()
				self.updateUI(True)
				self.updateTitle()
				#print(self.minefield.seed)

			case QtCore.Qt.Key_H:
				hint = self.minefield.getHint()

				if (hint):
					hint_square = [cell["pos"] for cell in self.minefield.getNearbyCells(*hint["pos"], True)]
					self.updateUI(zone=hint_square, highlight=hint_square)

			case QtCore.Qt.Key_S:
				try:
					settings = QtCore.QSettings("zweeper", "zweeper")
					settings.setValue("game", self.minefield.save())

					showMessageBox("Game Saved", "Game saved successfully")
				except:
					showMessageBox("Error", "Failed to save game")

			case QtCore.Qt.Key_L:
				load = QtCore.QSettings("zweeper", "zweeper").value("game")
				if (load):
					try:
						self.minefield = Minefield.load(load)
						self.updateUI(True)
						self.updateTitle()

						showMessageBox("Game Loaded", "Game loaded successfully")
					except:
						showMessageBox("Error", "Failed to load game")
				else:
					showMessageBox("Error", "No saved game found")

			case QtCore.Qt.Key_I:
				msg = QMessageBox()

				msg.setWindowTitle("Debug Info")
				msg.setText(f"Seed: {self.minefield.seed}{self.minefield.seed}{self.minefield.seed}")

				msg.setFixedWidth(200)
				msg.exec()

			case QtCore.Qt.Key_K:
				msg = QMessageBox()

				msg.setWindowTitle("Keybinds")
				msg.setText(
					"Left click: Open cell       \n"
					"Right click: Flag cell\n"
					"R: Restart game\n"
					"H: Show hint\n"
					"S: Save game\n"
					"L: Load game\n"
					"I: Show Debug Info\n"
					"K: Show keybinds\n"
				)
				msg.exec()



	def cellPress(self, event: QtGui.QMouseEvent, row: int, col: int):
		cellData = self.minefield.field[row][col]

		if (event.button() == QtCore.Qt.LeftButton and not cellData["isOpen"] and not cellData["isFlag"]):
			self.updateUI(pressed=[(row, col)])

	def cellRelease(self, event: QtGui.QMouseEvent, row: int, col: int):
		cellData = self.minefield.field[row][col]

		if (event.button() == QtCore.Qt.LeftButton and not cellData["isFlag"]):
			if (self.minefield.isNew() and options["noGuessMode"]):
				while (not self.minefield.isSolvableFrom(*cellData["pos"])):
					self.minefield.initialize()
				self.updateUI(True)

			zone = self.minefield.open(*cellData["pos"], nearbyOpening=options["autoMode"], nearbyFlagging=options["autoMode"])
			self.updateUI(zone=[cell["pos"] for cell in zone])

			if (self.minefield.isOver()):
				self.updateUI(zone=[cell["pos"] for cell in self.minefield.flat if cell["isMine"] and not cell["isFlag"]])
				self.onGameOver()
				self.minefield.initialize()
				self.updateUI(True)
				self.updateTitle()

		elif (event.button() == QtCore.Qt.RightButton):
			if (not cellData["isOpen"]):
				if (cellData["isFlag"]):
					cellData["isFlag"] = False
				elif (self.minefield.flags < self.minefield.mines):
					cellData["isFlag"] = True

				self.updateUI(zone=[cellData["pos"]])

		self.updateTitle()
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

		msg.exec()



class zweeper_size_prompt(QtWidgets.QWidget):
	def __init__(self):
		super().__init__()

		self.initUI()
		self.show()

	def initUI(self):
		self.setFixedSize(250, 250)
		self.setWindowTitle("zweeper")

		self.layout = QtWidgets.QVBoxLayout()
		self.layout.setSpacing(2)
		self.setStyleSheet("font-size: 15px;")

		centerWindow(self)

		self.difficultyLabel = QtWidgets.QLabel("")
		self.layout.addWidget(self.difficultyLabel, 0, QtCore.Qt.AlignCenter)

		self.difficulty = QtWidgets.QSlider(QtCore.Qt.Horizontal)
		self.difficulty.setMinimum(1)
		self.difficulty.setMaximum(5)
		self.difficulty.setValue(2)
		self.difficulty.valueChanged.connect(self.difficultyChanged)
		self.layout.addWidget(self.difficulty)

		self.rowsLine = QtWidgets.QHBoxLayout()
		self.layout.addLayout(self.rowsLine)
		self.rowsLabel = QtWidgets.QLabel("Rows:")
		self.rowsLine.addWidget(self.rowsLabel)
		self.rowsInput = QtWidgets.QSpinBox()
		self.rowsInput.setRange(1, 50)
		self.rowsInput.valueChanged.connect(lambda value: options.update({"rows": value}))
		self.rowsInput.setFixedWidth(100)
		self.rowsLine.addWidget(self.rowsInput)

		self.colsLine = QtWidgets.QHBoxLayout()
		self.layout.addLayout(self.colsLine)
		self.colsLabel = QtWidgets.QLabel("Columns:")
		self.colsLine.addWidget(self.colsLabel)
		self.colsInput = QtWidgets.QSpinBox()
		self.colsInput.setRange(1, 50)
		self.colsInput.valueChanged.connect(lambda value: options.update({"cols": value}))
		self.colsInput.setFixedWidth(100)
		self.colsLine.addWidget(self.colsInput)

		self.minesLine = QtWidgets.QHBoxLayout()
		self.layout.addLayout(self.minesLine)
		self.minesLabel = QtWidgets.QLabel("Mines:")
		self.minesLine.addWidget(self.minesLabel)
		self.minesInput = QtWidgets.QSpinBox()
		self.minesInput.setRange(0, 2000)
		self.minesInput.valueChanged.connect(lambda value: options.update({"mines": value}))
		self.minesInput.setFixedWidth(100)
		self.minesLine.addWidget(self.minesInput)

		self.autoModeCheckbox = QtWidgets.QCheckBox("Auto mode")
		self.autoModeCheckbox.setChecked(True)
		self.autoModeCheckbox.stateChanged.connect(lambda state: options.update({"autoMode": state == 2}))
		self.layout.addWidget(self.autoModeCheckbox)

		self.noGuessModeCheckbox = QtWidgets.QCheckBox("No guess mode")
		self.noGuessModeCheckbox.setChecked(True)
		self.noGuessModeCheckbox.stateChanged.connect(lambda state: options.update({"noGuessMode": state == 2}))
		self.layout.addWidget(self.noGuessModeCheckbox)

		self.button = QtWidgets.QPushButton("Start")
		self.button.clicked.connect(self.startGame)
		self.layout.addWidget(self.button)

		self.difficultyChanged()

		self.setLayout(self.layout)

	def difficultyChanged(self):
		self.rowsInput.setEnabled(False)
		self.colsInput.setEnabled(False)
		self.minesInput.setEnabled(False)

		match self.difficulty.value():
			case 1:
				options["rows"], options["cols"], options["mines"] = 9, 9, 10
				self.difficultyLabel.setText("Difficulty: Easy")
			case 2:
				options["rows"], options["cols"], options["mines"] = 16, 16, 40
				self.difficultyLabel.setText("Difficulty: Normal")
			case 3:
				options["rows"], options["cols"], options["mines"] = 16, 30, 99
				self.difficultyLabel.setText("Difficulty: Hard")
			case 4:
				options["rows"], options["cols"], options["mines"] = 30, 30, 200
				self.difficultyLabel.setText("Difficulty: Extreme")
			case 5:
				options["rows"], options["cols"], options["mines"] = 16, 16, 40
				self.difficultyLabel.setText("Difficulty: Custom")
				self.rowsInput.setEnabled(True)
				self.colsInput.setEnabled(True)
				self.minesInput.setEnabled(True)

		self.rowsInput.setValue(options["rows"])
		self.colsInput.setValue(options["cols"])
		self.minesInput.setValue(options["mines"])

	def startGame(self):
		options["mines"] = min(options["mines"], options["rows"]*options["cols"]-1)
		self.game = zweeper()
		self.close()



if __name__ == "__main__":
	app = QtWidgets.QApplication(sys.argv)
	ex = zweeper_size_prompt()
	sys.exit(app.exec())