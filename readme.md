# Fabric Tracker Application

## Overview

This application helps track fabric production stages from yarn purchase through knitting and dyeing. It supports multiple suppliers, batch and lot tracking, FIFO consumption logic, financial year reporting, and export to Excel.

There are two UI versions included:

- Tkinter (classic Python GUI)  
- PyQt (modern UI with charts and enhanced dashboard)

## Getting Started

### Prerequisites

- A GitHub account  
- Windows 11 64-bit machine to run the executable files  
- No Python installation required locally if using pre-built executables  

### Setup

1. Create a new GitHub repository named `fabric-tracker` (public or private).  
2. Upload all files from this project into the repository root.  
3. Once pushed, GitHub Actions will automatically build the Windows executables.  
4. After the workflow finishes, go to the repository’s **Actions** tab → select the latest run → Download artifacts → get the `.exe` files.  
5. Extract the `.exe` files and the SQLite database into the same folder on your PC.  
6. Run the `.exe` file to launch the app.

### Running from Source (Optional)

If you want to modify or run the app with Python installed, follow:

1. Clone the repository locally.  
2. Install dependencies:  
   ```bash
   pip install -r requirements.txt
