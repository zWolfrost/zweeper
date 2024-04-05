import random, json


class Minefield:
	def __init__(self, rows, cols, mines, seed=None):
		self.rows = rows
		self.cols = cols
		self.mines = mines
		self.seed = seed or generateSeed(int(self.rows*self.cols/5))
		self.field = []

		# Initialize the field
		for i in range(rows):
			self.field.append([])
			for j in range(cols):
				self.field[i].append({
					"mines": 0,
					"isMine": False,
					"isOpen": False,
					"isFlag": False
				})

		# Randomize the mines
		isMineList = [True]*mines + [False]*(rows*cols-mines)
		random.seed(self.seed)
		random.shuffle(isMineList)

		# Calculate the number of mines around each cell
		for i in range(rows):
			for j in range(cols):
				index = i*cols+j
				self.field[i][j]["row"] = i
				self.field[i][j]["col"] = j
				self.field[i][j]["pos"] = (i, j)
				self.field[i][j]["index"] = index

				if (isMineList[index]):
					self.field[i][j]["isMine"] = True
					for cell in self.getNearbyCells(i, j, True):
						cell["mines"] += 1

		# Create a flat list of cells
		self.flat = []
		for row in self.field:
			self.flat.extend(row)



	def initialize(self):
		self.__init__(self.rows, self.cols, self.mines)

	def restore(self):
		for row in self.field:
			for cell in row:
				cell["isOpen"] = False
				cell["isFlag"] = False

	def recountMines(self):
		for cell in self.flat:
			cell["mines"] = 0

		for i in range(self.rows):
			for j in range(self.cols):
				if (self.field[i][j]["isMine"]):
					for cell in self.getNearbyCells(i, j, True):
						cell["mines"] += 1



	def open(self, row, col, firstMoveCheck=True, nearbyOpening=False, nearbyFlagging=False, checkIsActive=False):
		index = self.positionToIndex(row, col)
		updatedCells = []

		if (firstMoveCheck):
			firstMoveCheck = self.isNew()

		def openEmptyZone(row, col):
			nonlocal updatedCells

			for cell in self.getEmptyZone(row, col):
				if (not cell["isOpen"]):
					cell["isOpen"] = True
					updatedCells.append(cell)


		if (not self.flat[index]["isOpen"]):
			if (checkIsActive): return True
			if (self.flat[index]["isMine"] and firstMoveCheck):
				self.moveMineToCorner(row, col)
			openEmptyZone(row, col)

		elif (self.flat[index]["mines"] != 0):
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
					if (self.flat[index]["mines"] == nearbyFlaggedCellsCount):
						if (checkIsActive): return True
						for unflaggedCell in nearbyUnflaggedCells:
							openEmptyZone(*unflaggedCell["pos"])
				if (nearbyFlagging):
					if (self.flat[index]["mines"] == nearbyClosedCellsCount):
						if (checkIsActive): return True
						for unflaggedCell in nearbyUnflaggedCells:
							unflaggedCell["isFlag"] = True
							updatedCells.append(unflaggedCell)

		if (checkIsActive):
			return False

		return updatedCells

	def isSolvableFrom(self, row, col, restore=True, firstMoveCheck=True):
		firstCell = self.field[row][col]

		if (firstCell["isMine"]):
			if (firstMoveCheck and self.isNew()):
				self.moveMineToCorner(row, col)
			else:
				return False

		if (firstCell["mines"] == 0):
			firstCell["isOpen"] = True
		else:
			return False


		importantIndexes = [cell["index"] for cell in self.flat if cell["isOpen"]]

		updates = True

		while (updates):
			updates = False

			allLinkedGroups = []

			def filterImportantIndexes(index):
				for nearbyCell in self.getNearbyCells(*self.flat[index]["pos"]):
					if (not nearbyCell["isOpen"] and not nearbyCell["isFlag"]):
						return True

				return False

			importantIndexes = list(filter(filterImportantIndexes, importantIndexes))

			# 1st try: open cells using nearby mines and flags
			for i in importantIndexes:
				if (self.flat[i]["mines"] == 0):
					for emptyCell in self.getEmptyZone(*self.flat[i]["pos"]):
						if (not emptyCell["isOpen"]):
							emptyCell["isOpen"] = True
							importantIndexes.append(emptyCell["index"])
							updates = True
				else:
					nearbyClosedCellsCount = 0
					nearbyFlaggedCellsCount = 0
					nearbyUnflaggedIndexes = [[], 0]

					for nearbyCell in self.getNearbyCells(*self.flat[i]["pos"]):
						if (not nearbyCell["isOpen"]):
							nearbyClosedCellsCount += 1
							if (nearbyCell["isFlag"]):
								nearbyFlaggedCellsCount += 1
							else:
								nearbyUnflaggedIndexes[0].append(nearbyCell["index"])

					if (len(nearbyUnflaggedIndexes[0]) > 0):
						# all nearby unflagged cells are safe -> open them
						if (self.flat[i]["mines"] == nearbyFlaggedCellsCount):
							for index in nearbyUnflaggedIndexes[0]:
								self.flat[index]["isOpen"] = True
								importantIndexes.append(index)
							updates = True

						# all nearby unflagged cells are mines -> flag them
						if (self.flat[i]["mines"] == nearbyClosedCellsCount):
							for index in nearbyUnflaggedIndexes[0]:
								self.flat[index]["isFlag"] = True
							updates = True

						# all nearby unflagged cells have SOME mines -> link them
						if (self.flat[i]["mines"] > nearbyFlaggedCellsCount):
							if (not nearbyUnflaggedIndexes in allLinkedGroups):
								nearbyUnflaggedIndexes[1] = self.flat[i]["mines"] - nearbyFlaggedCellsCount
								allLinkedGroups.append(nearbyUnflaggedIndexes)

			# 2nd try: link groups of cells
			if (not updates):
				shiftUpdates = True

				# adding & shifting linked groups
				while (shiftUpdates):
					shiftUpdates = False

					for i in importantIndexes:
						linkedGroupsSum = [[], 0]
						nearbyClosedIndexes = []
						nearbyFlaggedCellsCount = 0

						for nearbyCell in self.getNearbyCells(*self.flat[i]["pos"]):
							if (nearbyCell["isFlag"]):
								nearbyFlaggedCellsCount += 1
							elif (not nearbyCell["isOpen"]):
								nearbyClosedIndexes.append(nearbyCell["index"])

						for linkedGroup in allLinkedGroups:
							if (isSublist(nearbyClosedIndexes, linkedGroup[0]) and len(nearbyClosedIndexes) != len(linkedGroup[0])):
								shiftLinkedGroup = [
									subtractLists(nearbyClosedIndexes, linkedGroup[0]), # shifting
									self.flat[i]["mines"] - linkedGroup[1] - nearbyFlaggedCellsCount
								]

								if (len(shiftLinkedGroup[0]) > 0 and shiftLinkedGroup[1] > 0 and not shiftLinkedGroup in allLinkedGroups):
									allLinkedGroups.append(shiftLinkedGroup)
									shiftUpdates = True

								if (not hasDuplicates(linkedGroupsSum[0], linkedGroup[0])): # adding
									linkedGroupsSum[1] += linkedGroup[1]
									linkedGroupsSum[0].extend(linkedGroup[0])

						if (len(linkedGroupsSum[0]) > 0 and not linkedGroupsSum in allLinkedGroups):
							allLinkedGroups.append(linkedGroupsSum)
							shiftUpdates = True

				# open cells in linked groups
				for i in importantIndexes:
					nearbyIndexes = [cell["index"] for cell in self.getNearbyCells(*self.flat[i]["pos"])]

					for linkedGroup in allLinkedGroups:
						if (hasDuplicates(linkedGroup[0], nearbyIndexes)):
							nearbyFlaggedCellsCount = 0
							nearbyUnkownIndexes = []

							for index in nearbyIndexes:
								if (self.flat[index]["isFlag"]):
									nearbyFlaggedCellsCount += 1
								elif (not self.flat[index]["isOpen"] and not index in linkedGroup[0]):
									nearbyUnkownIndexes.append(index)

							if (len(nearbyUnkownIndexes) > 0):
								linkedGroupUncontainedCellsCount = len(subtractLists(linkedGroup[0], nearbyIndexes))

								# all unknown cells are mines -> flag them
								if (self.flat[i]["mines"] == nearbyFlaggedCellsCount + linkedGroup[1] + len(nearbyUnkownIndexes)):
									for index in nearbyUnkownIndexes:
										self.flat[index]["isFlag"] = True
									updates = True
								# all unknown cells are clear > open them
								elif (self.flat[i]["mines"] == nearbyFlaggedCellsCount + linkedGroup[1] - linkedGroupUncontainedCellsCount and not updates):
									for index in nearbyUnkownIndexes:
										if (not self.flat[index]["isFlag"]):
											self.flat[index]["isOpen"] = True
											importantIndexes.append(index)
											updates = True

			# 3rd try: open cells using remaining flags count
			if (not updates):
				flagsCount = 0
				minesCount = 0

				for cell in self.flat:
					if (cell["isFlag"]): flagsCount += 1
					if (cell["isMine"]): minesCount += 1

				if (flagsCount == minesCount):
					for cell in self.flat:
						if (not cell["isOpen"] and not cell["isFlag"]):
							cell["isOpen"] = True
							importantIndexes.append(cell["index"])
				else:
					for linkedGroup in allLinkedGroups:
						linkedGroup[0].sort()
					allLinkedGroups.sort()

					linkedGroupsSum = [[], 0]

					for linkedGroup in allLinkedGroups:
						if (not hasDuplicates(linkedGroupsSum[0], linkedGroup[0])):
							linkedGroupsSum[1] += linkedGroup[1]
							linkedGroupsSum[0].extend(linkedGroup[0])

					allLinkedGroups.append(linkedGroupsSum)

					for linkedGroup in allLinkedGroups:
						if linkedGroup[1] == minesCount - flagsCount:
							for cell in self.flat:
								if (not cell["isOpen"] and not cell["isFlag"] and not cell["index"] in linkedGroup[0]):
									cell["isOpen"] = True
									importantIndexes.append(cell["index"])
									updates = True


		if (restore):
			self.restore()

		isSolvable = len(importantIndexes) == 0

		return isSolvable

	def getHint(self):
		if (self.isNew()):
			return None

		def filterImportantIndexes(index):
			for nearbyCell in self.getNearbyCells(*self.flat[index]["pos"]):
				if (not nearbyCell["isOpen"] and not nearbyCell["isFlag"]):
					return True

			return False

		importantIndexes = [cell["index"] for cell in self.flat if cell["isOpen"]]
		importantIndexes = list(filter(filterImportantIndexes, importantIndexes))

		allLinkedGroups = []

		# 1st try: open cells using nearby mines and flags
		for i in importantIndexes:
			if (self.flat[i]["mines"] == 0):
				for emptyCell in self.getEmptyZone(*self.flat[i]["pos"]):
					if (not emptyCell["isOpen"]):
						return emptyCell
			else:
				nearbyClosedCellsCount = 0
				nearbyFlaggedCellsCount = 0
				nearbyUnflaggedIndexes = [[], 0]

				for nearbyCell in self.getNearbyCells(*self.flat[i]["pos"]):
					if (not nearbyCell["isOpen"]):
						nearbyClosedCellsCount += 1
						if (nearbyCell["isFlag"]):
							nearbyFlaggedCellsCount += 1
						else:
							nearbyUnflaggedIndexes[0].append(nearbyCell["index"])

				if (len(nearbyUnflaggedIndexes[0]) > 0):
					# all nearby unflagged cells are safe -> open them
					if (self.flat[i]["mines"] == nearbyFlaggedCellsCount):
						for index in nearbyUnflaggedIndexes[0]:
							return self.flat[index]

					# all nearby unflagged cells are mines -> flag them
					if (self.flat[i]["mines"] == nearbyClosedCellsCount):
						for index in nearbyUnflaggedIndexes[0]:
							return self.flat[index]

					# all nearby unflagged cells have SOME mines -> link them
					if (self.flat[i]["mines"] > nearbyFlaggedCellsCount):
						if (not nearbyUnflaggedIndexes in allLinkedGroups):
							nearbyUnflaggedIndexes[1] = self.flat[i]["mines"] - nearbyFlaggedCellsCount
							allLinkedGroups.append(nearbyUnflaggedIndexes)

		shiftUpdates = True

		# adding & shifting linked groups
		while (shiftUpdates):
			shiftUpdates = False

			for i in importantIndexes:
				linkedGroupsSum = [[], 0]
				nearbyClosedIndexes = []
				nearbyFlaggedCellsCount = 0

				for nearbyCell in self.getNearbyCells(*self.flat[i]["pos"]):
					if (nearbyCell["isFlag"]):
						nearbyFlaggedCellsCount += 1
					elif (not nearbyCell["isOpen"]):
						nearbyClosedIndexes.append(nearbyCell["index"])

				for linkedGroup in allLinkedGroups:
					if (isSublist(nearbyClosedIndexes, linkedGroup[0]) and len(nearbyClosedIndexes) != len(linkedGroup[0])):
						shiftLinkedGroup = [
							subtractLists(nearbyClosedIndexes, linkedGroup[0]), # shifting
							self.flat[i]["mines"] - linkedGroup[1] - nearbyFlaggedCellsCount
						]

						if (len(shiftLinkedGroup[0]) > 0 and shiftLinkedGroup[1] > 0 and not shiftLinkedGroup in allLinkedGroups):
							allLinkedGroups.append(shiftLinkedGroup)
							shiftUpdates = True

						if (not hasDuplicates(linkedGroupsSum[0], linkedGroup[0])): # adding
							linkedGroupsSum[1] += linkedGroup[1]
							linkedGroupsSum[0].extend(linkedGroup[0])

				if (len(linkedGroupsSum[0]) > 0 and not linkedGroupsSum in allLinkedGroups):
					allLinkedGroups.append(linkedGroupsSum)
					shiftUpdates = True

		# open cells in linked groups
		for i in importantIndexes:
			nearbyIndexes = [cell["index"] for cell in self.getNearbyCells(*self.flat[i]["pos"])]

			for linkedGroup in allLinkedGroups:
				if (hasDuplicates(linkedGroup[0], nearbyIndexes)):
					nearbyFlaggedCellsCount = 0
					nearbyUnkownIndexes = []

					for index in nearbyIndexes:
						if (self.flat[index]["isFlag"]):
							nearbyFlaggedCellsCount += 1
						elif (not self.flat[index]["isOpen"] and not index in linkedGroup[0]):
							nearbyUnkownIndexes.append(index)

					if (len(nearbyUnkownIndexes) > 0):
						linkedGroupUncontainedCellsCount = len(subtractLists(linkedGroup[0], nearbyIndexes))

						# all unknown cells are mines -> flag them
						if (self.flat[i]["mines"] == nearbyFlaggedCellsCount + linkedGroup[1] + len(nearbyUnkownIndexes)):
							for index in nearbyUnkownIndexes:
								return self.flat[index]
						# all unknown cells are clear > open them
						elif (self.flat[i]["mines"] == nearbyFlaggedCellsCount + linkedGroup[1] - linkedGroupUncontainedCellsCount):
							for index in nearbyUnkownIndexes:
								if (not self.flat[index]["isFlag"]):
									return self.flat[index]

		# 3rd try: open cells using remaining flags count
		flagsCount = 0
		minesCount = 0

		for cell in self.flat:
			if (cell["isFlag"]): flagsCount += 1
			if (cell["isMine"]): minesCount += 1

		if (flagsCount == minesCount):
			for cell in self.flat:
				if (not cell["isOpen"] and not cell["isFlag"]):
					return cell
		else:
			for linkedGroup in allLinkedGroups:
				linkedGroup[0].sort()
			allLinkedGroups.sort()

			linkedGroupsSum = [[], 0]

			for linkedGroup in allLinkedGroups:
				if (not hasDuplicates(linkedGroupsSum[0], linkedGroup[0])):
					linkedGroupsSum[1] += linkedGroup[1]
					linkedGroupsSum[0].extend(linkedGroup[0])

			allLinkedGroups.append(linkedGroupsSum)

			for linkedGroup in allLinkedGroups:
				if linkedGroup[1] == minesCount - flagsCount:
					for cell in self.flat:
						if (not cell["isOpen"] and not cell["isFlag"] and not cell["index"] in linkedGroup[0]):
							return cell

		return None

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

	def cell(self, row, col):
		return self.field[row][col]



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



	def visualize(self, unicode=False, color=False, highlight=False, uncover=False, log=True):
		EMPTY = "·" if unicode else "0"
		CLOSED = "■" if unicode else "?"
		FLAG = "►" if unicode else "F"
		MINE = "*" if unicode else "X"

		COLORS = {
			"END": "\x1b[0m",

			"ROW": {
				"blackbg": "\x1b[40m",
				"bright":  "\x1b[1m",
			},

			"COL": {
				"redfg":     "\x1b[31m",
				"greenfg":   "\x1b[32m",
				"yellowfg":  "\x1b[33m",
				"bluefg":    "\x1b[34m",
				"magentafg": "\x1b[35m",
				"cyanfg":    "\x1b[36m",
			},

			"HIGHLIGHT": "\x1b[7m"
		}
		ROW_COLORS = list(COLORS["ROW"].values())
		COL_COLORS = list(COLORS["COL"].values())

		def getCycleColor(colors, cycle):
			return colors[cycle % len(colors)]

		text = ""

		for row in self.field:
			if (color): text += getCycleColor(ROW_COLORS, row[0]["row"])

			for cell in row:
				char = ""

				if (not cell["isOpen"] and not uncover):
					if (cell["isFlag"]): char += FLAG
					else: char += CLOSED
				elif (cell["isMine"]): char += MINE
				elif (cell["mines"] == 0): char += EMPTY
				else: char += str(cell["mines"])

				if (color): text += getCycleColor(ROW_COLORS, row[0]["row"]) + getCycleColor(COL_COLORS, cell["col"])

				if (highlight and cell["pos"] in highlight):
					text += COLORS["HIGHLIGHT"] + char + COLORS["END"]
					if (color): text += getCycleColor(ROW_COLORS, row[0]["row"]) + getCycleColor(COL_COLORS, cell["col"])
				else:
					text += char

				if (cell["col"] != self.cols-1): text += " "

				if (color): text += COLORS["END"]
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



	def save(self):
		openCells = []
		flagCells = []

		for cell in self.flat:
			if (cell["isOpen"]): openCells.append(cell["index"])
			if (cell["isFlag"]): flagCells.append(cell["index"])

		return json.dumps({
			"rows": self.rows,
			"cols": self.cols,
			"mines": self.mines,
			"open": openCells,
			"flags": flagCells,
			"seed": self.seed,
		}, separators=(",", ":"))

	@staticmethod
	def load(data):
		load = json.loads(data)

		minefield = Minefield(load["rows"], load["cols"], load["mines"], load["seed"])

		for i in load["open"]:
			minefield.flat[i]["isOpen"] = True

		for i in load["flags"]:
			minefield.flat[i]["isFlag"] = True

		return minefield



def subtractLists(list1, list2):
	return [item for item in list1 if item not in list2]

def hasDuplicates(list1, list2):
	return any(item in list1 for item in list2)

def isSublist(list, sublist):
	return all(item in list for item in sublist)

def generateSeed(length):
	CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
	seed = ""
	for _ in range(length):
		seed += random.choice(CHARS)
	return seed