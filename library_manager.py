#!/usr/bin/env python3
"""
Python Package Manager - Gradio Interface
A complete GUI tool for managing Python packages with real-time console output
Fully compatible with Gradio 5.47.1 and all versions
"""

import gradio as gr
import subprocess
import sys
import pandas as pd
import threading
import queue
import time
from typing import List, Tuple, Optional

def get_installed_packages() -> List[List[str]]:
    """Get list of installed packages with versions"""
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', 'list'],
                              capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')[2:]  # Skip header lines
        packages = []
        for line in lines:
            if line.strip() and not line.startswith('-'):
                parts = line.split()
                if len(parts) >= 2:
                    packages.append([parts[0], parts[1]])
        return sorted(packages, key=lambda x: x[0].lower())  # Sort by package name
    except subprocess.CalledProcessError as e:
        return [['Error', f'Failed to get packages: {e}']]

def get_environment_info() -> str:
    """Get current Python environment information"""
    import platform
    import os

    # Get pip version
    try:
        pip_result = subprocess.run([sys.executable, '-m', 'pip', '--version'],
                                  capture_output=True, text=True, check=True)
        pip_version = pip_result.stdout.strip().split()[1]
    except:
        pip_version = "Unknown"

    # Get virtual environment info
    venv_info = "Not in virtual environment"
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        venv_info = f"Virtual environment: {sys.prefix}"

    return f"""**Environment Information:**

🐍 **Python:** {sys.version.split()[0]}
📍 **Location:** `{sys.executable}`
🖥️ **Platform:** {platform.system()} {platform.release()} ({platform.machine()})
📦 **pip Version:** {pip_version}
🔧 **Environment:** {venv_info}
📂 **Working Directory:** `{os.getcwd()}`"""

def run_pip_command(command: List[str], console_output: queue.Queue):
    """Run pip command and capture output in real-time"""
    try:
        console_output.put(f"\n🚀 Executing: {' '.join(command)}\n")
        console_output.put("═" * 60 + "\n")

        process = subprocess.Popen(command,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT,
                                 text=True,
                                 universal_newlines=True,
                                 bufsize=1)

        # Read output line by line in real-time
        for line in process.stdout:
            console_output.put(line)

        process.wait()

        console_output.put("═" * 60 + "\n")
        if process.returncode == 0:
            console_output.put("✅ Command completed successfully!\n\n")
        else:
            console_output.put(f"❌ Command failed with return code {process.returncode}\n\n")

    except Exception as e:
        console_output.put(f"\n💥 Error executing command: {str(e)}\n\n")

