# Interactive Wall

## Overview
This project presents a low-cost interactive wall system that allows users to control presentation slides using hand gestures instead of a mouse or keyboard. The system uses a webcam to track the user's hand and maps finger movements to screen regions, enabling:
- Next slide
- Previous slide
- Exit program

It is designed to be real-time, user-friendly, and accessible using standard hardware and open-source libraries.

## Features
- Hand gesture-based slide control
- Real-time hand tracking using MediaPipe
- Region-based interaction (simple and efficient)
- Fast response time (~115 ms)
- Works with standard webcam (no special hardware needed)
- Smooth and stable tracking using filtering algorithm

## Technologies Used
- Python 3.9+
- OpenCV
- MediaPipe
- NumPy
- PyAutoGUI

## System Requirements
- Windows 10 or higher
- Webcam
- Projector or display screen
- Python 3.9+ installed

## ⚙️ Installation

### 1. Clone the repository
git clone https://github.com/Maan-magid/interactive-wall
cd interactive-wall

### 2. Create virtual environment (venv)
python -m venv venv

### 3. Activate virtual environment

Windows:
venv\Scripts\activate

Mac / Linux:
source venv/bin/activate

### 4. Install required libraries
pip install -r requirements.txt

## ▶️ How to Run
python run.py

## 📷 Camera Setup (IMPORTANT)
For best performance:
- Place camera 1 to 1.5 meters from the wall
- Ensure camera captures only the projection area
- Adjust field of view (~65° recommended)
- Ensure good and stable lighting

The 4 corners of the camera view should match the screen.

## How to Use

### 1. Calibration
- Follow on-screen instructions
- Point your finger to the 4 corners
- Hold briefly to register each point

### 2. Interaction Mode
- Right side → Next slide
- Left side → Previous slide
- Top-left corner → Exit system

## ⏱️ Control Behavior
The system includes a delay (~3 seconds) between slide changes to prevent accidental multiple triggers.

## 📊 Performance
- Accuracy: ~94%
- Response Time: ~115 ms
- Frame Rate: 20–30 FPS

## ⚠️ Limitations
- Sensitive to poor lighting
- Fast hand movement may reduce accuracy
- Requires calibration before use

## 💡 Tips for Best Performance
- Use plain background
- Keep hand movements smooth
- Ensure proper calibration
- Avoid shadows or clutter

## 🔧 Troubleshooting
- Hand not detected → improve lighting or move closer
- Slides skip too fast → wait for delay between gestures
- Program not working → check Python and installed libraries
- Camera not detected → ensure no other app is using it

## 📌 Important Note about venv
- The venv folder is NOT uploaded to GitHub
- You must create it again on every new device
- It is used only for managing project dependencies locally

## 📌 Future Improvements
- Multi-gesture support (zoom, draw, etc.)
- Multi-user interaction
- Better low-light performance
- AI-based gesture recognition

## 👤 Author
Developed by: Maan Mohamed , Aya 
