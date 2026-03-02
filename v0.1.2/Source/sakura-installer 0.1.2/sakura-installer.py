#!/usr/bin/env python3
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GdkPixbuf, GLib
import subprocess
import sys
import os
import locale
import tempfile
import shutil

# --- Version ---
ALPHA_VERSION = "0.1.2"

# --- Language messages ---
LANG = locale.getdefaultlocale()[0]

MESSAGES = {
    "en": {
        "trust_warning": "Install this application only if you trust its origin.",
        "installation_failed": "Installation failed.",
        "installation_complete": "Installation complete.",
        "reboot_required": "A system restart is required.",
        "install_button": "Install",
        "cancel_button": "Cancel",
        "alpha_version": f"Sakura Linux Installer Manager Alpha v{ALPHA_VERSION}"
    },
    "es": {
        "trust_warning": "Instale esta aplicación solo si confía en su origen.",
        "installation_failed": "La instalación falló.",
        "installation_complete": "Instalación completada.",
        "reboot_required": "Se requiere reiniciar el sistema.",
        "install_button": "Instalar",
        "cancel_button": "Cancelar",
        "alpha_version": f"Sakura Linux Installer Manager Alfa v{ALPHA_VERSION}"
    },
    "ja": {
        "trust_warning": "このアプリケーションをインストールするのは、信頼できる場合のみです。",
        "installation_failed": "インストールに失敗しました。",
        "installation_complete": "インストールが完了しました。",
        "reboot_required": "システムの再起動が必要です。",
        "install_button": "インストール",
        "cancel_button": "キャンセル",
        "alpha_version": f"さくらLinuxインストーラーマネジャー アルファ v{ALPHA_VERSION}"
    }
}

# Select messages
if LANG.startswith("es"):
    msg = MESSAGES["es"]
elif LANG.startswith("ja"):
    msg = MESSAGES["ja"]
else:
    msg = MESSAGES["en"]