class PackageManager:
    """Main package manager class handling all operations"""

    def __init__(self):
        self.console_queue = queue.Queue()
        self.current_console = self._get_welcome_message()

    def _get_welcome_message(self) -> str:
        """Get welcome message for console"""
        return f"""🐍 Python Package Manager Console
═══════════════════════════════════════════════════════════

Welcome to the Python Package Manager!
Environment: {sys.executable}
Ready to manage your packages safely and efficiently.

Commands will appear here in real-time...

"""

    def refresh_packages(self):
        """Refresh the package list"""
        self.console_queue.put("🔄 Refreshing package list...\n")
        packages = get_installed_packages()
        if packages and packages[0][0] != 'Error':
            self.console_queue.put(f"✅ Successfully loaded {len(packages)} packages!\n\n")
        else:
            self.console_queue.put("❌ Failed to load packages.\n\n")
        return packages, self.update_console()

    def get_package_info(self, package_name: str):
        """Get detailed information about a package"""
        if not package_name or not package_name.strip():
            self.console_queue.put("❌ Please enter a package name to get information.\n\n")
            return get_installed_packages(), self.update_console()

        package_name = package_name.strip()
        command = [sys.executable, '-m', 'pip', 'show', package_name]
        thread = threading.Thread(target=run_pip_command, args=(command, self.console_queue))
        thread.daemon = True
        thread.start()

        return get_installed_packages(), self.update_console()

    def uninstall_package(self, package_name: str):
        """Uninstall a package"""
        if not package_name or not package_name.strip():
            self.console_queue.put("❌ Please enter a package name to uninstall.\n\n")
            return get_installed_packages(), self.update_console()

        package_name = package_name.strip()

        # Warn about critical system packages
        critical_packages = ['pip', 'setuptools', 'wheel', 'python', 'gradio']
        if package_name.lower() in critical_packages:
            self.console_queue.put(f"⚠️  WARNING: '{package_name}' is a critical system package!\n")
            self.console_queue.put("Uninstalling this may break your Python environment.\n")
            self.console_queue.put("Proceeding anyway...\n\n")

        command = [sys.executable, '-m', 'pip', 'uninstall', package_name, '-y']
        thread = threading.Thread(target=run_pip_command, args=(command, self.console_queue))
        thread.daemon = True
        thread.start()

        return get_installed_packages(), self.update_console()

    def install_package(self, package_name: str, version: str = ""):
        """Install a package with optional version specification"""
        if not package_name or not package_name.strip():
            self.console_queue.put("❌ Please enter a package name to install.\n\n")
            return get_installed_packages(), self.update_console()

        package_name = package_name.strip()

        # Handle version specification
        if version and version.strip():
            version = version.strip()
            # Support different version specifiers
            if not any(op in version for op in ['==', '>=', '<=', '>', '<', '~=', '!=']):
                package_spec = f"{package_name}=={version}"
            else:
                package_spec = f"{package_name}{version}"
        else:
            package_spec = package_name

        self.console_queue.put(f"📦 Installing package: {package_spec}\n")
        command = [sys.executable, '-m', 'pip', 'install', package_spec]
        thread = threading.Thread(target=run_pip_command, args=(command, self.console_queue))
        thread.daemon = True
        thread.start()

        return get_installed_packages(), self.update_console()

    def update_package(self, package_name: str):
        """Update a package to the latest version"""
        if not package_name or not package_name.strip():
            self.console_queue.put("❌ Please enter a package name to update.\n\n")
            return get_installed_packages(), self.update_console()

        package_name = package_name.strip()
        self.console_queue.put(f"⬆️ Updating package: {package_name}\n")
        command = [sys.executable, '-m', 'pip', 'install', '--upgrade', package_name]
        thread = threading.Thread(target=run_pip_command, args=(command, self.console_queue))
        thread.daemon = True
        thread.start()

        return get_installed_packages(), self.update_console()

    def reinstall_package(self, package_name: str):
        """Reinstall a package (force reinstall)"""
        if not package_name or not package_name.strip():
            self.console_queue.put("❌ Please enter a package name to reinstall.\n\n")
            return get_installed_packages(), self.update_console()

        package_name = package_name.strip()
        self.console_queue.put(f"🔄 Reinstalling package: {package_name}\n")
        command = [sys.executable, '-m', 'pip', 'install', '--force-reinstall', '--no-deps', package_name]
        thread = threading.Thread(target=run_pip_command, args=(command, self.console_queue))
        thread.daemon = True
        thread.start()

        return get_installed_packages(), self.update_console()

    def search_packages(self, search_term: str):
        """Search for packages on PyPI"""
        if not search_term or not search_term.strip():
            self.console_queue.put("❌ Please enter a search term.\n\n")
            return get_installed_packages(), self.update_console()

        search_term = search_term.strip()
        self.console_queue.put(f"🔍 Searching PyPI for: '{search_term}'\n")
        self.console_queue.put("═" * 60 + "\n")
        self.console_queue.put("Note: pip search is deprecated. Using PyPI web search instead.\n")
        self.console_queue.put(f"🌐 Visit: https://pypi.org/search/?q={search_term}\n")
        self.console_queue.put("\nAlternatively, you can try installing directly if you know the package name.\n\n")

        return get_installed_packages(), self.update_console()

    def list_outdated_packages(self):
        """List all outdated packages"""
        self.console_queue.put("🔍 Checking for outdated packages...\n")
        self.console_queue.put("This may take a moment to check all packages...\n\n")

        command = [sys.executable, '-m', 'pip', 'list', '--outdated', '--format=columns']
        thread = threading.Thread(target=run_pip_command, args=(command, self.console_queue))
        thread.daemon = True
        thread.start()

        return get_installed_packages(), self.update_console()

    def upgrade_all_packages(self):
        """Upgrade all packages (dangerous operation)"""
        self.console_queue.put("⚠️  BULK UPGRADE OPERATION\n")
        self.console_queue.put("═" * 60 + "\n")
        self.console_queue.put("WARNING: This will attempt to upgrade ALL packages!\n")
        self.console_queue.put("This operation can take a very long time and may cause conflicts.\n")
        self.console_queue.put("It is recommended to upgrade packages individually.\n\n")

        self.console_queue.put("🚀 Starting bulk upgrade...\n")

        # First get list of outdated packages
        try:
            result = subprocess.run([sys.executable, '-m', 'pip', 'list', '--outdated', '--format=freeze'],
                                  capture_output=True, text=True, check=True)
            outdated_lines = result.stdout.strip().split('\n')
            outdated_packages = [line.split('==')[0] for line in outdated_lines if '==' in line]

            if not outdated_packages:
                self.console_queue.put("✅ All packages are already up to date!\n\n")
                return get_installed_packages(), self.update_console()

            self.console_queue.put(f"Found {len(outdated_packages)} packages to upgrade:\n")
            for pkg in outdated_packages[:10]:  # Show first 10
                self.console_queue.put(f"  • {pkg}\n")
            if len(outdated_packages) > 10:
                self.console_queue.put(f"  ... and {len(outdated_packages) - 10} more\n")

            # Upgrade packages one by one
            for i, package in enumerate(outdated_packages, 1):
                self.console_queue.put(f"\n[{i}/{len(outdated_packages)}] Upgrading {package}...\n")
                command = [sys.executable, '-m', 'pip', 'install', '--upgrade', package]
                run_pip_command(command, self.console_queue)

        except Exception as e:
            self.console_queue.put(f"❌ Error during bulk upgrade: {e}\n\n")

        return get_installed_packages(), self.update_console()

    def freeze_requirements(self):
        """Generate requirements.txt file"""
        self.console_queue.put("📋 Generating requirements.txt...\n")

        command = [sys.executable, '-m', 'pip', 'freeze']
        thread = threading.Thread(target=run_pip_command, args=(command, self.console_queue))
        thread.daemon = True
        thread.start()

        return get_installed_packages(), self.update_console()

    def install_from_requirements(self, requirements_text: str):
        """Install packages from requirements text"""
        if not requirements_text or not requirements_text.strip():
            self.console_queue.put("❌ Please enter requirements text.\n\n")
            return get_installed_packages(), self.update_console()

        # Save requirements to temporary file
        import tempfile
        import os

        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(requirements_text.strip())
                temp_req_file = f.name

            self.console_queue.put("📦 Installing from requirements...\n")
            command = [sys.executable, '-m', 'pip', 'install', '-r', temp_req_file]
            thread = threading.Thread(target=run_pip_command, args=(command, self.console_queue))
            thread.daemon = True
            thread.start()

            # Clean up temp file after a delay
            def cleanup():
                time.sleep(30)  # Wait 30 seconds
                try:
                    os.unlink(temp_req_file)
                except:
                    pass

            cleanup_thread = threading.Thread(target=cleanup)
            cleanup_thread.daemon = True
            cleanup_thread.start()

        except Exception as e:
            self.console_queue.put(f"❌ Error processing requirements: {e}\n\n")

        return get_installed_packages(), self.update_console()

    def update_console(self):
        """Update console display with new messages"""
        try:
            while True:
                message = self.console_queue.get_nowait()
                self.current_console += message
                # Limit console length to prevent memory issues
                if len(self.current_console) > 100000:
                    # Keep last 80,000 characters
                    self.current_console = "... (earlier output truncated) ...\n\n" + self.current_console[-80000:]
        except queue.Empty:
            pass
        return self.current_console

    def clear_console(self):
        """Clear the console"""
        self.current_console = self._get_welcome_message()
        # Clear the queue as well
        while not self.console_queue.empty():
            try:
                self.console_queue.get_nowait()
            except queue.Empty:
                break
        return self.current_console

