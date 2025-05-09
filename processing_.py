from ij import IJ, WindowManager
from ij.gui import GenericDialog
from loci.plugins import BF
from loci.plugins.in import ImporterOptions
from ij.plugin.frame import RoiManager
from ij.measure import ResultsTable, Measurements
from ij.plugin.filter import ParticleAnalyzer
from ij.process import ImageProcessor
from ij.plugin.filter import EDM
from java.lang import Double

# Prompt the user to select a .lif file
gd = GenericDialog("Select Image File")
gd.addFileField("Choose a .lif file", "Select a .lif file", 40)
gd.addCheckbox("Show all Channels", True)
gd.addStringField("Select Series", "1")
gd.addCheckbox("Sample On Red Channel", True)
gd.addCheckbox("Sample On Green Channel", False)
gd.addCheckbox("Sample On Blue Channel", False)
gd.addStringField("Gaussian Blur Sigma", "3.0")
gd.addStringField("Threshold Method", "Triangle")
gd.addCheckbox("Apply Watershed", True)
gd.addStringField("Analyze Particles Size", "25-200")
gd.addStringField("Analyze Particles Show", "Outlines")
gd.addStringField("Analyze Particles Circularity", "0.60-1.00")
gd.addCheckbox("Show Blue Channel Measurements ", False)
gd.addCheckbox("Show Green Channel Measurements ", True)
gd.addCheckbox("Show Red Channel Measurements ", False)
gd.showDialog()

if gd.wasCanceled():
	IJ.log("No file selected.")
	exit()

if gd.wasOKed():
	# Get the file path from the dialog
	file_path = gd.getNextString()
	# Get the show all channels option from the dialog
	show_all_channels = gd.getNextBoolean()
	# Get the series index from the dialog
	series_index = int(gd.getNextString()) - 1

	imps = []
	# Open the selected .lif file using Bio-Formats
	try:
		options = ImporterOptions()
		options.setId(file_path)
		options.setSplitChannels(True)  # Open as a single hyperstack
		options.setColorMode(ImporterOptions.COLOR_MODE_COLORIZED)
		#options.setOpenAllSeries(True)  # Open all series in the file
		options.setVirtual(True)  # Open as a virtual stack
		#options.setStackFormat(ImporterOptions.VIEW_HYPERSTACK )
		options.setQuiet(True)
		options.setSeriesOn(series_index, True)  # Select the first series (0-based index)
		imps = BF.openImagePlus(options)
		if len(imps) == 0:
			IJ.log("No images found in the .lif file.")
			exit()
		
		#for imp in imps:
		#	print("Image Title: " + imp.getTitle())
		#	print("Image Dimensions: " + str(imp.getDimensions()))
		#	print("Image Type: " + str(imp.getType()))
		#	print("Image Calibration: " + str(imp.getCalibration()))
		#	print("Image Stack Size: " + str(imp.getStackSize()))
		#	print("Image Pixel Width: " + str(imp.getWidth()))
		#	print("Image Pixel Height: " + str(imp.getHeight()))
		#	print("Image Pixel Depth: " + str(imp.getBitDepth()))
		#	imp.show()  # Show the image in ImageJ
	except Exception as e:
		IJ.log("Error opening .lif file: " + str(e))
		exit()
	
	# Check which channels to duplicate
	duplicate_red = gd.getNextBoolean()
	duplicate_green = gd.getNextBoolean()
	duplicate_blue = gd.getNextBoolean()

	red = "C=2"
	green = "C=1"
	blue = "C=0"
		# Duplicate the selected channels

		# Array Filtered by the channel name
	filtered_imps = []	
	for imp in imps:
		if duplicate_red and red in imp.getTitle():
			red_duplicate = imp.duplicate()
			filtered_imps.append(red_duplicate)
		if duplicate_green and green in imp.getTitle():
			green_duplicate = imp.duplicate()
			filtered_imps.append(green_duplicate)
		if duplicate_blue and blue in imp.getTitle():
			blue_duplicate = imp.duplicate()
			filtered_imps.append(blue_duplicate)
		
	for fimp in filtered_imps:
		fimp.setTitle(fimp.getTitle() + "_duplicate")
		# IJ.run(fimp, "Z Project...", "projection=[Max Intensity]")
		gaussian_sigma = gd.getNextString()
		threshold_method = gd.getNextString()
		IJ.run(fimp, "Gaussian Blur...", "sigma=" + gaussian_sigma + " stack")
		IJ.run(fimp, "Threshold...", "method=" + threshold_method + " stack dark")
		IJ.run(fimp, "Make Binary", "method=" + threshold_method + " background=Dark stack calculate black")
		if gd.getNextBoolean():
			IJ.run(fimp, "Watershed", "stack")
		IJ.run(fimp, "Analyze Particles...", "size=" + gd.getNextString() +" show=" + gd.getNextString() + " circularity=" + gd.getNextString() + " add summarize stack include")
		
		#fimp.show()
	
	#Clear the results table
	rt = ResultsTable.getResultsTable()
	rt.reset()

	#Show the results on the imported image
	if show_all_channels:
		for imp in imps:
			imp.show()
			rm = RoiManager.getInstance()
			if rm is None:
				rm = RoiManager()
			rm.runCommand(imp, "Show All")

	show_blue_measurements = gd.getNextBoolean()
	show_green_measurements = gd.getNextBoolean()
	show_red_measurements = gd.getNextBoolean()

	fimps = []
	for imp in imps:
		if show_blue_measurements and blue in imp.getTitle():
			fimps.append(imp)
		if show_green_measurements and green in imp.getTitle():
			fimps.append(imp)
		if show_red_measurements and red in imp.getTitle():
			fimps.append(imp)
	

	for fimp in fimps:
		fimp.show()
		fimp.setTitle(fimp.getTitle() + "_measurements")
		rm = RoiManager.getInstance()
		if rm is None:
			rm = RoiManager()
		
		rm.runCommand(fimp, "Show All")
		rm.runCommand(fimp, "Select All")
		rm.runCommand(fimp, "Measure")