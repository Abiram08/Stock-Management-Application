import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PySide6.QtWidgets import QWidget, QVBoxLayout

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        # Configure modern fonts
        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['font.sans-serif'] = ['Inter', 'Segoe UI', 'Arial']
        
        self.fig, self.ax = plt.subplots(figsize=(width, height), dpi=dpi, facecolor='none')
        super(MplCanvas, self).__init__(self.fig)
        self.fig.patch.set_alpha(0)
        self.ax.set_facecolor('none')
        self.fig.tight_layout(pad=0.5)

class ChartWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0,0,0,0)
        self.canvas = MplCanvas(self)
        self.layout.addWidget(self.canvas)
        
        # Tooltip annotation
        self.annot = self.canvas.ax.annotate("", xy=(0,0), xytext=(10,10),
                                            textcoords="offset points",
                                            bbox=dict(boxstyle="round", fc="white", ec="#e2e8f0", alpha=0.9),
                                            arrowprops=dict(arrowstyle="->", color='#64748b'))
        self.annot.set_visible(False)
        self.canvas.mpl_connect("motion_notify_event", self._on_hover)

    def _on_hover(self, event):
        vis = self.annot.get_visible()
        if event.inaxes == self.canvas.ax:
            for line in self.canvas.ax.get_lines():
                cont, ind = line.contains(event)
                if cont:
                    pos = line.get_offsets()[ind["ind"][0]] if hasattr(line, 'get_offsets') else line.get_data()
                    x_idx = ind["ind"][0]
                    x_data = line.get_xdata()[x_idx]
                    y_data = line.get_ydata()[x_idx]
                    
                    self.annot.xy = (x_data, y_data)
                    text = f"{x_data}\n₹{y_data:,.0f}"
                    self.annot.set_text(text)
                    self.annot.set_visible(True)
                    self.canvas.draw_idle()
                    return
        if vis:
            self.annot.set_visible(False)
            self.canvas.draw_idle()

    def draw_bar(self, labels, values, title, color='#6366f1'):
        self.canvas.ax.clear()
        # Reset annotation after clear
        self.annot = self.canvas.ax.annotate("", xy=(0,0), xytext=(0,10),
                                            textcoords="offset points",
                                            ha='center',
                                            bbox=dict(boxstyle="round", fc="white", ec="#e2e8f0", alpha=0.9),
                                            fontsize=8, fontweight='bold')
        self.annot.set_visible(False)
        
        bars = self.canvas.ax.bar(labels, values, color=color, alpha=0.8, width=0.6)
        self.canvas.ax.set_title(title, color='#475569', fontsize=10, fontweight='bold', pad=15)
        self.canvas.ax.tick_params(colors='#64748b', labelsize=8)
        
        # Rotate labels to prevent overlap
        plt.setp(self.canvas.ax.get_xticklabels(), rotation=45, ha='right')
        
        # Add headroom for tooltips
        if values:
            max_val = max(values)
            self.canvas.ax.set_ylim(0, max_val * 1.25)
        
        for spine in self.canvas.ax.spines.values():
            spine.set_visible(False)
            
        self.canvas.ax.yaxis.grid(True, linestyle='--', alpha=0.2, color='#64748b')
        self.canvas.fig.tight_layout(pad=2.0)
        self.canvas.draw()

    def draw_line(self, x, y, title, color='#8b5cf6'):
        self.canvas.ax.clear()
        # Reset annotation after clear
        self.annot = self.canvas.ax.annotate("", xy=(0,0), xytext=(0,10),
                                            textcoords="offset points",
                                            ha='center',
                                            bbox=dict(boxstyle="round", fc="white", ec="#e2e8f0", alpha=0.9, pad=0.5),
                                            fontsize=8, color='#1e293b', fontweight='bold')
        self.annot.set_visible(False)

        self.canvas.ax.plot(x, y, marker='o', markersize=6, color=color, 
                          linewidth=2, antialiased=True, picker=True, pickradius=5)
        self.canvas.ax.fill_between(x, y, color=color, alpha=0.1)
        
        self.canvas.ax.set_title(title, color='#475569', fontsize=10, fontweight='bold', pad=15)
        self.canvas.ax.tick_params(colors='#64748b', labelsize=8)
        
        # Rotate labels to prevent overlap
        plt.setp(self.canvas.ax.get_xticklabels(), rotation=45, ha='right')
        
        # Add headroom for tooltips
        if y:
            max_val = max(y)
            self.canvas.ax.set_ylim(0, max_val * 1.25)

        for spine in self.canvas.ax.spines.values():
            spine.set_visible(False)
            
        self.canvas.ax.yaxis.grid(True, linestyle='--', alpha=0.2, color='#64748b')
        self.canvas.fig.tight_layout(pad=2.0)
        self.canvas.draw()

    def draw_pie(self, labels, values, title):
        self.canvas.ax.clear()

        # Handle empty data or zero sum
        if not values or sum(values) == 0:
            self.canvas.ax.text(0.5, 0.5, 'No Data Available', 
                                horizontalalignment='center',
                                verticalalignment='center',
                                transform=self.canvas.ax.transAxes,
                                color='#94a3b8', fontsize=12, style='italic')
            self.canvas.ax.set_title(title, color='#475569', fontsize=10, fontweight='bold', pad=20)
            self.canvas.draw()
            return

        # Modern, vibrant palette
        colors = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']
        
        # Use white for autopct (percentages) to contrast with slices
        # Use dark slate for labels 
        wedges, texts, autotexts = self.canvas.ax.pie(
            values, labels=labels, autopct='%1.1f%%', 
            colors=colors, startangle=140, 
            textprops={'color': "#1e293b", 'fontsize': 9, 'fontweight': 'bold'},
            wedgeprops={'alpha': 0.8, 'edgecolor': 'white', 'linewidth': 1.5},
            pctdistance=0.75,
            labeldistance=1.1
        )
        
        # Explicitly set percentage text to white for high contrast
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(9)
            
        self.canvas.ax.set_title(title, color='#475569', fontsize=10, fontweight='bold', pad=20)
        self.canvas.draw()
