from zweeper_engine import Minefield
import timeit, random


#m = Minefield(16, 16, 40)

#win = 0
#stuck = 0
#single = 0

#for i in range(1000):
#	m.randomize()
#	m.isSolvableFrom(2, 3, restore=False)
#	if (m.isCleared()):
#		win += 1
#	elif (m.field[2][3]["mines"] == 0):
#		stuck += 1
#		#m.visualize(color=True, unicode=True)
#	else:
#		single += 1

#print(f"win: {win}, stuck: {stuck}, single: {single}")
#print(f"actual games: {win + stuck}, winrate: {win/(win+stuck)*100:.2f}%")


#m = Minefield(16, 16, 40)
#m.isSolvableFrom(2, 3, restore=False)
#m.visualize()




#m = Minefield(40, 40, 320)
#
#def findSolvableFrom(row, col):
#	it = 0
#	while not m.isSolvableFrom(row, col):
#		it += 1
#		m.randomize()
#	print(it)
#
#print(timeit.timeit(lambda: findSolvableFrom(2, 3), number=1))


random.seed(57457475)

def results(rows=11, cols=11, mines=24, start=(5, 5), tests=10000):
	isPlaying = 0
	goodStarts = 0
	isPlayingGoodStarts = 0
	isOver = 0
	isCleared = 0
	isLost = 0
	firstCellMine = 0

	for _ in range(tests):
		test = Minefield(rows, cols, mines, seed=random.randint(0, 1000000))
		test.isSolvableFrom(*start, False)

		if (test.cell(*start)["mines"] == 0):
			goodStarts += 1

			if (test.isPlaying()):
				isPlayingGoodStarts += 1

		if (test.isPlaying()): isPlaying += 1
		if (test.isOver()): isOver += 1
		if (test.isCleared()): isCleared += 1
		if (test.isLost()):
			isLost += 1
			if (test.cell(*start)["isMine"]): firstCellMine += 1

	print(f"""
		Total tests: {tests}
		goodStarts: {goodStarts}
		isPlaying (gs): {isPlayingGoodStarts}
		isCleared (gs): {isCleared}
		isLost: {isLost-firstCellMine}

		% cleared: {isCleared*100/tests}%
		% cleared (/gs): {(isCleared*100/goodStarts):.2f}%
	""")

# results()

# Total tests: 10000
# goodStarts: 1274
# isPlaying (gs): 831
# isCleared (gs): 443
# isLost: 0
# 
# % cleared: 4.43%
# % cleared (/gs): 34.77%