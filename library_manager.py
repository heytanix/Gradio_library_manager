#!/usr/bin/env python3
"""
PUIPM - Python User Interfaced Package Manager
Flask-based web interface for managing Python packages
FINAL VERSION WITH AGGRESSIVE UI REFRESH
"""
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
import subprocess
import sys
import threading
import queue
import time
import shutil
import psutil
import os
import platform
from typing import List, Dict, Optional
import json
import pkg_resources

app = Flask(__name__, template_folder='components', static_folder='components')
app.config['SECRET_KEY'] = 'puipm-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

class PackageManager:
    """Main package manager class with AGGRESSIVE UI refresh"""

    def __init__(self):
        self.console_queue = queue.Queue()
        self.current_console = self._get_welcome_message()
        self._operation_in_progress = False

    def _get_welcome_message(self) -> str:
        """Get welcome message for console"""
        return f"""🐍 PUIPM - Python User Interfaced Package Manager
═══════════════════════════════════════════════════════════
Welcome to PUIPM!
Environment: {sys.executable}
Ready to manage your packages safely and efficiently.
Commands will appear here in real-time...

"""

    def get_installed_packages(self) -> List[Dict]:
        """Get list of installed packages - ALWAYS FRESH"""
        try:
            # Force fresh reload of pkg_resources working_set
            if hasattr(pkg_resources, '_initialize_master_working_set'):
                pkg_resources._initialize_master_working_set()

            # Clear any caches
            if hasattr(pkg_resources.working_set, '_cache'):
                pkg_resources.working_set._cache.clear()

            # Get fresh package list
            working_set = sorted(pkg_resources.working_set, key=lambda d: d.project_name.lower())
            packages = []
            for dist in working_set:
                packages.append({
                    'name': dist.project_name,
                    'version': dist.version
                })

            print(f"📦 Fresh package list loaded: {len(packages)} packages")
            return packages

        except Exception as e:
            print(f"Error with pkg_resources, falling back to pip list: {e}")
            # Fallback to subprocess with timeout
            try:
                result = subprocess.run([sys.executable, '-m', 'pip', 'list', '--format=json'],
                                      capture_output=True, text=True, check=True, timeout=15)
                pip_packages = json.loads(result.stdout)
                packages = [{'name': pkg['name'], 'version': pkg['version']} for pkg in pip_packages]
                print(f"📦 Fallback package list loaded: {len(packages)} packages")
                return packages
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired, json.JSONDecodeError) as fallback_error:
                print(f"Both methods failed: {e}, {fallback_error}")
                return [{'name': 'Error', 'version': f'Failed to get packages: {str(e)}'}]

    def _force_ui_refresh(self, delay=1.0):
        """AGGRESSIVELY force UI to refresh package list"""
        def delayed_refresh():
            time.sleep(delay)
            try:
                print(f"🔄 FORCING UI REFRESH after {delay} seconds")

                # Get completely fresh package list
                fresh_packages = self.get_installed_packages()

                # Send multiple update events to ensure UI gets them
                socketio.emit('force_package_update', {
                    'packages': fresh_packages,
                    'timestamp': time.time(),
                    'force': True
                }, broadcast=True)

                socketio.emit('package_list_changed', {
                    'packages': fresh_packages,
                    'count': len(fresh_packages),
                    'timestamp': time.time()
                }, broadcast=True)

                socketio.emit('refresh_package_display', {
                    'packages': fresh_packages,
                    'source': 'force_refresh'
                }, broadcast=True)

                print(f"📦 Sent force refresh with {len(fresh_packages)} packages")

            except Exception as e:
                print(f"Error in force refresh: {e}")

        # Run in background thread
        thread = threading.Thread(target=delayed_refresh, daemon=True)
        thread.start()

    def run_pip_command(self, command: List[str]):
        """Run pip command and AGGRESSIVELY refresh UI afterward"""
        self._operation_in_progress = True
        try:
            cmd_str = ' '.join(command)
            self.console_queue.put(f"\n🚀 Executing: {cmd_str}\n")
            self.console_queue.put("═" * 60 + "\n")
            socketio.emit('console_update', {'data': f"\n🚀 Executing: {cmd_str}\n"})
            socketio.emit('console_update', {'data': "═" * 60 + "\n"})

            # Execute command
            process = subprocess.Popen(command,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT,
                                     text=True,
                                     universal_newlines=True,
                                     bufsize=1)

            # Read output line by line
            start_time = time.time()
            timeout = 300

            while True:
                if time.time() - start_time > timeout:
                    process.terminate()
                    timeout_msg = f"\n⏰ Command timed out after {timeout} seconds\n"
                    self.console_queue.put(timeout_msg)
                    socketio.emit('console_update', {'data': timeout_msg})
                    break

                try:
                    if process.poll() is not None:
                        remaining = process.stdout.read()
                        if remaining:
                            self.console_queue.put(remaining)
                            socketio.emit('console_update', {'data': remaining})
                        break

                    line = process.stdout.readline()
                    if line:
                        self.console_queue.put(line)
                        socketio.emit('console_update', {'data': line})
                    else:
                        time.sleep(0.1)

                except Exception as read_error:
                    error_msg = f"\n💥 Error reading output: {str(read_error)}\n"
                    self.console_queue.put(error_msg)
                    socketio.emit('console_update', {'data': error_msg})
                    break

            process.wait()
            separator = "═" * 60 + "\n"
            self.console_queue.put(separator)
            socketio.emit('console_update', {'data': separator})

            if process.returncode == 0:
                success_msg = "✅ Command completed successfully!\n\n"
                self.console_queue.put(success_msg)
                socketio.emit('console_update', {'data': success_msg})
                socketio.emit('operation_complete', {'success': True})

                # AGGRESSIVE: Multiple refresh attempts at different intervals
                self._force_ui_refresh(0.5)  # Immediate
                self._force_ui_refresh(1.5)  # Short delay
                self._force_ui_refresh(3.0)  # Longer delay

            else:
                error_msg = f"❌ Command failed with return code {process.returncode}\n\n"
                self.console_queue.put(error_msg)
                socketio.emit('console_update', {'data': error_msg})
                socketio.emit('operation_complete', {'success': False})

                # Even on failure, refresh UI in case something changed
                self._force_ui_refresh(1.0)
                self._force_ui_refresh(2.5)

        except Exception as e:
            error_msg = f"\n💥 Error executing command: {str(e)}\n\n"
            self.console_queue.put(error_msg)
            socketio.emit('console_update', {'data': error_msg})
            socketio.emit('operation_complete', {'success': False})

            # Force refresh even on exception
            self._force_ui_refresh(1.0)
        finally:
            self._operation_in_progress = False

    def install_package(self, package_name: str, version: str = ""):
        """Install a package"""
        if not package_name or not package_name.strip():
            return {'success': False, 'message': 'Please enter a package name'}

        package_name = package_name.strip()

        if version and version.strip():
            version = version.strip()
            if not any(op in version for op in ['==', '>=', '<=', '>', '<', '~=', '!=']):
                package_spec = f"{package_name}=={version}"
            else:
                package_spec = f"{package_name}{version}"
        else:
            package_spec = package_name

        command = [sys.executable, '-m', 'pip', 'install', package_spec]
        thread = threading.Thread(target=self.run_pip_command, args=(command,))
        thread.daemon = True
        thread.start()

        return {'success': True, 'message': f'Installing {package_spec}...'}

    def uninstall_package(self, package_name: str):
        """Uninstall a package"""
        if not package_name or not package_name.strip():
            return {'success': False, 'message': 'Please enter a package name'}

        package_name = package_name.strip()

        critical_packages = ['pip', 'setuptools', 'wheel', 'python', 'flask', 'flask-socketio']
        if package_name.lower() in critical_packages:
            warning_msg = f"⚠️ WARNING: '{package_name}' is a critical system package!\n"
            self.console_queue.put(warning_msg)
            socketio.emit('console_update', {'data': warning_msg})

        command = [sys.executable, '-m', 'pip', 'uninstall', package_name, '-y']
        thread = threading.Thread(target=self.run_pip_command, args=(command,))
        thread.daemon = True
        thread.start()

        return {'success': True, 'message': f'Uninstalling {package_name}...'}

    def update_package(self, package_name: str):
        """Update a package"""
        if not package_name or not package_name.strip():
            return {'success': False, 'message': 'Please enter a package name'}

        package_name = package_name.strip()
        command = [sys.executable, '-m', 'pip', 'install', '--upgrade', package_name]
        thread = threading.Thread(target=self.run_pip_command, args=(command,))
        thread.daemon = True
        thread.start()

        return {'success': True, 'message': f'Updating {package_name}...'}

    def reinstall_package(self, package_name: str):
        """Reinstall a package"""
        if not package_name or not package_name.strip():
            return {'success': False, 'message': 'Please enter a package name'}

        package_name = package_name.strip()
        command = [sys.executable, '-m', 'pip', 'install', '--force-reinstall', '--no-deps', package_name]
        thread = threading.Thread(target=self.run_pip_command, args=(command,))
        thread.daemon = True
        thread.start()

        return {'success': True, 'message': f'Reinstalling {package_name}...'}

