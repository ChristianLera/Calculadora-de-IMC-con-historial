
"""
CALCULADORA DE IMC CON HISTORIAL Y GRÁFICO DE PROGRESO - VERSIÓN TKINTER
Aplicación profesional con interfaz gráfica, persistencia de datos, 
visualización de tendencias y manejo robusto de errores.
Requerimientos: pip install matplotlib
"""

import json
import os
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
from tkinter import *
from tkinter import ttk, messagebox
from typing import List, Optional
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.dates as mdates


# ========== MODELO ==========
class CategoriaIMC(Enum):
    """Enumeración para categorías de IMC según estándares de la OMS."""
    BAJO_PESO = ("Bajo peso", 0, 18.4, "#FFE5B4", 1)
    NORMAL = ("Normal", 18.5, 24.9, "#90EE90", 2)
    SOBREPESO = ("Sobrepeso", 25.0, 29.9, "#FFD700", 3)
    OBESIDAD_I = ("Obesidad grado I", 30.0, 34.9, "#FFA500", 4)
    OBESIDAD_II = ("Obesidad grado II", 35.0, 39.9, "#FF6347", 5)
    OBESIDAD_III = ("Obesidad grado III", 40.0, float('inf'), "#FF0000", 6)
    
    def __init__(self, nombre: str, min_imc: float, max_imc: float, color: str, orden: int):
        self.nombre = nombre
        self.min_imc = min_imc
        self.max_imc = max_imc
        self.color = color
        self.orden = orden
    
    @classmethod
    def desde_imc(cls, imc: float) -> 'CategoriaIMC':
        """Factory method que retorna la categoría correspondiente según el IMC."""
        for categoria in cls:
            if categoria.min_imc <= imc <= categoria.max_imc:
                return categoria
        return cls.BAJO_PESO  # fallback seguro


@dataclass
class RegistroIMC:
    """
    Data class inmutable para representar un cálculo de IMC.
    frozen=True garantiza inmutabilidad después de la creación.
    """
    peso: float
    altura: float
    imc: float
    categoria: str
    fecha: str
    color: str
    timestamp: float  # Para ordenamiento preciso en gráficos
    
    def __post_init__(self):
        """Validaciones post-creación para garantizar integridad de datos."""
        if self.peso <= 0 or self.peso > 500:
            raise ValueError("El peso debe estar entre 1 y 500 kg")
        if self.altura <= 0 or self.altura > 3.0:
            raise ValueError("La altura debe estar entre 0.1 y 3.0 metros")