class DebInstaller:

    def __init__(self, filepath):
        self.filepath = filepath
        self.package_name = "Unknown"
        self.package_version = "Unknown"
        self.maintainer = "Unknown"

        # Sakura Installer logo
        self.sakura_logo = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")
        # App logo placeholder
        self.app_logo = None

        self.extract_info()
        self.extract_app_logo()
        self.set_default_handler()
        self.show_install_window()

    # --- Extract .deb info ---
    def extract_info(self):
        try:
            output = subprocess.check_output(
                ["dpkg-deb", "-f", self.filepath, "Package", "Version", "Maintainer"],
                text=True
            ).strip().split("\n")
            if len(output) >= 3:
                self.package_name = output[0]
                self.package_version = output[1]
                self.maintainer = output[2]
        except:
            pass

    # --- Extract app logo from .deb (first .png or .xpm in /usr/share/icons) ---
    def extract_app_logo(self):
        temp_dir = tempfile.mkdtemp()
        try:
            subprocess.run(["dpkg-deb", "-x", self.filepath, temp_dir], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            # Look for common icons inside extracted deb
            possible_icons = []
            for root, dirs, files in os.walk(temp_dir):
                for f in files:
                    if f.lower().endswith((".png", ".xpm", ".svg")):
                        possible_icons.append(os.path.join(root, f))
            if possible_icons:
                self.app_logo = possible_icons[0]  # take first found icon
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    # --- Set default .deb handler ---
    def set_default_handler(self):
        user_app_dir = os.path.expanduser("~/.local/share/applications")
        os.makedirs(user_app_dir, exist_ok=True)
        desktop_file = os.path.join(user_app_dir, "sakura-installer.desktop")

        if not os.path.exists(desktop_file):
            content = f"""
[Desktop Entry]
Name=Sakura Linux Installer Manager
Comment=Beginner-friendly .deb installer
Exec={sys.argv[0]} %f
Icon={self.sakura_logo}
Terminal=false
Type=Application
MimeType=application/vnd.debian.binary-package;
Categories=System;
"""
            with open(desktop_file, "w") as f:
                f.write(content)
            os.chmod(desktop_file, 0o644)

        subprocess.run(["update-desktop-database", user_app_dir], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run([
            "xdg-mime",
            "default",
            "sakura-installer.desktop",
            "application/vnd.debian.binary-package"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # --- Show main window ---
    def show_install_window(self):
        window = Gtk.Window(title=msg["alpha_version"])
        window.set_border_width(10)
        window.set_default_size(600, 200)

        # Set taskbar icon to Sakura logo
        if os.path.exists(self.sakura_logo):
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(self.sakura_logo)
            window.set_icon(pixbuf)

        outer_grid = Gtk.Grid(column_spacing=10, row_spacing=10)
        window.add(outer_grid)

        # --- Small Sakura logo corner ---
        if os.path.exists(self.sakura_logo):
            pixbuf_small = GdkPixbuf.Pixbuf.new_from_file(self.sakura_logo)
            pixbuf_small = pixbuf_small.scale_simple(64, 64, GdkPixbuf.InterpType.BILINEAR)
            sakura_image = Gtk.Image.new_from_pixbuf(pixbuf_small)
        else:
            sakura_image = Gtk.Image.new_from_icon_name("application-x-deb", Gtk.IconSize.DIALOG)

        outer_grid.attach(sakura_image, 0, 0, 1, 3)

        # --- VBox for App Logo + Info ---
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)

        # App Logo (inside white rectangle)
        if self.app_logo and os.path.exists(self.app_logo):
            pixbuf_app = GdkPixbuf.Pixbuf.new_from_file(self.app_logo)
            pixbuf_app = pixbuf_app.scale_simple(128, 128, GdkPixbuf.InterpType.BILINEAR)
            app_image = Gtk.Image.new_from_pixbuf(pixbuf_app)
        else:
            # fallback
            app_image = Gtk.Image.new_from_icon_name("application-x-deb", Gtk.IconSize.DIALOG)
        vbox.pack_start(app_image, False, False, 0)

        # --- App Info Labels ---
        name_label = Gtk.Label(label=f"{self.package_name}.deb")
        name_label.set_xalign(0)
        version_label = Gtk.Label(label=f"Version {self.package_version}")
        version_label.set_xalign(0)
        maintainer_label = Gtk.Label(label=self.maintainer)
        maintainer_label.set_xalign(0)

        vbox.pack_start(name_label, False, False, 0)
        vbox.pack_start(version_label, False, False, 0)
        vbox.pack_start(maintainer_label, False, False, 0)

        # --- Buttons ---
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        install_button = Gtk.Button(label=msg["install_button"])
        install_button.connect("clicked", self.on_install_clicked)
        cancel_button = Gtk.Button(label=msg["cancel_button"])
        cancel_button.connect("clicked", lambda x: window.destroy())

        button_box.pack_start(install_button, True, True, 0)
        button_box.pack_start(cancel_button, True, True, 0)

        vbox.pack_start(button_box, False, False, 10)

        outer_grid.attach(vbox, 1, 0, 1, 3)

        window.show_all()
        window.connect("destroy", Gtk.main_quit)
        Gtk.main()

    # --- Install process ---
    def on_install_clicked(self, widget):
        dialog = Gtk.MessageDialog(
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.OK_CANCEL,
            text=msg["trust_warning"]
        )
        response = dialog.run()
        dialog.destroy()
        if response != Gtk.ResponseType.OK:
            return

        try:
            subprocess.run(
                ["pkexec", "apt", "install", "-y", self.filepath],
                check=True
            )
        except subprocess.CalledProcessError:
            err_dialog = Gtk.MessageDialog(
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text=msg["installation_failed"]
            )
            err_dialog.run()
            err_dialog.destroy()
            return

        reboot_required = os.path.exists("/var/run/reboot-required")
        message = msg["installation_complete"]
        if reboot_required:
            message += f"\n{msg['reboot_required']}"

        success_dialog = Gtk.MessageDialog(
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=message
        )
        success_dialog.run()
        success_dialog.destroy()


# --- Main ---
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("No .deb file provided")
        sys.exit(1)

    deb_file = sys.argv[1]
    DebInstaller(deb_file)