def get_storage_info():
    """Get storage information for all mounted drives"""
    storage_data = []
    try:
        partitions = psutil.disk_partitions()

        for partition in partitions:
            try:
                partition_usage = psutil.disk_usage(partition.mountpoint)
                total_gb = partition_usage.total / (1024**3)
                used_gb = partition_usage.used / (1024**3)
                free_gb = partition_usage.free / (1024**3)
                used_percent = (partition_usage.used / partition_usage.total) * 100

                is_usb = detect_usb_drive(partition.mountpoint, partition.device)

                storage_data.append({
                    'device': partition.device,
                    'mountpoint': partition.mountpoint,
                    'filesystem': partition.fstype,
                    'total_gb': round(total_gb, 2),
                    'used_gb': round(used_gb, 2),
                    'free_gb': round(free_gb, 2),
                    'used_percent': round(used_percent, 1),
                    'type': 'USB' if is_usb else 'Internal'
                })
            except (PermissionError, OSError):
                continue
    except Exception as e:
        print(f"Error getting storage info: {e}")

    return storage_data

def detect_usb_drive(mountpoint, device):
    """Detect if a drive is USB-connected"""
    try:
        usb_indicators = ['/media/', '/mnt/', '/run/media/']
        if any(mountpoint.startswith(indicator) for indicator in usb_indicators):
            return True

        if platform.system() == 'Linux':
            device_name = device.split('/')[-1].rstrip('0123456789')
            sys_path = f'/sys/block/{device_name}'
            if os.path.exists(sys_path):
                try:
                    real_path = os.path.realpath(sys_path)
                    if 'usb' in real_path.lower():
                        return True
                except:
                    pass
        return False
    except:
        return False

