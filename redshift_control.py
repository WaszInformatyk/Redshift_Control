#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  redshift_control.py - Kontroler Redshift GTK dla Polski
#
#  Copyright (C) 2025  Wasz Informatyk
#
#  Ten program jest wolnym oprogramowaniem; możesz go rozprowadzać dalej i/lub
#  modyfikować na warunkach Powszechnej Licencji Publicznej GNU, wydanej przez
#  Fundację Wolnego Oprogramowania; według wersji 3 tej Licencji lub (według
#  twojego wyboru) którejkolwiek późniejszej wersji.
#
#  Ten program rozpowszechniany jest z nadzieją, że będzie użyteczny – jednak
#  BEZ JAKIEJKOLWIEK GWARANCJI, nawet domyślnej gwarancji PRZYDATNOŚCI
#  HANDLOWEJ albo PRZYDATNOŚCI DO OKREŚLONYCH ZASTOSOWAŃ. W celu uzyskania
#  bliższych informacji sięgnij do Powszechnej Licencji Publicznej GNU.
#
#  Powinieneś otrzymać kopię Powszechnej Licencji Publicznej GNU wraz z tym
#  programem; jeśli nie – zobacz <https://www.gnu.org/licenses/>.

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import subprocess
import re
import time
import os
import configparser

POLISH_CITIES = {
    "Białystok": ("53.13", "23.16"), "Bydgoszcz": ("53.12", "18.00"),
    "Gdańsk": ("54.35", "18.64"), "Gorzów Wielkopolski": ("52.73", "15.24"),
    "Katowice": ("50.26", "19.02"), "Kielce": ("50.87", "20.62"),
    "Kraków": ("50.06", "19.94"), "Lublin": ("51.24", "22.56"),
    "Łódź": ("51.76", "19.45"), "Olsztyn": ("53.77", "20.49"),
    "Opole": ("50.67", "17.92"), "Poznań": ("52.40", "16.92"),
    "Rzeszów": ("50.04", "21.99"), "Szczecin": ("53.42", "14.55"),
    "Toruń": ("53.01", "18.61"), "Warszawa": ("52.23", "21.01"),
    "Wrocław": ("51.10", "17.03"), "Zielona Góra": ("51.93", "15.50")
}
CONFIG_PATH = os.path.expanduser("~/.config/redshift/redshift.conf")

class RedshiftLogic:
    """
    Klasa odpowiedzialna za logikę działania programu: obsługa konfiguracji, uruchamianie i resetowanie Redshift.
    """
    def __init__(self, config_path=CONFIG_PATH):
        self.config_path = config_path

    def load_config(self):
        """
        Wczytuje konfigurację z pliku.
        """
        config = configparser.ConfigParser()
        if not os.path.exists(self.config_path):
            return None
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config.read_file(f)
            return config
        except (OSError, configparser.Error) as e:
            print(f"Błąd podczas wczytywania konfiguracji: {e}")
            return None

    def save_config(self, redshift_data, manual_data):
        """
        Zapisuje konfigurację do pliku w kodowaniu UTF-8.
        """
        config = configparser.ConfigParser()
        config['redshift'] = redshift_data
        config['manual'] = manual_data
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as configfile:
                configfile.write("; Konfiguracja wygenerowana przez Kontroler Redshift\n")
                config.write(configfile)
            return True, None
        except OSError as e:
            return False, str(e)

    def run_redshift(self, cmd, background=False):
        """
        Uruchamia polecenie redshift.
        """
        try:
            if background:
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.run(cmd, check=True, capture_output=True, text=True)
            return True, None
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            return False, str(e)

    def kill_redshift(self):
        """
        Zatrzymuje wszystkie procesy redshift.
        """
        try:
            subprocess.run(["killall", "redshift"], stderr=subprocess.DEVNULL)
        except Exception:
            pass  # Brak procesu nie jest błędem krytycznym

    def kill_redshift_gtk(self):
        """
        Zatrzymuje redshift-gtk (na starcie programu).
        """
        try:
            subprocess.run(["killall", "redshift-gtk"], stderr=subprocess.DEVNULL)
        except Exception:
            pass

    @staticmethod
    def validate_float(value, min_val, max_val):
        """
        Waliduje wartość zmiennoprzecinkową.
        """
        try:
            val = float(value)
            if not (min_val <= val <= max_val):
                return False
            return True
        except ValueError:
            return False

    @staticmethod
    def validate_int(value, min_val, max_val):
        """
        Waliduje wartość całkowitą.
        """
        try:
            val = int(value)
            if not (min_val <= val <= max_val):
                return False
            return True
        except ValueError:
            return False

