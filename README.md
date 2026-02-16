# Screenshot Helper

A Python GUI application that allows you to capture screenshots of custom-defined screen areas with a configurable hotkey.

## Features

- **Multi-Monitor Support**: Define screen areas across multiple monitors
- **Custom Hotkey**: Set a custom hotkey to trigger screenshots
- **Configurable Save Location**: Choose where to save your screenshots
- **Area Management**: Easily add and remove screen capture areas
- **Visual Area Selection**: Drag your mouse to visually define capture areas

## Installation

### Prerequisites
- Python 3.8 or higher
- Windows (primarily tested on Windows, may work on other OS with modifications)

### Setup

1. Navigate to the project directory:
   ```
   cd "c:\Screenshot-Helper"
   ```

2. Activate the virtual environment:
   ```
   .\venv\Scripts\activate
   ```

3. Install dependencies (if not already done):
   ```
   pip install -r requirements.txt
   ```

## Usage

### Running the Application

```
.\venv\Scripts\python screenshot_helper.py
```

### GUI Components

1. **Save Location**
   - Click "Browse" to select where screenshots will be saved
   - This must be set before taking screenshots

2. **Hotkey Configuration**
   - Click "Set Hotkey" to configure a keyboard shortcut
   - Press the key combination you want within 5 seconds
   - The hotkey is displayed on the button

3. **Screen Areas**
   - **ADD Area**: Click to enter area selection mode. Drag your mouse across the screen to define a capture area. Press ESC to cancel.
   - **DELETE Selected**: Select an area from the list and click to remove it
   - Areas are saved to `config.json` and persist between sessions

### Taking Screenshots

Press your configured hotkey to capture all defined areas. Screenshots are saved with timestamps to your chosen location.

## Configuration

Settings are stored in `config.json` and include:
- Save location
- Hotkey configuration
- Screen area definitions

## Dependencies

- **Pillow**: Image processing and capture
- **mss**: Multi-monitor screenshot support
- **pynput**: Global hotkey detection

## File Structure

```
Screenshot-Helper/
├── screenshot_helper.py    # Main application
├── config.json            # Configuration storage
├── requirements.txt       # Python dependencies
├── venv/                  # Virtual environment
└── README.md             # This file
```

## Notes

- Screenshots are saved as PNG files with timestamps
- Multiple areas are captured and saved with area numbers (area1, area2, etc.)
- The application runs in the system tray/taskbar when minimized
- Configuration persists between sessions

## Troubleshooting

- **Hotkey not working**: Ensure the application window has focus or try running as Administrator
- **Screenshots blank**: Verify the area coordinates are correct and visible on your monitor
- **Import errors**: Make sure the virtual environment is activated and all packages are installed