def get_current_cache_locations():
    """Get current cache locations for different tools"""
    cache_info = {}

    try:
        result = subprocess.run([sys.executable, '-m', 'pip', 'cache', 'dir'],
                              capture_output=True, text=True, check=True, timeout=10)
        cache_info['pip_cache'] = result.stdout.strip()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        cache_info['pip_cache'] = "~/.cache/pip (default)"

    torch_home = os.environ.get('TORCH_HOME')
    if torch_home:
        cache_info['torch_cache'] = torch_home
    else:
        xdg_cache = os.environ.get('XDG_CACHE_HOME')
        if xdg_cache:
            cache_info['torch_cache'] = os.path.join(xdg_cache, 'torch')
        else:
            cache_info['torch_cache'] = os.path.expanduser('~/.cache/torch')

    pycache_prefix = os.environ.get('PYTHONPYCACHEPREFIX')
    if pycache_prefix:
        cache_info['pycache'] = pycache_prefix
    else:
        cache_info['pycache'] = "Project directories (default)"

    return cache_info

def set_cache_location(cache_type, location):
    """Set cache location for specified cache type"""
    try:
        if cache_type == "pip_cache":
            result = subprocess.run([sys.executable, '-m', 'pip', 'config', 'set',
                                   'global.cache-dir', location],
                                  capture_output=True, text=True, check=True, timeout=10)
            return f"✅ Pip cache location set to: {location}"
        elif cache_type == "torch_cache":
            os.environ['TORCH_HOME'] = location
            return f"✅ PyTorch cache location set to: {location}\n⚠️ Note: Add 'export TORCH_HOME={location}' to ~/.bashrc for persistence."
        elif cache_type == "pycache":
            os.environ['PYTHONPYCACHEPREFIX'] = location
            return f"✅ Python __pycache__ location set to: {location}\n⚠️ Note: Add 'export PYTHONPYCACHEPREFIX={location}' to ~/.bashrc for persistence."
        else:
            return "❌ Invalid cache type specified"
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        return f"❌ Error setting cache location: {e}"
    except Exception as e:
        return f"❌ Unexpected error: {e}"

