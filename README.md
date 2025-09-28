# Enhanced Python Package Manager

A comprehensive Gradio-based web interface for managing Python packages with advanced storage visualization and cache management capabilities.

![Python](https://img.shields.io/badge/python-3.7+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Gradio](https://img.shields.io/badge/gradio-5.47.1+-orange.svg)

## Table of Contents

- [Features](#features)
- [Screenshots](#screenshots)
- [Installation](#installation)
- [Usage](#usage)
- [System Requirements](#system-requirements)
- [Configuration](#configuration)
- [Advanced Features](#advanced-features)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Features

### **Core Package Management**
- **Install/Uninstall/Update** packages with version specifications
- **Real-time console output** with threaded execution
- **Package information** retrieval and detailed metadata display
- **Requirements management** (import/export requirements.txt)
- **Bulk operations** including upgrade all packages
- **Search integration** with PyPI
- **Safety warnings** for critical system packages

### **Storage & Cache Management**
- **USB storage detection** and visualization
- **Storage usage monitoring** with detailed disk information
- **Configurable cache locations** for pip, PyTorch, and Python
- **Cache management** with environment variable setting
- **Cross-platform storage detection** (Linux, Windows, macOS)

### **User Interface**
- **Modern Gradio interface** with responsive design
- **Real-time console updates** with manual refresh capability
- **Organized layout** with collapsible sections
- **Environment information display**
- **Package count tracking** and statistics

### **Advanced Features**
- **Thread-safe operations** preventing UI freezing
- **Comprehensive error handling** with user-friendly messages
- **Environment detection** (virtual environments, system Python)
- **Cross-platform compatibility** (Windows, Linux, macOS)
- **Memory management** with console output limiting

## Installation

### Prerequisites
- Python 3.7 or higher
- pip package manager

### Quick Install

1. **Clone the repository:**
```bash
git clone https://github.com/heytanix/Gradio_library_manager.git
cd Gradio_library_manager
```

2. **Install dependencies:**
```bash
pip install gradio pandas psutil
```

3. **Run the application:**
```bash
python library_manager.py
```

The web interface will automatically open in your default browser at `http://127.0.0.1:7860`

### Docker Installation (Optional)

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY library_manager.py .

RUN pip install gradio pandas psutil

EXPOSE 7860

CMD ["python", "library_manager.py"]
```

```bash
docker build -t gradio-package-manager .
docker run -p 7860:7860 gradio-package-manager
```

## Usage

### Basic Operations

1. **Install a Package:**
   - Enter package name (e.g., `numpy`, `pandas`)
   - Optionally specify version (e.g., `>=1.21.0`, `==2.0.1`)
   - Click "Install"

2. **View Package Information:**
   - Enter package name
   - Click "ℹPackage Info" to see detailed metadata

3. **Manage Requirements:**
   - Use "Export Requirements" to generate requirements.txt
   - Paste requirements text and click "Install from Requirements"

### Storage Management

1. **View Storage Information:**
   - Expand "Storage & Cache Management" section
   - View all mounted drives with usage statistics
   - Identify USB drives automatically

2. **Configure Cache Locations:**
   - Select cache type (pip, PyTorch, or Python)
   - Enter new cache path (e.g., `/media/usb/cache`)
   - Click "Set Cache Location"

### Console Operations

- **Real-time Output:** All operations show live progress in the console
- **Manual Refresh:** Click "Refresh Console" to update display
- **Clear Console:** Use "Clear Console" to reset output

## System Requirements

### Minimum Requirements
- **RAM:** 512MB available
- **Storage:** 100MB free space
- **Network:** Internet connection for PyPI operations

### Recommended Requirements
- **RAM:** 2GB+ for large package operations
- **Storage:** 1GB+ free space for cache management
- **CPU:** Multi-core processor for concurrent operations

### Supported Platforms
- **Linux:** Ubuntu 18.04+, CentOS 7+, Debian 10+
- **Windows:** Windows 10/11
- **macOS:** macOS 10.14+

## Configuration

### Environment Variables

The application supports several environment variables for customization:

```bash
# Cache locations
export TORCH_HOME="/path/to/torch/cache"
export PYTHONPYCACHEPREFIX="/path/to/pycache"

# Gradio configuration
export GRADIO_SERVER_NAME="0.0.0.0"  # Allow external access
export GRADIO_SERVER_PORT="8080"     # Custom port
```

### Cache Management

Configure persistent cache locations by adding to your shell profile:

```bash
# Add to ~/.bashrc or ~/.zshrc
export TORCH_HOME="/media/usb/torch_cache"
export PYTHONPYCACHEPREFIX="/media/usb/pycache"
```

## Advanced Features

### USB Storage Detection

The application automatically detects USB drives using:
- **Mount point analysis** (`/media/`, `/mnt/`, `/run/media/`)
- **System integration** with `/sys/block` on Linux
- **Cross-platform compatibility** with different OS conventions

### Thread Management

- **Non-blocking operations** using Python threading
- **Queue-based communication** between threads and UI
- **Graceful error handling** with timeout management

### Security Features

- **Critical package warnings** for system-essential packages
- **Permission validation** before dangerous operations
- **Safe temporary file handling** for requirements processing

## Troubleshooting

### Common Issues

**1. Permission Errors:**
```bash
# Run with appropriate permissions
sudo python library_manager.py  # Linux/macOS
```

**2. Port Already in Use:**
```bash
# Kill existing process
pkill -f "library_manager.py"
# Or use different port
GRADIO_SERVER_PORT=8080 python library_manager.py
```

**3. Cache Location Errors:**
- Ensure target directories exist and are writable
- Check USB drive mount status
- Verify filesystem permissions

**4. Package Installation Failures:**
- Check internet connectivity
- Verify package names on PyPI
- Review console output for specific errors

### Debug Mode

Enable verbose logging:
```bash
GRADIO_DEBUG=1 python library_manager.py
```

### Log Files

Console output is automatically managed, but for persistent logging:
```bash
python library_manager.py 2>&1 | tee package_manager.log
```

## Contributing

We welcome contributions! Please follow these guidelines:

### Development Setup

```bash
git clone https://github.com/heytanix/Gradio_library_manager.git
cd Gradio_library_manager
pip install -r requirements-dev.txt  # If available
```

### Code Style

- Follow PEP 8 guidelines
- Use type hints where applicable
- Add docstrings for new functions
- Include error handling

### Submitting Changes

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -am 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Submit a Pull Request

### Reporting Issues

Please include:
- Operating system and version
- Python version
- Complete error messages
- Steps to reproduce

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License
Copyright (c) 2025 Thanish C
```

## Acknowledgments

- **Gradio** team for the excellent web framework
- **Python** community for packaging tools
- **Contributors** who help improve this project

## Contact

- **Author:** Thanish C
- **GitHub:** [@heytanix](https://github.com/heytanix)
- **Repository:** [Gradio_library_manager](https://github.com/heytanix/Gradio_library_manager)

---

**Star this repository if you find it helpful!**

## Project Stats

![GitHub Stars](https://img.shields.io/github/stars/heytanix/Gradio_library_manager)
![GitHub Forks](https://img.shields.io/github/forks/heytanix/Gradio_library_manager)
![GitHub Issues](https://img.shields.io/github/issues/heytanix/Gradio_library_manager)

---