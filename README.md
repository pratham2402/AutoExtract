<!--Please do not remove this part-->
![Star Badge](https://img.shields.io/static/v1?label=%F0%9F%8C%9F&message=If%20Useful&style=style=flat&color=BC4E99)
![Open Source Love](https://badges.frapsoft.com/os/v1/open-source.svg?v=103)
![Python](https://img.shields.io/badge/Python-3776AB.svg?style=for-the-badge&logo=Python&logoColor=white)

# AutoExtract

![](https://github.com/pratham2402/AutoExtract/blob/master/ReadMe%20Banner%20Design.png)

<!--An image is an illustration for your project, the tip here is using your sense of humour as much as you can :D 

You can copy paste my markdown photo insert as following:
<p align="center">
<img src="your-source-is-here" width=40% height=40%>
-->

## 🛠️ Description
<!--Remove the below lines and add yours -->
AutoExtract is a Python-based tool that monitors a specified downloads folder for ZIP files and automatically extracts them to a designated directory. It keeps track of processed files to avoid duplicate extractions and runs continuously, checking for new ZIP files at regular intervals.

Key Features:

    Monitors a folder for new ZIP files
    Automatically extracts ZIP contents to a specified location
    Keeps track of processed files to prevent redundant extractions
    Customizable folder paths and checking intervals

Ideal for automating repetitive unzipping tasks!

## ⚙️ Languages or Frameworks Used
<!--Remove the below lines and add yours -->
Languages:

    Python

Frameworks/Modules:

    os (for file and path operations)
    zipfile (for handling ZIP file extraction)
    time (for controlling the interval between folder check

## 🌟 How to run
<!--Remove the below lines and add yours -->
<b>1. Clone the Repository:</b>
   
   git clone https://github.com/your-username/AutoExtract.git
   
   cd AutoExtract
   
<b>2. Edit Paths: Open the script file and update the following paths with your specific folders:</b>

    downloads_folder: The folder where your ZIP files are downloaded.
   
    unzip_to_folder: The folder where the extracted contents should go.
   
    processed_files_file: The file path to store the list of processed files.
<b>3. Run the Script:</b> 
You can run the script manually using - python3 AutoUnzip.py

<b>4. Set Up as a Service (Optional):</b> To have the script run automatically at startup, you can set it up as a systemd service on Linux systems. This ensures the script starts running in the background after your system boots.

By following these steps, the AutoUnzip script will be up and running, automating the extraction of ZIP files in your specified directory.


<!--## 📺 Demo
Add a Screenshot/GIF showing the sample use of the script (jpeg/png/gif).-->

## 🤖 Author
<!--Remove the below lines and add yours -->
[Pratham2402](https://github.com/pratham2402)