# Create the package manager instance
pm = PackageManager()

def create_interface():
    """Create the main Gradio interface"""

    with gr.Blocks(title="🐍 Python Package Manager", theme=gr.themes.Soft()) as demo:

        # Header
        gr.Markdown("# 🐍 Python Package Manager")
        gr.Markdown("**Manage your Python packages with ease and real-time feedback!**")

        # Environment information
        with gr.Accordion("📊 Environment Information", open=False):
            gr.Markdown(get_environment_info())

        with gr.Row():
            # Left Column - Package Management
            with gr.Column(scale=1):
                gr.Markdown("## 📦 Package Management")

                # Package list section
                with gr.Group():
                    gr.Markdown("### 📋 Installed Packages")

                    with gr.Row():
                        refresh_btn = gr.Button("🔄 Refresh List", variant="secondary", size="sm")
                        package_count = gr.Textbox(
                            value=f"Total: {len(get_installed_packages())} packages",
                            label="Package Count",
                            interactive=False,
                            scale=2
                        )

                    package_df = gr.Dataframe(
                        value=get_installed_packages(),
                        headers=["Package", "Version"],
                        datatype=["str", "str"],
                        interactive=False
                    )

                # Package operations section
                with gr.Group():
                    gr.Markdown("### 🛠️ Package Operations")

                    with gr.Row():
                        package_input = gr.Textbox(
                            label="Package Name",
                            placeholder="e.g., numpy, pandas, requests",
                            scale=2
                        )
                        version_input = gr.Textbox(
                            label="Version (optional)",
                            placeholder="e.g., >=1.21.0, ==2.0.1",
                            scale=1
                        )

                    # Main action buttons
                    with gr.Row():
                        install_btn = gr.Button("📥 Install", variant="primary")
                        uninstall_btn = gr.Button("🗑️ Uninstall", variant="stop")

                    with gr.Row():
                        update_btn = gr.Button("⬆️ Update", variant="secondary")
                        reinstall_btn = gr.Button("🔄 Reinstall", variant="secondary")

                    with gr.Row():
                        info_btn = gr.Button("ℹ️ Package Info", variant="secondary")
                        search_btn = gr.Button("🔍 Search PyPI", variant="secondary")

                # Bulk operations
                with gr.Group():
                    gr.Markdown("### 📊 Bulk Operations")
                    with gr.Row():
                        list_outdated_btn = gr.Button("📋 List Outdated", variant="secondary")
                        upgrade_all_btn = gr.Button("⚠️ Upgrade All", variant="stop")

                    with gr.Row():
                        freeze_btn = gr.Button("💾 Export Requirements", variant="secondary")

                # Requirements section
                with gr.Group():
                    gr.Markdown("### 📄 Requirements Management")
                    requirements_input = gr.Textbox(
                        label="Requirements Text",
                        placeholder="Enter requirements (one per line):\nnumpy>=1.21.0\npandas==1.3.0",
                        lines=4,
                        max_lines=10
                    )
                    install_req_btn = gr.Button("📦 Install from Requirements", variant="primary")

            # Right Column - Console Output
            with gr.Column(scale=1):
                gr.Markdown("## 🖥️ Real-time Console")

                console_output = gr.Textbox(
                    label="Console Output",
                    value=pm.current_console,
                    lines=30,
                    max_lines=35,
                    interactive=False,
                    show_copy_button=True
                )

                with gr.Row():
                    clear_console_btn = gr.Button("🧹 Clear Console", variant="secondary")
                    refresh_console_btn = gr.Button("🔄 Refresh Console", variant="secondary")

                # Console status
                with gr.Row():
                    console_status = gr.Textbox(
                        label="Status",
                        value="Ready - Click 'Refresh Console' to update",
                        interactive=False,
                        scale=3
                    )

        # Event handlers
        def update_package_count():
            packages = get_installed_packages()
            return f"Total: {len(packages)} packages"

        refresh_btn.click(
            fn=lambda: (*pm.refresh_packages(), update_package_count()),
            outputs=[package_df, console_output, package_count]
        )

        install_btn.click(
            fn=lambda pkg, ver: (*pm.install_package(pkg, ver), update_package_count()),
            inputs=[package_input, version_input],
            outputs=[package_df, console_output, package_count]
        )

        uninstall_btn.click(
            fn=lambda pkg: (*pm.uninstall_package(pkg), update_package_count()),
            inputs=[package_input],
            outputs=[package_df, console_output, package_count]
        )

        update_btn.click(
            fn=lambda pkg: (*pm.update_package(pkg), update_package_count()),
            inputs=[package_input],
            outputs=[package_df, console_output, package_count]
        )

        reinstall_btn.click(
            fn=lambda pkg: (*pm.reinstall_package(pkg), update_package_count()),
            inputs=[package_input],
            outputs=[package_df, console_output, package_count]
        )

        info_btn.click(
            fn=pm.get_package_info,
            inputs=[package_input],
            outputs=[package_df, console_output]
        )

        search_btn.click(
            fn=pm.search_packages,
            inputs=[package_input],
            outputs=[package_df, console_output]
        )

        list_outdated_btn.click(
            fn=pm.list_outdated_packages,
            outputs=[package_df, console_output]
        )

        upgrade_all_btn.click(
            fn=lambda: (*pm.upgrade_all_packages(), update_package_count()),
            outputs=[package_df, console_output, package_count]
        )

        freeze_btn.click(
            fn=pm.freeze_requirements,
            outputs=[package_df, console_output]
        )

        install_req_btn.click(
            fn=lambda req: (*pm.install_from_requirements(req), update_package_count()),
            inputs=[requirements_input],
            outputs=[package_df, console_output, package_count]
        )

        clear_console_btn.click(
            fn=pm.clear_console,
            outputs=[console_output]
        )

        refresh_console_btn.click(
            fn=pm.update_console,
            outputs=[console_output]
        )

    return demo

def main():
    """Main function to start the application"""
    print("🚀 Python Package Manager Starting Up...")
    print("═" * 60)
    print(f"📍 Python Environment: {sys.executable}")
    print(f"📦 Total Packages Found: {len(get_installed_packages())}")

    # Check Gradio version
    try:
        print(f"🎨 Gradio Version: {gr.__version__}")
    except:
        print("🎨 Gradio Version: Unknown")

    print("═" * 60)
    print("🌐 Starting web interface...")
    print("🔗 URL: http://127.0.0.1:7860")
    print("═" * 60)
    print("💡 Note: Console updates manually - click 'Refresh Console' to see latest output")
    print("═" * 60)

    # Create and launch interface
    demo = create_interface()
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        debug=False,
        show_error=True,
        quiet=False,
        inbrowser=True,
        show_api=False
    )

if __name__ == "__main__":
    main()