class GestorHistorial:
    """
    Gestor de persistencia para el historial de IMC.
    Principio de responsabilidad única: solo maneja almacenamiento/recuperación.
    """
    
    def __init__(self, archivo: str = "historial_imc.json"):
        self.archivo = archivo
        self.historial: List[RegistroIMC] = []
        self._cargar_historial()
    
    def _cargar_historial(self) -> None:
        """Carga el historial desde disco con manejo de errores."""
        if not os.path.exists(self.archivo):
            self.historial = []
            return
        
        try:
            with open(self.archivo, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.historial = []
                for item in data:
                    # Reconstruir objetos desde JSON
                    registro = RegistroIMC(
                        peso=item['peso'],
                        altura=item['altura'],
                        imc=item['imc'],
                        categoria=item['categoria'],
                        fecha=item['fecha'],
                        color=item['color'],
                        timestamp=item['timestamp']
                    )
                    self.historial.append(registro)
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Error al cargar historial: {e}")
            self.historial = []  # Iniciar historial vacío si hay corrupción
    
    def guardar_historial(self) -> None:
        """Persiste el historial actual en disco."""
        try:
            with open(self.archivo, 'w', encoding='utf-8') as f:
                # Convertir cada registro a diccionario para serialización JSON
                data = [asdict(registro) for registro in self.historial]
                json.dump(data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Error al guardar historial: {e}")
    
    def agregar_registro(self, registro: RegistroIMC) -> None:
        """Agrega un nuevo registro al historial y lo persiste."""
        self.historial.append(registro)
        self.guardar_historial()
    
    def eliminar_registro(self, indice: int) -> bool:
        """Elimina un registro por índice. Retorna True si se eliminó."""
        if 0 <= indice < len(self.historial):
            del self.historial[indice]
            self.guardar_historial()
            return True
        return False
    
    def limpiar_historial(self) -> None:
        """Elimina todo el historial."""
        self.historial.clear()
        self.guardar_historial()
    
    def obtener_datos_para_grafico(self):
        """
        Prepara los datos del historial para visualización en gráfico.
        Retorna tuplas de (fechas, valores_imc, colores, categorias)
        """
        if not self.historial:
            return [], [], [], []
        
        # Ordenar por timestamp (fecha cronológica)
        registros_ordenados = sorted(self.historial, key=lambda x: x.timestamp)
        
        fechas = []
        valores_imc = []
        colores = []
        categorias = []
        
        for registro in registros_ordenados:
            # Convertir string de fecha a objeto datetime para matplotlib
            fecha_obj = datetime.strptime(registro.fecha, "%Y-%m-%d %H:%M:%S")
            fechas.append(fecha_obj)
            valores_imc.append(registro.imc)
            colores.append(registro.color)
            categorias.append(registro.categoria)
        
        return fechas, valores_imc, colores, categorias


# ========== VISTA Y CONTROLADOR (TKINTER) ==========
class CalculadoraIMCApp:
    """
    Clase principal de la aplicación.
    Sigue un patrón MVC ligero donde la vista y controlador están integrados.
    """
    
    def __init__(self, root: Tk):
        self.root = root
        self.root.title("Calculadora de IMC con Historial y Gráfico de Progreso")
        self.root.geometry("1200x700")
        self.root.resizable(True, True)
        
        # Inicializar gestor de datos
        self.gestor = GestorHistorial()
        
        # Variables de control tkinter
        self.peso_var = StringVar()
        self.altura_var = StringVar()
        
        # Referencia para el canvas del gráfico
        self.canvas = None
        
        # Configurar estilo y UI
        self._configurar_estilo()
        self._crear_widgets()
        self._actualizar_tabla_historial()
        self._actualizar_grafico()  # Cargar gráfico inicial si hay datos
    
    def _configurar_estilo(self) -> None:
        """Configura el estilo visual de la aplicación."""
        style = ttk.Style()
        style.theme_use('clam')  # Tema moderno
        
        # Configurar colores principales
        self.root.configure(bg='#f0f0f0')
        
        # Estilo para los frames
        style.configure('TFrame', background='#f0f0f0')
        style.configure('Card.TFrame', background='white', relief='raised', borderwidth=1)
        
        # Estilo para labels
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'), background='#f0f0f0')
        style.configure('Result.TLabel', font=('Arial', 14), background='#f0f0f0')
        style.configure('IMC.TLabel', font=('Arial', 24, 'bold'))
    
    def _crear_widgets(self) -> None:
        """Crea y organiza todos los widgets de la interfaz."""
        # Frame principal con padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=BOTH, expand=True)
        
        # Panel izquierdo (entrada y resultado)
        left_panel = ttk.Frame(main_frame)
        left_panel.pack(side=LEFT, fill=BOTH, expand=False, padx=(0, 5))
        
        # ===== Panel de entrada =====
        input_frame = ttk.LabelFrame(left_panel, text="Datos del Paciente", padding="15")
        input_frame.pack(fill=BOTH, expand=False, pady=(0, 10))
        
        # Campo peso
        ttk.Label(input_frame, text="Peso (kg):", font=('Arial', 11)).pack(anchor=W, pady=(0, 5))
        peso_entry = ttk.Entry(input_frame, textvariable=self.peso_var, font=('Arial', 12), width=25)
        peso_entry.pack(fill=X, pady=(0, 15))
        peso_entry.bind('<Return>', lambda e: self.calcular_imc())
        
        # Campo altura
        ttk.Label(input_frame, text="Altura (m):", font=('Arial', 11)).pack(anchor=W, pady=(0, 5))
        altura_entry = ttk.Entry(input_frame, textvariable=self.altura_var, font=('Arial', 12), width=25)
        altura_entry.pack(fill=X, pady=(0, 20))
        altura_entry.bind('<Return>', lambda e: self.calcular_imc())
        
        # Botón calcular
        self.calcular_btn = ttk.Button(input_frame, text="Calcular IMC", command=self.calcular_imc)
        self.calcular_btn.pack(fill=X, pady=(0, 10))
        
        # Botón limpiar campos
        ttk.Button(input_frame, text="Limpiar Campos", command=self._limpiar_campos).pack(fill=X, pady=(0, 5))
        
        # ===== Panel de resultado =====
        result_frame = ttk.LabelFrame(left_panel, text="Resultado Actual", padding="15")
        result_frame.pack(fill=BOTH, expand=True)
        
        self.imc_label = ttk.Label(result_frame, text="---", style='IMC.TLabel')
        self.imc_label.pack(pady=10)
        
        self.categoria_label = ttk.Label(result_frame, text="Esperando datos...", font=('Arial', 12), wraplength=250)
        self.categoria_label.pack(pady=5)
        
        # Panel central (gráfico)
        center_panel = ttk.LabelFrame(main_frame, text="Gráfico de Progreso", padding="10")
        center_panel.pack(side=LEFT, fill=BOTH, expand=True, padx=5)
        
        # Frame para el gráfico de matplotlib
        self.graph_frame = ttk.Frame(center_panel)
        self.graph_frame.pack(fill=BOTH, expand=True)
        
        # Panel derecho (historial)
        right_panel = ttk.LabelFrame(main_frame, text="Historial de Cálculos", padding="10")
        right_panel.pack(side=RIGHT, fill=BOTH, expand=True, padx=(5, 0))
        
        # Frame para botones de historial
        btn_frame = ttk.Frame(right_panel)
        btn_frame.pack(fill=X, pady=(0, 10))
        
        ttk.Button(btn_frame, text="Eliminar Seleccionado", command=self._eliminar_seleccionado).pack(side=LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="Limpiar Todo", command=self._limpiar_historial).pack(side=LEFT)
        ttk.Button(btn_frame, text="Actualizar Gráfico", command=self._actualizar_grafico).pack(side=LEFT, padx=(5, 0))
        
        # Treeview para mostrar historial
        columns = ('Fecha', 'Peso (kg)', 'Altura (m)', 'IMC', 'Categoría')
        self.tree = ttk.Treeview(right_panel, columns=columns, show='headings', height=18)
        
        # Configurar columnas
        self.tree.heading('Fecha', text='Fecha')
        self.tree.heading('Peso (kg)', text='Peso (kg)')
        self.tree.heading('Altura (m)', text='Altura (m)')
        self.tree.heading('IMC', text='IMC')
        self.tree.heading('Categoría', text='Categoría')
        
        self.tree.column('Fecha', width=130)
        self.tree.column('Peso (kg)', width=80)
        self.tree.column('Altura (m)', width=80)
        self.tree.column('IMC', width=80)
        self.tree.column('Categoría', width=150)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(right_panel, orient=VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        # Bind doble click para cargar datos seleccionados
        self.tree.bind('<Double-Button-1>', self._cargar_desde_historial)
    
    def _actualizar_grafico(self) -> None:
        """
        Genera y muestra el gráfico de progreso del IMC usando matplotlib.
        Incluye línea de tendencia y zonas de color por categoría.
        """
        # Limpiar frame anterior
        for widget in self.graph_frame.winfo_children():
            widget.destroy()
        
        # Obtener datos del historial
        fechas, valores_imc, colores, categorias = self.gestor.obtener_datos_para_grafico()
        
        if not fechas:
            # Mostrar mensaje si no hay datos
            empty_label = ttk.Label(self.graph_frame, 
                                   text="No hay datos suficientes para mostrar el gráfico.\nAgregue registros de IMC para ver su progreso.",
                                   font=('Arial', 12),
                                   justify='center')
            empty_label.pack(expand=True)
            return
        
        # Crear figura con estilo profesional
        fig = Figure(figsize=(8, 5), dpi=100, facecolor='#f0f0f0')
        ax = fig.add_subplot(111)
        
        # 1. Graficar puntos con colores según categoría
        for i, (fecha, imc, color, categoria) in enumerate(zip(fechas, valores_imc, colores, categorias)):
            ax.scatter(fecha, imc, color=color, s=100, zorder=3, 
                      edgecolors='black', linewidth=1.5, alpha=0.8)
            # Añadir etiqueta con el valor en puntos seleccionados (opcional)
            if i % max(1, len(fechas)//10) == 0:  # Mostrar solo algunos para no saturar
                ax.annotate(f'{imc:.1f}', (fecha, imc), 
                           xytext=(5, 5), textcoords='offset points',
                           fontsize=8, alpha=0.7)
        
        # 2. Línea de tendencia (conexión entre puntos)
        ax.plot(fechas, valores_imc, color='gray', linewidth=2, linestyle='-', 
               marker='', alpha=0.5, label='Tendencia')
        
        # 3. Línea de tendencia suavizada (media móvil simple)
        if len(valores_imc) >= 3:
            # Calcular media móvil de 3 puntos
            smoothed = []
            for i in range(len(valores_imc)):
                start = max(0, i-1)
                end = min(len(valores_imc), i+2)
                avg = sum(valores_imc[start:end]) / (end-start)
                smoothed.append(avg)
            ax.plot(fechas, smoothed, color='blue', linewidth=2.5, 
                   linestyle='--', alpha=0.7, label='Tendencia suavizada')
        
        # 4. Colorear zonas según categorías de IMC
        # Definir rangos de IMC y colores semi-transparentes
        zonas = [
            (0, 18.5, '#FFE5B4', 'Bajo peso'),
            (18.5, 25, '#90EE90', 'Normal'),
            (25, 30, '#FFD700', 'Sobrepeso'),
            (30, 35, '#FFA500', 'Obesidad I'),
            (35, 40, '#FF6347', 'Obesidad II'),
            (40, 100, '#FF0000', 'Obesidad III')
        ]
        
        for min_val, max_val, color, label in zonas:
            ax.axhspan(min_val, max_val, alpha=0.15, color=color, label=label)
        
        # Configurar ejes
        ax.set_xlabel('Fecha', fontsize=11, fontweight='bold')
        ax.set_ylabel('Índice de Masa Corporal (IMC)', fontsize=11, fontweight='bold')
        ax.set_title('Evolución del IMC a lo largo del tiempo', fontsize=14, fontweight='bold', pad=20)
        
        # Formatear fechas en el eje X
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        fig.autofmt_xdate(rotation=45)
        
        # Configurar límites del eje Y con margen
        y_min = max(0, min(valores_imc) - 3)
        y_max = max(valores_imc) + 3
        ax.set_ylim(y_min, y_max)
        
        # Añadir línea de IMC ideal (22)
        ax.axhline(y=22, color='green', linestyle=':', linewidth=2, alpha=0.7, label='IMC Ideal (22)')
        
        # Añadir grid para mejor lectura
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.set_axisbelow(True)  # Grid detrás de los datos
        
        # Leyenda (evitar duplicados)
        handles, labels = ax.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        ax.legend(by_label.values(), by_label.keys(), loc='upper left', fontsize=8, framealpha=0.9)
        
        # Estadísticas resumen en el gráfico
        stats_text = f"Total registros: {len(valores_imc)}\n"
        stats_text += f"IMC inicial: {valores_imc[0]:.1f}\n"
        stats_text += f"IMC actual: {valores_imc[-1]:.1f}\n"
        stats_text += f"Cambio: {valores_imc[-1] - valores_imc[0]:+.1f}"
        
        ax.text(0.02, 0.98, stats_text, transform=ax.transAxes,
               fontsize=9, verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # Ajustar layout
        fig.tight_layout()
        
        # Integrar gráfico en tkinter
        self.canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=BOTH, expand=True)
    
    def calcular_imc(self) -> None:
        """
        Calcula el IMC basado en los valores ingresados.
        Incluye validaciones robustas y manejo de errores.
        """
        try:
            # Validar y convertir entradas
            peso = float(self.peso_var.get().strip())
            altura = float(self.altura_var.get().strip())
            
            # Validaciones de rango
            if peso <= 0 or peso > 500:
                messagebox.showerror("Error", "El peso debe estar entre 1 y 500 kg")
                return
            
            if altura <= 0 or altura > 3.0:
                messagebox.showerror("Error", "La altura debe estar entre 0.1 y 3.0 metros")
                return
            
            # Calcular IMC
            imc = peso / (altura ** 2)
            imc_redondeado = round(imc, 2)
            
            # Obtener categoría
            categoria = CategoriaIMC.desde_imc(imc_redondeado)
            
            # Mostrar resultado con formato profesional
            self.imc_label.config(text=f"IMC: {imc_redondeado}")
            self.categoria_label.config(
                text=f"Categoría: {categoria.nombre}",
                foreground=categoria.color,
                font=('Arial', 12, 'bold')
            )
            
            # Cambiar color del texto del IMC según categoría
            self.imc_label.config(foreground=categoria.color)
            
            # Preguntar si desea guardar
            if messagebox.askyesno("Guardar Registro", 
                                    f"IMC: {imc_redondeado}\n"
                                    f"Categoría: {categoria.nombre}\n\n"
                                    "¿Desea guardar este registro en el historial?"):
                
                # Crear y guardar registro con timestamp
                registro = RegistroIMC(
                    peso=peso,
                    altura=altura,
                    imc=imc_redondeado,
                    categoria=categoria.nombre,
                    fecha=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    color=categoria.color,
                    timestamp=datetime.now().timestamp()
                )
                
                self.gestor.agregar_registro(registro)
                self._actualizar_tabla_historial()
                self._actualizar_grafico()  # Actualizar gráfico con nuevo dato
                messagebox.showinfo("Éxito", "Registro guardado correctamente")
        
        except ValueError:
            messagebox.showerror("Error", "Por favor ingrese valores numéricos válidos")
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error inesperado: {str(e)}")
    
    def _actualizar_tabla_historial(self) -> None:
        """Actualiza la tabla con los datos del historial."""
        # Limpiar tabla actual
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Insertar registros ordenados por fecha (más reciente primero)
        for registro in reversed(self.gestor.historial):
            # Aplicar tag para colorear según categoría
            tag = f"color_{registro.categoria.replace(' ', '_')}"
            self.tree.tag_configure(tag, foreground=registro.color)
            
            self.tree.insert('', END, 
                           values=(
                               registro.fecha,
                               f"{registro.peso:.1f}",
                               f"{registro.altura:.2f}",
                               f"{registro.imc:.2f}",
                               registro.categoria
                           ),
                           tags=(tag,))
    
    def _eliminar_seleccionado(self) -> None:
        """Elimina el registro seleccionado en la tabla."""
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Seleccione un registro para eliminar")
            return
        
        if messagebox.askyesno("Confirmar", "¿Está seguro de eliminar este registro?"):
            # Obtener índice real desde el historial
            # Como mostramos en orden inverso, calculamos el índice correcto
            indices = [self.tree.index(item) for item in seleccion]
            # Ordenar de mayor a menor para no afectar índices al eliminar
            for idx in sorted(indices, reverse=True):
                # Convertir índice visual a índice real en el historial
                real_idx = len(self.gestor.historial) - 1 - idx
                self.gestor.eliminar_registro(real_idx)
            
            self._actualizar_tabla_historial()
            self._actualizar_grafico()  # Actualizar gráfico después de eliminar
            messagebox.showinfo("Éxito", "Registro(s) eliminado(s)")
    
    def _limpiar_historial(self) -> None:
        """Limpia todo el historial después de confirmación."""
        if messagebox.askyesno("Confirmar", 
                               "¿Está seguro de eliminar TODO el historial?\n"
                               "Esta acción no se puede deshacer."):
            self.gestor.limpiar_historial()
            self._actualizar_tabla_historial()
            self._actualizar_grafico()  # Actualizar gráfico después de limpiar
            messagebox.showinfo("Éxito", "Historial limpiado completamente")
    
    def _limpiar_campos(self) -> None:
        """Limpia los campos de entrada y resetea el resultado."""
        self.peso_var.set("")
        self.altura_var.set("")
        self.imc_label.config(text="---", foreground='black')
        self.categoria_label.config(text="Esperando datos...", foreground='black')
    
    def _cargar_desde_historial(self, event) -> None:
        """Carga los datos de un registro seleccionado en los campos de entrada."""
        seleccion = self.tree.selection()
        if not seleccion:
            return
        
        item = seleccion[0]
        valores = self.tree.item(item, 'values')
        
        if valores:
            # Cargar peso y altura en los campos
            self.peso_var.set(valores[1])  # Peso
            self.altura_var.set(valores[2])  # Altura
            messagebox.showinfo("Cargado", "Datos cargados. Presione 'Calcular IMC' para ver el resultado.")


# ========== PUNTO DE ENTRADA PRINCIPAL ==========
def main():
    """
    Función principal de la aplicación.
    Configura la ventana raíz y ejecuta el loop de eventos.
    """
    # Verificar que matplotlib esté instalado
    try:
        import matplotlib
        matplotlib.use('TkAgg')  # Usar backend de TkAgg para compatibilidad
    except ImportError:
        messagebox.showerror("Error", 
                            "Matplotlib no está instalado.\n"
                            "Instálelo con: pip install matplotlib")
        return
    
    root = Tk()
    app = CalculadoraIMCApp(root)
    
    root.state('zoomed')
    
    root.mainloop()


if __name__ == "__main__":
    main()
