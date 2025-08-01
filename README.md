# Limelight5921
Demonstration project for the Limelight 3A in Python

In PyCharm Open the Run ... Edit configurations dialog and add a new configuration
that matches the screenshot below. 

![PyCharm - Run - Edit Configurations.png](files/screenshots/PyCharm%20-%20Run%20-%20Edit%20Configurations.png)

Make sure to leave the Working Directory field blank so that it defaults to the project root.
Set the Script Parameters field to the single parameter  
--image_dir=\files\images\ 

From the Python Packages icon in the left margin install numpy and opencv-python

![PyCharm - Python packages.png](files/screenshots/PyCharm%20-%20Python%20packages.png)![](file:///c%3A/Users/lonep/OneDrive/Documents/FTC/FTC%202026/Kickoff%20session%20-%20Limelight/PyCharm%20-%20Python%20packages.png)

Look at the runPipeline_Tester.py. It contains the lines --
```python
##** CHANGE the next two lines for the file and/or alliance you want to test. **
image_filename = "LRS0308173523970710581193948.png"
alliance = "RED"
```
Currently the demonstration code ignores the alliance and thresholds the yellow
samples. But if you look in the file detect_sample_as_runPipeline.py you'll see
a TODO that shows you where to insert the HSV inRange() thresholding of red and
blue samples.
```python
##**TODO In the real IntoTheDeep game you'd want to recognize
# both alliance and neutral (yellow) samples and combine the
# results to target the best sample to pick up. But in the
# interest of simplicity let's just look for the neutral
# samples.
```

The ftc-autonomous directory contains an FTC Autonomous OpMode and companion files
that connect to the current Limelight5921 Python project. That is, the llrobot and
llpython arrays have been designed and tested to match.