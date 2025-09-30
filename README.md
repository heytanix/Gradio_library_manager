# PUIPM: Python User Interfaced Package Manager

A Flask + SocketIO–based web application for managing Python packages with advanced storage and cache visualization.

## Features

- **Package Management**  
  Install, uninstall, update, and reinstall packages with version specifications.  
- **Real-Time Console**  
  Live progress updates using WebSockets.  
- **Requirements Handling**  
  Export and install from `requirements.txt`.  
- **Storage & Cache Management**  
  View mounted drives (including USB detection), monitor usage, and configure cache locations for pip, PyTorch, and Python.  
- **Thread-Safe Operations**  
  Non-blocking UI with background threading and comprehensive error handling.  
- **Cross-Platform Compatibility**  
  Supports Linux, Windows, and macOS.

## Installation

### Prerequisites

- Python 3.7 or higher  
- pip package manager  

### Quick Install

```bash
git clone https://github.com/heytanix/PUIPM.git
cd PUIPM
pip install flask flask-socketio pandas psutil pkg-resources
```

### Running the Application

```bash
python library_manager.py
```

The web interface will be available at **http://127.0.0.1:5000**.

### Docker (Optional)

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY . .
RUN pip install flask flask-socketio pandas psutil pkg-resources
EXPOSE 5000
CMD ["python", "library_manager.py"]
```

Build and run:

```bash
docker build -t puipm .
docker run -p 5000:5000 puipm
```

## Usage

1. **Install a Package**  
   Enter the package name (and optional version) and click **Install**.  
2. **View Package Info**  
   Search for a package and click the info icon to see metadata.  
3. **Bulk Operations**  
   Upgrade all outdated packages or manage via requirements file.  
4. **Storage Overview**  
   Navigate to the **Paths** section to view disk usage and USB detection.  
5. **Configure Cache Paths**  
   Edit cache locations for pip, PyTorch, and Python `__pycache__`.

## Configuration

Set environment variables as needed:

```bash
# Pip cache directory
export PIP_CACHE_DIR="/path/to/pip/cache"

# PyTorch cache directory
export TORCH_HOME="/path/to/torch/cache"

# Python __pycache__ prefix
export PYTHONPYCACHEPREFIX="/path/to/pycache"

# Flask settings (optional)
export FLASK_ENV=development
export FLASK_RUN_HOST=0.0.0.0
export FLASK_RUN_PORT=5000
```

## System Requirements

- **RAM:** ≥512 MB (2 GB+ recommended)  
- **Storage:** ≥100 MB free (1 GB+ recommended)  
- **Network:** Internet access for PyPI operations  

## Supported Platforms

- **Linux:** Ubuntu 18.04+, CentOS 7+, Debian 10+  
- **Windows:** Windows 10/11  
- **macOS:** macOS 10.14+  

## Advanced Details

- **USB Detection:** Mount-point analysis and `/sys/block` inspection on Linux.  
- **Thread Management:** Background threads for pip operations with timeout control.  
- **Security:** Warnings for critical system packages (e.g., pip, setuptools).  

## Troubleshooting

- **Permission Errors:**  
  ```bash
  sudo python library_manager.py
  ```  
- **Port Already in Use:**  
  ```bash
  pkill -f library_manager.py
  ```  
  Or change port:  
  ```bash
  export FLASK_RUN_PORT=5001
  ```  
- **Cache Path Issues:** Ensure target directories exist and are writable.

## Contributing

1. Fork the repository  
2. Create a branch: `git checkout -b feature-name`  
3. Commit: `git commit -am "Add feature"`  
4. Push: `git push origin feature-name`  
5. Open a Pull Request

Please follow PEP 8 guidelines, include docstrings, and write tests for new features.

## License

MIT License © 2025 Thanish C.  
See [LICENSE](LICENSE) for details.