class RedshiftController(Gtk.Window):
    """
    Klasa odpowiedzialna za GUI i interakcję z użytkownikiem.
    """
    def __init__(self):
        Gtk.Window.__init__(self, title="Kontroler Redshift")
        self.set_border_width(15)
        self.set_default_size(500, 750)
        self.cities_data = POLISH_CITIES
        self.logic = RedshiftLogic()

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        self.add(vbox)

        # Tworzenie interfejsu
        self._create_auto_mode_section(vbox)
        self._create_manual_mode_section(vbox)
        self._create_action_buttons_section(vbox)
        self._create_status_section(vbox)
        self._create_config_save_section(vbox)

        self.load_config_on_startup()
        self.check_and_update_status()

    # --- Sekcja GUI ---

    def _create_auto_mode_section(self, parent_box):
        frame = Gtk.Frame(label=" Ustawienia Trybu Automatycznego ")
        parent_box.pack_start(frame, False, True, 0)
        grid = Gtk.Grid(column_spacing=6, row_spacing=10)
        grid.set_border_width(10)
        frame.add(grid)
        grid.attach(Gtk.Label(label="Wybierz miasto:"), 0, 0, 1, 1)
        self.combo_cities = Gtk.ComboBoxText()
        self.combo_cities.append_text("Wybierz z listy...")
        for city in sorted(self.cities_data.keys()):
            self.combo_cities.append_text(city)
        self.combo_cities.set_active(0)
        self.combo_cities.connect("changed", self.on_city_changed)
        grid.attach(self.combo_cities, 1, 0, 3, 1)
        grid.attach(Gtk.Label(label="Szerokość (LAT):"), 0, 1, 1, 1)
        self.entry_lat = Gtk.Entry()
        grid.attach(self.entry_lat, 1, 1, 3, 1)
        grid.attach(Gtk.Label(label="Długość (LON):"), 0, 2, 1, 1)
        self.entry_lon = Gtk.Entry()
        grid.attach(self.entry_lon, 1, 2, 3, 1)
        grid.attach(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), 0, 3, 4, 1)
        # Pola z przyciskami +/- (refaktoryzacja)
        self.entry_temp_day = self._create_adjustable_entry(grid, "Temp. dzień (K):", 4, "6500", -100, 100, False)
        self.entry_temp_night = self._create_adjustable_entry(grid, "Temp. noc (K):", 5, "4500", -100, 100, False)
        self.entry_bright_day = self._create_adjustable_entry(grid, "Jasność dzień:", 6, "1.0", -0.05, 0.05, True)
        self.entry_bright_night = self._create_adjustable_entry(grid, "Jasność noc:", 7, "1.0", -0.05, 0.05, True)
        btn_set_loc = Gtk.Button(label="Uruchom tryb automatyczny")
        btn_set_loc.connect("clicked", self.on_set_location)
        grid.attach(btn_set_loc, 0, 8, 4, 1)

    def _create_manual_mode_section(self, parent_box):
        frame = Gtk.Frame(label=" Kontrola Ręczna (Jednorazowy Efekt) ")
        parent_box.pack_start(frame, False, True, 0)
        grid = Gtk.Grid(column_spacing=10, row_spacing=10)
        grid.set_border_width(10)
        frame.add(grid)
        # Suwaki temperatury i jasności
        self.scale_temp = self._create_scale(grid, "Temperatura (K):", 0, 6500, 1000, 9000, 100, 0)
        self.scale_bright = self._create_scale(grid, "Jasność:", 1, 1.0, 0.1, 1.0, 0.05, 2)
        # Suwaki gamma
        self.scale_gamma_r = self._create_scale(grid, "Gamma Czerwony (R):", 2, 1.0, 0.1, 2.0, 0.01, 2)
        self.scale_gamma_g = self._create_scale(grid, "Gamma Zielony (G):", 3, 1.0, 0.1, 2.0, 0.01, 2)
        self.scale_gamma_b = self._create_scale(grid, "Gamma Niebieski (B):", 4, 1.0, 0.1, 2.0, 0.01, 2)

    def _create_action_buttons_section(self, parent_box):
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        parent_box.pack_start(hbox, False, True, 0)
        btn_reset = Gtk.Button(label="Resetuj / Wyłącz")
        btn_reset.get_style_context().add_class("destructive-action")
        btn_reset.connect("clicked", self.on_reset)
        btn_apply = Gtk.Button(label="Zastosuj ustawienia ręczne")
        btn_apply.connect("clicked", self.on_apply_manual)
        hbox.pack_start(btn_reset, True, True, 0)
        hbox.pack_start(btn_apply, True, True, 0)

    def _create_status_section(self, parent_box):
        frame = Gtk.Frame(label=" Aktualny Status Redshift ")
        parent_box.pack_start(frame, True, True, 0)
        self.status_label = Gtk.Label(label="Sprawdzanie statusu...")
        self.status_label.set_margin_top(10)
        self.status_label.set_margin_bottom(10)
        frame.add(self.status_label)

    def _create_config_save_section(self, parent_box):
        btn_save = Gtk.Button(label=f"Zapisz ustawienia w pliku ~/.config/redshift/redshift.conf")
        btn_save.connect("clicked", self.on_save_config_clicked)
        parent_box.pack_start(btn_save, False, True, 0)

    # --- Metody pomocnicze GUI ---

    def _create_adjustable_entry(self, grid, label, row, default_text, step_minus, step_plus, is_float):
        """
        Tworzy pole tekstowe z przyciskami +/- do regulacji wartości.
        """
        entry = Gtk.Entry()
        entry.set_text(default_text)
        btn_m = Gtk.Button(label="-")
        btn_p = Gtk.Button(label="+")
        btn_m.connect("clicked", lambda w: self._on_adjust_button_clicked(entry, step_minus, is_float))
        btn_p.connect("clicked", lambda w: self._on_adjust_button_clicked(entry, step_plus, is_float))
        grid.attach(Gtk.Label(label=label), 0, row, 1, 1)
        grid.attach(entry, 1, row, 1, 1)
        grid.attach(btn_m, 2, row, 1, 1)
        grid.attach(btn_p, 3, row, 1, 1)
        return entry

    def _create_scale(self, grid, label, row, value, lower, upper, step, digits):
        """
        Tworzy suwak do regulacji wartości liczbowych.
        """
        adj = Gtk.Adjustment(value=value, lower=lower, upper=upper, step_increment=step, page_increment=step*2, page_size=0)
        scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=adj)
        scale.set_digits(digits)
        scale.set_hexpand(True)
        grid.attach(Gtk.Label(label=label), 0, row, 1, 1)
        grid.attach(scale, 1, row, 1, 1)
        return scale

    def _on_adjust_button_clicked(self, entry_widget, step, is_float=False):
        """
        Obsługuje kliknięcia przycisków +/- przy polach tekstowych.
        """
        try:
            val = float(entry_widget.get_text()) if is_float else int(entry_widget.get_text())
            new_val = val + step
            if is_float:
                entry_widget.set_text(f"{max(0.1, min(1.0, new_val)):.2f}")
            else:
                entry_widget.set_text(str(max(1000, min(25000, new_val))))
        except ValueError:
            entry_widget.set_text("1.0" if is_float else "6500")

    # --- Logika aplikacji ---

    def load_config_on_startup(self):
        """
        Wczytuje konfigurację przy starcie programu.
        """
        config = self.logic.load_config()
        if not config:
            return
        if 'redshift' in config:
            self.entry_temp_day.set_text(config.get('redshift', 'temp-day', fallback='6500'))
            self.entry_temp_night.set_text(config.get('redshift', 'temp-night', fallback='4500'))
            self.entry_bright_day.set_text(config.get('redshift', 'brightness-day', fallback='1.0'))
            self.entry_bright_night.set_text(config.get('redshift', 'brightness-night', fallback='1.0'))
            gamma_str = config.get('redshift', 'gamma', fallback='1.0:1.0:1.0')
            try:
                r, g, b = map(float, gamma_str.split(':'))
                self.scale_gamma_r.get_adjustment().set_value(r)
                self.scale_gamma_g.get_adjustment().set_value(g)
                self.scale_gamma_b.get_adjustment().set_value(b)
            except (ValueError, IndexError):
                print(f"Ostrzeżenie: nieprawidłowy format gamma w pliku konfiguracyjnym: {gamma_str}")
        if 'manual' in config:
            self.entry_lat.set_text(config.get('manual', 'lat', fallback=''))
            self.entry_lon.set_text(config.get('manual', 'lon', fallback=''))

    def on_save_config_clicked(self, widget):
        """
        Zapisuje konfigurację do pliku.
        """
        gamma_r = self.scale_gamma_r.get_value()
        gamma_g = self.scale_gamma_g.get_value()
        gamma_b = self.scale_gamma_b.get_value()
        redshift_data = {
            'temp-day': self.entry_temp_day.get_text(),
            'temp-night': self.entry_temp_night.get_text(),
            'brightness-day': self.entry_bright_day.get_text(),
            'brightness-night': self.entry_bright_night.get_text(),
            'gamma': f'{gamma_r:.2f}:{gamma_g:.2f}:{gamma_b:.2f}',
            'location-provider': 'manual'
        }
        manual_data = {
            'lat': self.entry_lat.get_text(),
            'lon': self.entry_lon.get_text()
        }
        success, error = self.logic.save_config(redshift_data, manual_data)
        if success:
            self.show_info_dialog("Sukces!", f"Konfiguracja została zapisana w pliku:\n{CONFIG_PATH}")
        else:
            self.show_error_dialog(f"Nie udało się zapisać pliku konfiguracyjnego.\nBłąd: {error}")

    def on_apply_manual(self, widget):
        """
        Zastosowanie ustawień ręcznych (jednorazowy efekt).
        """
        self.logic.kill_redshift()
        time.sleep(0.2)
        temp = int(self.scale_temp.get_value())
        bright = round(self.scale_bright.get_value(), 2)
        gamma_r = round(self.scale_gamma_r.get_value(), 2)
        gamma_g = round(self.scale_gamma_g.get_value(), 2)
        gamma_b = round(self.scale_gamma_b.get_value(), 2)
        gamma_str = f"{gamma_r}:{gamma_g}:{gamma_b}"
        command = ["redshift", "-P", "-O", str(temp), "-b", str(bright), "-g", gamma_str]
        success, error = self.logic.run_redshift(command)
        if success:
            self.status_label.set_markup(
                f"<b>Zastosowano ustawienia ręczne (jednorazowy efekt)</b>\n"
                f"Temperatura: {temp}K, Jasność: {bright}\n"
                f"Gamma (R:G:B): {gamma_str}"
            )
        else:
            self.show_error_dialog(f"Błąd uruchamiania redshift: {error}")

    def on_reset(self, widget):
        """
        Resetuje ustawienia i wyłącza redshift.
        """
        self.logic.kill_redshift()
        self.logic.run_redshift(["redshift", "-x"])
        self.scale_temp.get_adjustment().set_value(6500)
        self.scale_bright.get_adjustment().set_value(1.0)
        self.scale_gamma_r.get_adjustment().set_value(1.0)
        self.scale_gamma_g.get_adjustment().set_value(1.0)
        self.scale_gamma_b.get_adjustment().set_value(1.0)
        self.check_and_update_status()

    def check_and_update_status(self):
        """
        Sprawdza status działania redshift (niezmienione).
        """
        try:
            result = subprocess.run(["pgrep", "-a", "redshift"], capture_output=True, text=True)
            if result.returncode == 0:
                cmd_line = result.stdout.strip()
                pid = cmd_line.split()[0]
                loc_match = re.search(r'-l\s+([\d.-]+):([\d.-]+)', cmd_line)
                temp_match = re.search(r'-t\s+(\d+):(\d+)', cmd_line)
                bright_match = re.search(r'-b\s+([\d.]+):([\d.]+)', cmd_line)
                if loc_match and temp_match and bright_match:
                    lat, lon = loc_match.groups()
                    t_day, t_night = temp_match.groups()
                    b_day, b_night = bright_match.groups()
                    status_text = (
                        f"<b>Tryb automatyczny aktywny (PID: {pid})</b>\n"
                        f"Lokalizacja: {lat}, {lon}\n"
                        f"Temp (Dzień/Noc): {t_day}K / {t_night}K\n"
                        f"Jasność (Dzień/Noc): {b_day} / {b_night}"
                    )
                    self.entry_lat.set_text(lat)
                    self.entry_lon.set_text(lon)
                    self.entry_temp_day.set_text(t_day)
                    self.entry_temp_night.set_text(t_night)
                    self.entry_bright_day.set_text(b_day)
                    self.entry_bright_night.set_text(b_night)
                    self.status_label.set_markup(status_text)
                    return
                else:
                    parts = cmd_line.split()
                    arguments = " ".join(parts[2:]) if len(parts) > 2 else "tryb domyślny (geolokalizacja)"
                    self.status_label.set_markup(f"<b>Redshift działa (PID: {pid})</b>\nUruchomiony z opcjami:\n<tt>{arguments}</tt>")
            else:
                self.status_label.set_text("Redshift nie jest uruchomiony.")
        except Exception as e:
            self.status_label.set_text(f"Błąd podczas sprawdzania statusu: {e}")

    def on_set_location(self, widget):
        """
        Uruchamia redshift w trybie automatycznym na podstawie wprowadzonych danych.
        """
        try:
            values = [w.get_text() for w in [
                self.entry_lat, self.entry_lon, self.entry_temp_day,
                self.entry_temp_night, self.entry_bright_day, self.entry_bright_night
            ]]
            if not all(values):
                self.show_error_dialog("Wszystkie pola trybu auto muszą być wypełnione.")
                return
            lat, lon, t_day, t_night, b_day, b_night = values
            # Walidacja danych wejściowych
            if not (self.logic.validate_float(lat, -90, 90) and self.logic.validate_float(lon, -180, 180)):
                self.show_error_dialog("Nieprawidłowe współrzędne geograficzne.")
                return
            if not (self.logic.validate_int(t_day, 1000, 25000) and self.logic.validate_int(t_night, 1000, 25000)):
                self.show_error_dialog("Temperatura powinna być liczbą z zakresu 1000-25000.")
                return
            if not (self.logic.validate_float(b_day, 0.1, 1.0) and self.logic.validate_float(b_night, 0.1, 1.0)):
                self.show_error_dialog("Jasność powinna być liczbą z zakresu 0.1-1.0.")
                return
        except Exception as e:
            self.show_error_dialog(f"Błąd odczytu danych: {e}")
            return
        self.logic.kill_redshift()
        time.sleep(0.2)
        cmd = [
            "redshift", "-l", f"{lat}:{lon}", "-t", f"{t_day}:{t_night}", "-b", f"{b_day}:{b_night}"
        ]
        self.logic.run_redshift(cmd, background=True)
        self.status_label.set_text("Uruchamianie trybu auto...")
        time.sleep(0.5)
        self.check_and_update_status()

    def on_city_changed(self, widget):
        """
        Ustawia współrzędne po wyborze miasta.
        """
        coords = self.cities_data.get(widget.get_active_text())
        if coords:
            self.entry_lat.set_text(coords[0])
            self.entry_lon.set_text(coords[1])

    # --- Dialogi ---

    def show_error_dialog(self, message):
        """
        Wyświetla okno dialogowe z błędem.
        """
        dialog = Gtk.MessageDialog(
            transient_for=self, flags=0, message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK, text="Wystąpił błąd"
        )
        dialog.format_secondary_text(str(message))
        dialog.run()
        dialog.destroy()

    def show_info_dialog(self, title, message):
        """
        Wyświetla okno dialogowe z informacją.
        """
        dialog = Gtk.MessageDialog(
            transient_for=self, flags=0, message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK, text=title
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()

if __name__ == "__main__":
    RedshiftLogic().kill_redshift_gtk()
    win = RedshiftController()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