# Create package manager instance
pm = PackageManager()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/packages')
def get_packages():
    """API endpoint - ALWAYS return fresh package list"""
    try:
        print("🔄 API request for fresh package list")
        packages = pm.get_installed_packages()
        print(f"📦 Returning {len(packages)} packages via API")
        return jsonify(packages)
    except Exception as e:
        print(f"Error in /api/packages: {e}")
        return jsonify([{'name': 'Error', 'version': f'Server error: {str(e)}'}]), 500

@app.route('/api/install', methods=['POST'])
def install_package():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400

        package_name = data.get('package_name', '')
        version = data.get('version', '')
        result = pm.install_package(package_name, version)
        return jsonify(result)
    except Exception as e:
        print(f"Error in /api/install: {e}")
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500

@app.route('/api/uninstall', methods=['POST'])
def uninstall_package():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400

        package_name = data.get('package_name', '')
        result = pm.uninstall_package(package_name)
        return jsonify(result)
    except Exception as e:
        print(f"Error in /api/uninstall: {e}")
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500

@app.route('/api/update', methods=['POST'])
def update_package():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400

        package_name = data.get('package_name', '')
        result = pm.update_package(package_name)
        return jsonify(result)
    except Exception as e:
        print(f"Error in /api/update: {e}")
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500

@app.route('/api/reinstall', methods=['POST'])
def reinstall_package():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400

        package_name = data.get('package_name', '')
        result = pm.reinstall_package(package_name)
        return jsonify(result)
    except Exception as e:
        print(f"Error in /api/reinstall: {e}")
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500

@app.route('/api/storage')
def get_storage():
    try:
        storage = get_storage_info()
        return jsonify(storage)
    except Exception as e:
        print(f"Error in /api/storage: {e}")
        return jsonify([]), 500

@app.route('/api/cache-locations')
def get_cache_locations():
    try:
        cache_info = get_current_cache_locations()
        return jsonify(cache_info)
    except Exception as e:
        print(f"Error in /api/cache-locations: {e}")
        return jsonify({
            'pip_cache': 'Error loading',
            'torch_cache': 'Error loading',
            'pycache': 'Error loading'
        }), 500

@app.route('/api/set-cache', methods=['POST'])
def set_cache():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No data provided'}), 400

        cache_type = data.get('cache_type', '')
        location = data.get('location', '')
        result = set_cache_location(cache_type, location)
        return jsonify({'message': result})
    except Exception as e:
        print(f"Error in /api/set-cache: {e}")
        return jsonify({'message': f'Server error: {str(e)}'}), 500

# WebSocket handlers
@socketio.on('connect')
def handle_connect():
    try:
        emit('console_update', {'data': pm.current_console})
        # Send fresh package list immediately on connect
        packages = pm.get_installed_packages()
        emit('initial_package_load', {
            'packages': packages,
            'count': len(packages)
        })
        print(f"🔌 Client connected, sent {len(packages)} packages")
    except Exception as e:
        print(f"Error in socket connect: {e}")

@socketio.on('clear_console')
def handle_clear_console():
    try:
        pm.current_console = pm._get_welcome_message()
        emit('console_clear', {'data': pm.current_console})
    except Exception as e:
        print(f"Error in clear_console: {e}")

@socketio.on('force_refresh_request')
def handle_force_refresh():
    """Handle forced refresh request from frontend"""
    try:
        print("🔄 Force refresh requested by client")
        packages = pm.get_installed_packages()
        emit('force_package_update', {
            'packages': packages,
            'count': len(packages),
            'timestamp': time.time(),
            'force': True
        })
        print(f"📦 Sent force refresh: {len(packages)} packages")
    except Exception as e:
        print(f"Error in force_refresh_request: {e}")

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    print("🚀 PUIPM - Python User Interfaced Package Manager Starting Up...")
    print("═" * 60)
    print(f"📍 Python Environment: {sys.executable}")
    try:
        total_packages = len(pm.get_installed_packages())
        print(f"📦 Total Packages Found: {total_packages}")
    except Exception as e:
        print(f"📦 Package count unavailable: {e}")
    print("═" * 60)
    print("🌐 Starting web interface...")
    print("🔗 URL: http://127.0.0.1:5000")
    print("🔄 AGGRESSIVE UI REFRESH MODE ENABLED")
    print("═" * 60)

    socketio.run(app, debug=True, host='127.0.0.1', port=5000)
