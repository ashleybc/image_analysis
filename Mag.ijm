
// getArgument allows you to get this variable from calling the macro from another macro
name=getArgument(); 

//this splits the string into an array along _ as a delimiter
spstr=split(name,"_");

var done = false;
for (i=0; i<spstr.length && !done;i++) {
	print("i is",i);
	indEv=indexOf(spstr[i],"x");
	print("indev",indEv);

	if (indEv>=0){ //Flag value for absence of substring is -1
		ind=i;
		done=true;
			}
	else{done=false;
			}
		}	
	
print("ind is",ind);
//goes from 0th character of string to last occurrence of x 
mag=substring(spstr[ind],0,lastIndexOf(spstr[ind],"x"));
print(mag);

//scale settings dependent on magnification
if(mag == 63){
run("Set Scale...", "distance=9.48148 known=1 pixel=1 unit=um global");
print("63x scale set");
} 
else if (mag == 100){
run("Set Scale...", "distance=14.675 known=1 pixel=1 unit=um global"); //14.675 Roland's lab 14.84214 Gordon's lab
print("100x scale set");
}

return mag; 
