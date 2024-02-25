import tkinter as tk
from tkinter import filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import numpy as np
import sys
import os


def normalize(value, min_range, max_range):
    normalized_values = [(v - min_range) / (max_range - min_range) for v in value]
    return normalized_values


class MatplotlibTkinterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Detrender")
        self.individual_points_var = tk.BooleanVar(value=False)
        self.x_range_var = tk.BooleanVar(value=False)
        self.x_normalized = []
        self.y_normalized = []
        self.removed = []
        self.original_data = []
        self.click_count = 0
        self.first_click = 0
        self.second_click = 0
        self.out_path = ''
        self.create_widgets()

        if len(sys.argv) == 2:
            if "=" not in sys.argv[1]:
                file_path = sys.argv[1]
                if file_path:
                    self.plot_data(file_path)
                    self.file_name = os.path.basename(file_path)
            if "=" in sys.argv[1]:
                self.out_path = sys.argv[1].split("=")[1]

        if len(sys.argv) == 3:
            for arg in sys.argv[1:]:
                print(arg)
                if "=" not in arg:
                    print('should be file path')
                    file_path = arg
                    if file_path:
                        self.plot_data(file_path)
                        self.file_name = os.path.basename(file_path)
                if "=" in arg:
                    print('should be out file')
                    self.out_path = arg.split("=")[1]

    def create_widgets(self):
        # Create a Matplotlib figure and axis
        self.figure, self.ax = plt.subplots(figsize=(10, 8), tight_layout=True)

        # Canvas to display the plot
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.root)
        self.canvas.get_tk_widget().pack(pady=10)

        # Matplotlib navigation toolbar
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.root)
        self.toolbar.update()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Buttons
        self.button_load = tk.Button(self.root, text="Load", command=self.load_data)
        self.button_load.pack(side=tk.LEFT, padx=10)
        self.button_save = tk.Button(self.root, text="Save", command=self.save_files)
        self.button_save.pack(side=tk.LEFT)
        self.polynomial_degree = tk.Label(self.root, text="Polynomial degree:")
        self.poly_degree_entry = tk.Entry(self.root, width=5)
        self.polynomial_degree.pack(side=tk.LEFT, padx=10)
        self.poly_degree_entry.pack(side=tk.LEFT, padx=10)
        self.button_poly = tk.Button(self.root, text="Fit polynomial", command=self.fit_poly)
        self.button_poly.pack(side=tk.LEFT)
        self.button_poly_subtract = tk.Button(self.root, text="Subtract polynomial",
                                              command=self.subtract_poly)
        self.button_poly_subtract.pack(side=tk.LEFT)
        self.button_remove_individual = tk.Checkbutton(self.root, text="Remove individual points",
                                                       variable=self.individual_points_var,
                                                       command=self.update_checkbuttons)
        self.button_remove_individual.pack(side=tk.LEFT)
        self.button_remove_individual = tk.Checkbutton(self.root, text="Remove x range",
                                                       variable=self.x_range_var,
                                                       command=self.update_checkbuttons)
        self.button_remove_individual.pack(side=tk.LEFT)
        self.button_restore = tk.Button(self.root, text="Restore original",
                                        command=self.restore_original_data)
        self.button_restore.pack(side=tk.LEFT)
        self.canvas.mpl_connect('button_press_event', self.on_canvas_click)
        self.canvas.draw()

    def load_data(self):
        self.removed = []
        file_path = filedialog.askopenfilename(title="Select a file",
                                               filetypes=[("Dat files", "*.dat"),
                                                          ("Text files", "*.txt"),
                                                          ("All files", "*.*")])
        self.file_name = os.path.basename(file_path)
        if file_path:
            self.plot_data(file_path)

    def restore_original_data(self):
        self.data = self.original_data.copy()
        self.removed = []
        self.ax.clear()
        self.ax.scatter(self.data[:, 0], self.data[:, 1], label="Data")
        self.ax.set_xlim(self.ax.get_xlim())
        self.ax.set_ylim(self.ax.get_ylim())
        self.canvas.draw()

        self.x_normalized = normalize(self.data[:, 0], self.ax.get_xlim()[0],
                                      self.ax.get_xlim()[1])
        self.y_normalized = normalize(self.data[:, 1], self.ax.get_ylim()[0],
                                      self.ax.get_ylim()[1])

    def plot_data(self, file_path):
        self.data = np.loadtxt(file_path)
        self.file_name = os.path.basename(file_path)
        self.root.title("Detrender: "+self.file_name)
        print(len(self.data))
        self.original_data = np.loadtxt(file_path)
        self.ax.clear()
        self.ax.scatter(self.data[:, 0], self.data[:, 1], label="Data")
        self.ax.set_xlim(self.ax.get_xlim())
        self.ax.set_ylim(self.ax.get_ylim())
        self.canvas.draw()

        self.x_normalized = normalize(self.data[:, 0], self.ax.get_xlim()[0],
                                      self.ax.get_xlim()[1])
        self.y_normalized = normalize(self.data[:, 1], self.ax.get_ylim()[0],
                                      self.ax.get_ylim()[1])

    def save_files(self):
        np.savetxt(os.path.join(self.out_path, self.file_name) + "_data", self.data,
                   delimiter=' ', fmt='%f')
        if len(self.removed) > 0:
            np.savetxt(os.path.join(self.out_path, self.file_name) + "_removed", self.removed,
                       delimiter=' ', fmt='%f')
        if hasattr(self, 'fitted_poly_line'):
            print(self.fitted_poly_coefficients)
            polynomial_order = int(self.poly_degree_entry.get())
            header_text = f"Polynomial coefficients and the first element corresponds to the " \
                          f"coefficient of the highest-degree term \n " \
                          f"Polynomial order: {polynomial_order}"
            np.savetxt(os.path.join(self.out_path, self.file_name) + "_polynomial",
                       self.fitted_poly_coefficients, header=header_text, comments='#',
                       delimiter=' ')
        exit()

    def update_checkbuttons(self):
        # Ensure that only one option is selected at a time
        if self.individual_points_var.get():
            self.x_range_var.set(False)
        if self.x_range_var.get():
            self.individual_points_var.set(False)

    def fit_poly(self):
        if len(self.data) < int(self.poly_degree_entry.get()) + 1:
            print("Not enough remaining points to fit a polynomial.")
            return

        degree = int(self.poly_degree_entry.get())
        coefficients = np.polyfit(self.data[:, 0], self.data[:, 1], degree)
        self.fitted_poly_coefficients = coefficients  # Store coefficients in the attribute

        if hasattr(self, 'fitted_poly_line'):
            self.fitted_poly_line.set_visible(False)

        x_values = np.linspace(min(self.data[:, 0]), max(self.data[:, 0]), 100)
        y_values = np.polyval(coefficients, x_values)
        self.fitted_poly_line, = self.ax.plot(x_values, y_values,
                                              label=f'Fitted Polynomial (Degree {degree})',
                                              color='green')
        print(self.fitted_poly_coefficients)
        self.canvas.draw()

    def subtract_poly(self):
        # Check if a polynomial has been fitted
        if not hasattr(self, 'fitted_poly_coefficients'):
            print("Please fit a polynomial first.")
            return

        x_values = self.data[:, 0]
        fitted_y_values = np.polyval(self.fitted_poly_coefficients, x_values)
        self.data[:, 1] -= fitted_y_values

        if len(self.removed) > 0:
            fitted_y_values_removed = np.polyval(self.fitted_poly_coefficients, self.removed[:, 0])
            self.removed[:, 1] -= fitted_y_values_removed

        self.update_plot()
        self.fitted_poly_line.set_visible(False)
        print("Polynomial subtracted from the data.")

    def on_canvas_click(self, event):
        if (not self.toolbar.mode):
            if event.button == 1:
                clicked_point = self.ax.transAxes.inverted().transform([(event.x, event.y)])[0]
            if event.button == 1 and self.individual_points_var.get():
                self.remove_point(clicked_point)
            if event.button == 3 and self.individual_points_var.get():
                self.removed = []
                self.ax.clear()
                self.ax.scatter(self.data[:, 0], self.data[:, 1], label="Data")
                self.ax.set_xlim(self.ax.get_xlim())
                self.ax.set_ylim(self.ax.get_ylim())
                self.canvas.draw()
            if event.button == 1 and self.x_range_var.get():
                self.click_count += 1
                if self.click_count % 2 == 1:
                    self.first_click = event.xdata
                    self.ax.axvline(self.first_click, c='lime')
                    self.canvas.draw()
                if self.click_count % 2 == 0:
                    self.second_click = event.xdata
                    self.ax.axvline(self.second_click, c='lime')
                    self.canvas.draw()
                    self.remove_points()

    def remove_points(self):
        xdata = self.data[:, 0]
        filtr = (xdata < self.first_click) | (xdata > self.second_click)
        filtr2 = ~filtr

        if len(self.removed) > 0:
            self.removed = np.concatenate((self.removed, self.data[filtr2]))
        else:
            self.removed = self.data[filtr2].copy()

        print(self.removed)
        self.data = np.delete(self.data, filtr2, 0)
        self.update_plot()

    def update_plot(self):
        self.ax.clear()
        self.ax.scatter(self.data[:, 0], self.data[:, 1], label="Data")
        if len(self.removed) > 0:
            self.ax.scatter(self.removed[:, 0], self.removed[:, 1], c='red', label="Removed")
        self.ax.set_xlim(self.ax.get_xlim())
        self.ax.set_ylim(self.ax.get_ylim())
        self.canvas.draw()

    def remove_point(self, clicked):
        x_clicked = clicked[0]
        y_clicked = clicked[1]

        self.x_normalized = normalize(self.data[:, 0], self.ax.get_xlim()[0],
                                      self.ax.get_xlim()[1])
        self.y_normalized = normalize(self.data[:, 1], self.ax.get_ylim()[0],
                                      self.ax.get_ylim()[1])

        closest_point_index = np.argmin(np.sqrt((self.x_normalized - x_clicked)**2 +
                                                (self.y_normalized - y_clicked)**2))
        closest_point = self.data[closest_point_index]

        if len(self.removed) > 0:
            self.removed = np.concatenate((self.removed, [closest_point]))
        else:
            self.removed.append(self.data[closest_point_index])

        self.data = np.delete(self.data, closest_point_index, 0)
        print(self.removed)
        self.ax.scatter(closest_point[0], closest_point[1], label="Selected Point", color='red')
        self.canvas.draw()


if __name__ == "__main__":
    root = tk.Tk()
    app = MatplotlibTkinterApp(root)
    root.geometry("1100x900")
    root.mainloop()
