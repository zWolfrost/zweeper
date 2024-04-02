import random

class Minefield:
	def __init__(self, rows, cols, mines):
		self.rows = rows
		self.cols = cols
		self.mines = mines

		# Initialize the field
		self.field = [[{
			"mines": 0,
			"isMine": i*cols+j < mines,
			"isOpen": False,
			"isFlag": False,
			"row": i,
			"col": j,
			"pos": (i, j)
		} for j in range(cols)] for i in range(rows)]

		# Fisher-Yates shuffle algorithm
		for i in range(rows*cols-1, 0, -1):
			j = random.randint(0, i)
			row1, col1 = self.indexToPosition(i)
			row2, col2 = self.indexToPosition(j)
			self.field[row1][col1], self.field[row2][col2] = self.field[row2][col2], self.field[row1][col1]

		# Calculate the number of mines around each cell
		for i in range(rows):
			for j in range(cols):
				self.field[i][j]["row"] = i
				self.field[i][j]["col"] = j
				self.field[i][j]["pos"] = (i, j)

				if (self.field[i][j]["isMine"]):
					for cell in self.getNearbyCells(i, j, True):
						cell["mines"] += 1



	def concatenate(self):
		flat = []
		for row in self.field:
			flat.extend(row)
		return flat



	def open(self, row, col, firstMoveCheck=True, nearbyOpening=False, nearbyFlagging=False, checkIsActive=False):
		flat = self.concatenate()
		index = self.positionToIndex(row, col)
		updatedCells = []

		if (firstMoveCheck):
			firstMoveCheck = self.isNew()

		def openEmptyZone(row, col):
			nonlocal updatedCells

			for cell in self.getEmptyZone(row, col):
				if (not cell["isOpen"]):
					if (not checkIsActive):
						cell["isOpen"] = True
					updatedCells.append(cell)


		if (not flat[index]["isOpen"]):
			if (flat[index]["isMine"] and firstMoveCheck):
				if (checkIsActive): return True
				self.moveMineToCorner(row, col)
			openEmptyZone(row, col)

		elif (flat[index]["mines"] != 0):
			if (nearbyOpening or nearbyFlagging):
				nearbyClosedCellsCount = 0
				nearbyFlaggedCellsCount = 0
				nearbyUnflaggedCells = []

				for cell in self.getNearbyCells(row, col):
					if (not cell["isOpen"]):
						nearbyClosedCellsCount += 1
						if (cell["isFlag"]):
							nearbyFlaggedCellsCount += 1
						else:
							nearbyUnflaggedCells.append(cell)

				if (nearbyOpening):
					if (flat[index]["mines"] == nearbyFlaggedCellsCount):
						for unflaggedCell in nearbyUnflaggedCells:
							openEmptyZone(*unflaggedCell["pos"])
				if (nearbyFlagging):
					if (flat[index]["mines"] == nearbyClosedCellsCount):
						for unflaggedCell in nearbyUnflaggedCells:
							if (checkIsActive): return True
							unflaggedCell["isFlag"] = True
							updatedCells.append(unflaggedCell)

		if (checkIsActive):
			return len(updatedCells) > 0

		return updatedCells

	def moveMineToCorner(self, row, col):
		if (self.field[row][col]["isMine"]):
			for i in range(self.rows):
				for j in range(self.cols):
					if (not self.field[i][j]["isMine"]):
						self.field[i][j]["isMine"] = True
						self.field[row][col]["isMine"] = False

						for cell in self.getNearbyCells(i, j, True):
							cell["mines"] += 1

						for cell in self.getNearbyCells(row, col, True):
							cell["mines"] -= 1

						return self.field[i][j]



	def indexToPosition(self, index):
		return index//self.cols, index%self.cols

	def positionToIndex(self, row, col):
		return row*self.cols+col



	def getNearbyCells(self, row, col, includeSelf=False):
		nearbyCells = []

		isNotFirstCol = col > 0
		isNotLastCol = col < self.cols-1

		if (row > 0):
			if (isNotFirstCol): nearbyCells.append(self.field[row-1][col-1])
			nearbyCells.append(self.field[row-1][col])
			if (isNotLastCol): nearbyCells.append(self.field[row-1][col+1])

		if (isNotFirstCol): nearbyCells.append(self.field[row][col-1])
		if (includeSelf): nearbyCells.append(self.field[row][col])
		if (isNotLastCol): nearbyCells.append(self.field[row][col+1])

		if (row < self.rows-1):
			if (isNotFirstCol): nearbyCells.append(self.field[row+1][col-1])
			nearbyCells.append(self.field[row+1][col])
			if (isNotLastCol): nearbyCells.append(self.field[row+1][col+1])

		return nearbyCells

	def getEmptyZone(self, row, col, includeFlagged=False):
		visited = [(row, col)]

		for cell in visited:
			if (self.field[cell[0]][cell[1]]["mines"] == 0):
				for nearbyCell in self.getNearbyCells(*cell):
					if (nearbyCell["pos"] not in visited):
						if (includeFlagged or not nearbyCell["isFlag"]):
							visited.append((nearbyCell["row"], nearbyCell["col"]))

		return [self.field[cell[0]][cell[1]] for cell in visited]



	def isNew(self):
		for row in self.field:
			for cell in row:
				if (cell["isOpen"]):
					return False
		return True

	def isPlaying(self):
		foundOpen = False
		foundClosedEmpty = False

		for row in self.field:
			for cell in row:
				if (cell["isOpen"]):
					if (cell["isMine"]): return False
					foundOpen = True
				elif (not cell["isOpen"] and not cell["isMine"]): foundClosedEmpty = True

		return foundOpen and foundClosedEmpty

	def isOver(self):
		foundClosedEmpty = False

		for row in self.field:
			for cell in row:
				if (not cell["isOpen"] and not cell["isMine"]): foundClosedEmpty = True
				elif (cell["isOpen"] and cell["isMine"]): return True

		return not foundClosedEmpty

	def isCleared(self):
		for row in self.field:
			for cell in row:
				if (cell["isOpen"] == cell["isMine"]): return False
		return True

	def isLost(self):
		for row in self.field:
			for cell in row:
				if (cell["isOpen"] and cell["isMine"]): return True
		return False



	def visualize(self, uncover=False, log=True):
		EMPTY = "0"
		CLOSED = "?"
		FLAG = "F"
		MINE = "X"

		text = ""

		for i in range(self.rows):
			for j in range(self.cols):
				char = ""
				cell = self.field[i][j]

				if (not cell["isOpen"] and not uncover):
					if (cell["isFlag"]): char += FLAG
					else: char += CLOSED
				elif (cell["isMine"]): char += MINE
				elif (cell["mines"] == 0): char += EMPTY
				else: char += str(cell["mines"])

				text += char

				if (j < self.cols-1): text += " "
			text += "\n"

		if (log): print(text)
		return text



	@property
	def flags(self):
		flagCount = 0
		for row in self.field:
			for cell in row:
				if (cell["isFlag"]): flagCount += 1
		return flagCount