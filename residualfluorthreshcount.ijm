//constants

inFolder = getDirectory("Choose the folder with all input images");
print("infolder is",inFolder);

output_Folder = getDirectory("Choose the folder for output images");

csv_Folder=getDirectory("Choose the folder for csv files");


print("output",output_Folder);

setBatchMode(false);

//set universal parameters for file input/output and particle measurements
run("Input/Output...", "jpeg=85 gif=-1 file=.csv save_column");
run("Set Measurements...", "area mean standard min centroid perimeter fit shape feret's integrated area_fraction limit redirect=None decimal=3");

//this gets the list of all files in the directory
images = getFileList(inFolder);

for (i=0; i<images.length; i++) {

	inputPath = inFolder + images[i];
	print(inputPath);
	fnameInd=lastIndexOf(inputPath, '/');
	fnameStr=substring(inputPath, fnameInd+1);
	print(fnameStr);

	//if(indexOf(toLowerCase(fnameStr),'dapi')==-1){

		//print("DAPI not in file name");
	
		open(inputPath); 
		inName=getTitle();
		print("inName",inName);

		//scale settings dependent on magnification
		mag = runMacro("Mag.ijm", inName); 

		imInfo=getImageInfo();
		imInfoArr=split(imInfo,"\n");
		
		imWidthLine=imInfoArr[3];
		imWidthUM=substring(imWidthLine, 7, indexOf(imWidthLine,'(') - 4);
		imHeightLine=imInfoArr[4];
		imHeightUM=substring(imHeightLine, 8, indexOf(imHeightLine,'(') - 4);

		imAreaUM2=parseFloat(imWidthUM)*parseFloat(imHeightUM);
		print(imAreaUM2);
			
		run("Stack to RGB");
		run("16-bit");
		run("Subtract Background...", "rolling=20");

		orRGBName=getTitle();
		print("original RGB name",orRGBName);

		run("Duplicate...", " ");

		workingImName="working_"+inName;
		print("workingImName",workingImName);
		setMetadata("Label",workingImName);
		rename(workingImName);

		
		run("Gaussian Blur...", "sigma=2");
		setAutoThreshold("Default dark"); //for the ones that come out like shit, repeat program with setAutoThreshold("MaxEntropy dark");
		call("ij.plugin.frame.ThresholdAdjuster.setMode", "B&W");
		run("Threshold...");
		
		getThreshold(lower, upper);
		setThreshold(lower, upper);


		run("Make Binary"); 		//this binary is just to mask the background, not for counting
		binaryName='binaryROImask'+inName;
		setMetadata("Label",binaryName);
		saveAs("Tiff", output_Folder + binaryName);
		rename(binaryName);
	
		run("Analyze Particles...", "size=0.2-Infinity circularity=0.00-1.00 show=Nothing clear add");	//add masked regions to the ROI manager

		selectWindow(orRGBName);

		if(roiManager("count")>1){ //in the case there is only one cell, do not do this
			roiManager("combine"); //combine all ROIs into one ROI area selection
			roiManager("Add");	//add combined cells area to manager
		}
		
		n=roiManager("count")-1;	//find last entry in ROI manager
		roiManager("Select", n);
		
		run("Make Inverse");	//make inverse selection to select the background
		roiManager("Add");

		n=roiManager("count")-1;
		roiManager("Select", n);
		
		roiManager("fill");			//fill background with pure black

		run("Make Binary");"
		binary2Name='binaryTruemask'+inName;
		setMetadata("Label",binary2Name);
		saveAs("Tiff", output_Folder + binary2Name);
		rename(binary2Name);

		roiManager("reset"); //clear the roi manager of all the particles from first binary

		imageCalculator("XOR create", binary2Name,binaryName);
		binaryXORName='binaryXOR'+inName;
		setMetadata("Label",binaryXORName);
		saveAs("Tiff", output_Folder + binaryXORName);
		rename(binaryXORName);
		
		selectWindow(binaryXORName);
		run("Analyze Particles...", "size=0.0314-Infinity circularity=0.00-1.00 clear add");	//add true particles to the ROI manager
		roiManager("measure");
				
		for(j=nResults - 1; j >= 0; j--) {
			percArea = getResult("%Area", j);

			print(percArea);
			
			if(percArea<90){
					print(j);
					roiManager("Select",j);
					roiManager("Delete");
				}
		}
	
		close(binaryName);
		close(binaryXORName);

		selectWindow(binary2Name);
		

		if(roiManager("count")!=0){	//if there are cells unique to each image
			run("Select None");
			roiManager("Show All without labels")
			run("From ROI Manager");
			Overlay.flatten
			run("Make Binary");
			run("Fill Holes");

		}
		binary3Name="FinalMask"+inName;
		setMetadata("Label",binary3Name);
		saveAs("Tiff", output_Folder + binary3Name);
		rename(binary3Name);

		if(roiManager("count")!=0){
			close(binary2Name);
		}	
		
		roiManager("reset");
		
		run("Analyze Particles...", "size=0.0314-Infinity circularity=0.00-1.00 show=[Bare Outlines] clear add");	//add true particles to the ROI manager

		outlinesName="CountOutlinesAll_"+inName;
		print("outlinesName",outlinesName);
		setMetadata("Label",outlinesName);
		saveAs("Tiff", output_Folder + outlinesName);
		rename(outlinesName);

		selectWindow(inName); //must use non-background corrected for actual grey measurements
		run("Stack to RGB");
		run("16-bit");

		notBGcorrName="notbgcorr_"+inName;
		setMetadata("Label",notBGcorrName);
		rename(notBGcorrName);

				
		roiManager("measure");	//mean gray value measurements using true particle binary as ROI selection


		fnInd=indexOf(inName,".");
		tableName=substring(inName, 0, fnInd)+'.csv';
		selectWindow("Results"); 

		for(j=0; j<nResults; j++) {
			setResult("im area um^2", j,imAreaUM2);
		}

		
		saveAs("Results", csv_Folder+'fluorall'+tableName);
		run("Clear Results"); //clear results table for next image set


		if(roiManager("count")>1){ //in the case there is only one cell, do not do this
			roiManager("combine"); //combine all ROIs into one ROI area selection
			roiManager("Add");	//add combined cells area to manager
		}

		n=roiManager("count")-1;	//find last entry in ROI manager
		roiManager("Select", n);
		
		run("Make Inverse");	//make inverse selection to select the background
		roiManager("Add");

		n=roiManager("count")-1;
		roiManager("Select", n);

		roiManager("measure"); //measure background

		saveAs("Results", csv_Folder+'fluorbackground'+tableName);
		run("Clear Results"); //clear results table for next image set

		roiManager("reset"); //clear the roi manager of all the particles before overlay operations

		close(notBGcorrName);

		selectWindow(outlinesName);
		run("Red");
		run("Invert");

		selectWindow(binary3Name);
	
		run("Add Image...", "image="+outlinesName+" x=0 y=0 opacity=100 zero");

		roiManager("Show None");

		Overlay.flatten
	
    	overlayName="Overlay_"+inName;
		print("overlayName",overlayName);
		setMetadata("Label",overlayName);
		saveAs("Tiff", output_Folder + overlayName);
		rename(overlayName);

		close(overlayName);
		close(outlinesName);
		close(binary3Name);
		close(inName);
		close(notBGcorrName);

		roiManager("reset"); //clear the roi manager


	//}
}
	