import os
import tkinter as tk
from tkinter import messagebox, scrolledtext
from abc import ABC, abstractmethod
from datetime import datetime

#*******************************************
# Módulo propio para guardar los errores de un archivo .log
# Hecho para cumplir con el requerimiento de la guia de la actividad de la UNAD 
#*******************************************
class registrodeeventos:
    ARCHIVO_LOG = "sistema.log"

    @classmethod
    def registrar_evento(cls, nivel: str, descripcion: str):
        marca_tiempo = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        linea = f"[{marca_tiempo}] [{nivel.upper}]: {descripcion}\n"
        with open(cls.ARCHIVO_LOG, "a", encoding="utf-8") as f:
            f.write(linea)

# Excepciones propias del negocio
class excepcionpersonalizadaFJ(Exception):
    pass

class ClienteNoValido(excepcionpersonalizadaFJ):
    pass

class ServicioNoDisponible(excepcionpersonalizadaFJ):
    pass

class ReservaFallida(excepcionpersonalizadaFJ):
    pass

#******************************************
# MODELO ORIENTADO A OBJETOS (POO)
#******************************************
class EntidadRaiz(ABC):
    def __init__(self, codigo: str):
        self._codigo = codigo

    @property
    def codigo(self):
        return self._codigo

    @abstractmethod
    def ver_info(self) -> str:
        pass

class Cliente(EntidadRaiz):
    def __init__(self, codigo: str, nombre_completo: str, email: str):
        super().__init__(codigo)
        self.nombre_completo = nombre_completo
        self.email = email  # Usa el setter de abajo para validar

    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, valor_email: str):
        # Validación estricta para forzar excepciones controladas
        if "@" not in valor_email or "." not in valor_email:
            registrodeeventos.registrar_evento("ERROR", f"Intento fallido de registro de correo: {valor_email}")
            raise ClienteNoValido(f"El correo '{valor_email}' no cumple con el formato requerido.")
        self._email = valor_email

    def ver_info(self) -> str:
        return f"Cliente: {self.nombre_completo} | Email: {self._email}"

class ServicioBase(EntidadRaiz, ABC):
    def __init__(self, codigo: str, titulo: str, costo_inicial: float):
        super().__init__(codigo)
        self.titulo = titulo
        self.costo_inicial = costo_inicial

    @abstractmethod
    def calcular_tarifa(self) -> float:
        pass

    # Método sobrecargado con parámetros opcionales para descuentos/impuestos
    def calcular_tarifa_flexible(self, incluir_impuesto: bool = True, porcentaje_desc: float = 0.0) -> float:
        monto = self.calcular_tarifa()
        if porcentaje_desc > 0:
            monto = monto - (monto * (porcentaje_desc / 100))
        if incluir_impuesto:
            monto = monto * 1.19  # IVA estándar
        return round(monto, 2)

class ReservaSalas(ServicioBase):
    def __init__(self, codigo: str, costo_inicial: float, nro_personas: int):
        super().__init__(codigo, "Reserva de Espacios / Salas", costo_inicial)
        if nro_personas <= 0:
            raise ServicioNoDisponible("La capacidad de personas debe ser superior a 0.")
        self.nro_personas = nro_personas

    def calcular_tarifa(self) -> float:
        # Recargo si la sala es grande
        return self.costo_inicial * 1.15 if self.nro_personas > 10 else self.costo_inicial

    def ver_info(self) -> str:
        return f"[Sala] {self.titulo} - Capacidad: {self.nro_personas} pax - Base: ${self.costo_inicial}"

class AlquilerEquipos(ServicioBase):
    def __init__(self, codigo: str, costo_inicial: float, cantidad_horas: int):
        super().__init__(codigo, "Alquiler de Equipamiento", costo_inicial)
        if cantidad_horas <= 0:
            raise ServicioNoDisponible("Las horas de alquiler no pueden ser negativas o cero.")
        self.cantidad_horas = cantidad_horas

    def calcular_tarifa(self) -> float:
        return self.costo_inicial * self.cantidad_horas

    def ver_info(self) -> str:
        return f"[Equipo] {self.titulo} - Tiempo: {self.cantidad_horas} hrs - Base: ${self.costo_inicial}"

class AsesoriaExperta(ServicioBase):
    def __init__(self, codigo: str, costo_inicial: float, es_senior: bool):
        super().__init__(codigo, "Asesoría Profesional", costo_inicial)
        self.es_senior = es_senior

    def calcular_tarifa(self) -> float:
        return self.costo_inicial * 1.4 if self.es_senior else self.costo_inicial

    def ver_info(self) -> str:
        return f"[Asesoría] {self.titulo} - Senior: {self.es_senior} - Base: ${self.costo_inicial}"

class GestionReserva:
    def __init__(self, id_ticket: str, comprador: Cliente, servicio_solicitado: ServicioBase):
        self.id_ticket = id_ticket
        self.comprador = comprador
        self.servicio_solicitado = servicio_solicitado
        self.estado_actual = "En Espera"

    def procesar_operacion(self) -> str:
        resultado_proceso = ""
        try:
            registrodeeventos.registrar_evento("INFO", f"Procesando ticket {self.id_ticket}...")
            if not self.comprador or not self.servicio_solicitado:
                raise ReservaFallida("Faltan datos críticos en la reserva.")
            
            # Aquí calculo el total aplicando el IVA y el descuento del 5% como lo solicita el ejercicio
            total_pagar = self.servicio_solicitado.calcular_tarifa_flexible(incluir_impuesto=True, porcentaje_desc=5.0)
            self.estado_actual = "Aprobada"
            resultado_proceso = f"✅ ÉXITO: Reserva {self.id_ticket} aprobada para {self.comprador.nombre_completo}. Total: ${total_pagar}"
            registrodeeventos.registrar_evento("INFO", f"Ticket {self.id_ticket} completado con éxito.")
            
        except ZeroDivisionError as zde:
            registrodeeventos.registrar_evento("ERROR", f"Fallo matemático crítico en ticket {self.id_ticket}: {zde}")
            raise ReservaFallida("Error interno de cálculo aritmético.") from zde
        except Exception as err:
            registrodeeventos.registrar_evento("ERROR", f"Excepción atrapada en ticket {self.id_ticket}: {err}")
            raise ReservaFallida(f"No se pudo finiquitar la reserva: {err}") from err
        else:
            return resultado_proceso
        finally:
            # Bloque finally obligatorio por guía
            print(f"[LOG INTERNO] Cierre del flujo de control para ticket: {self.id_ticket}")


#************************************
# INTERFAZ GRÁFICA (GUI) DINÁMICA
#************************************
class AppSoftwareFJ:
    def __init__(self, root):
        self.root = root
        self.root.title("sistema Software FJ - version final grupo edwin valencia,.....")
        self.root.geometry("750x550")
        self.root.config(bg="#f0f2f5")

        # Título visual superior
        lbl_titulo = tk.Label(root, text="🏢 Sistema de Gestión Software FJ", font=("Arial", 16, "bold"), bg="#f0f2f5", fg="#1a73e8")
        lbl_titulo.pack(pady=10)

        # Botón para ejecutar la simulación de las 10 operaciones de la guía
        btn_simular = tk.Button(root, text="▶ Ejecutar Simulación de 10 Operaciones (Válidas y Errores)", 
                                command=self.lanzar_simulacion, font=("Arial", 11, "bold"), bg="#1a73e8", fg="white", padx=10, relief="flat")
        btn_simular.pack(pady=10)

        # Consola visual interna para mostrar resultados dinámicos
        lbl_consola = tk.Label(root, text="Registro de Ejecución en Tiempo Real:", font=("Arial", 10, "italic"), bg="#f0f2f5")
        lbl_consola.pack(anchor="w", padx=25)

        self.consola = scrolledtext.ScrolledText(root, width=85, height=22, font=("Consolas", 10), bg="#1e1e1e", fg="#d4d4d4")
        self.consola.pack(pady=5, padx=20)

    def escribir_consola(self, texto):
        self.consola.insert(tk.END, texto + "\n")
        self.consola.see(tk.END)

    def lanzar_simulacion(self):
        self.consola.delete("1.0", tk.END)
        self.escribir_consola("=== INICIANDO PRUEBAS DEL SISTEMA SOFTWARE FJ ===\n")

        if os.path.exists("sistema.log"):
            os.remove("sistema.log")

        # Las 10 operaciones combinadas (correctas e incorrectas para probar excepciones)
        casos_prueba_estudiantes = [
            ("Prueba 1: creacio exitosa de un cliente normal", lambda: Cliente("C01", "Juan pérez", "juan.perez@unad.edu.co")),
            ("prueba 2: forzando errores de correo sin arroba", lambda: Cliente("C02", "María Lopez", "correo_malo_sin_arroba")),
            ("prueba 3: Creación correcta de Sala", lambda: ReservaSalas("S01", 120000.0, 8)),
            ("prueba 4. Error: Sala con capacidad negativa", lambda: ReservaSalas("S02", 90000.0, -2)),
            ("prueba 5. Alquiler de equipo correcto", lambda: AlquilerEquipos("E01", 45000.0, 5)),
            ("prueba 6. Error: Alquiler de equipo en cero horas", lambda: AlquilerEquipos("E02", 30000.0, 0)),
            ("prueba 7. Asesoría experta creada con éxito", lambda: AsesoriaExperta("A01", 180000.0, True)),
            ("prueba 8. Procesar reserva exitosa integral", lambda: GestionReserva("T01", Cliente("C03", "Sofia Leon", "sofia@mail.com"), AlquilerEquipos("E03", 50000.0, 3)).procesar_operacion()),
            ("prueba 9. Error controlado en reserva (correo inválido interno)", lambda: GestionReserva("T02", Cliente("C04", "Andres Gil", "andres_correo_malo"), ReservaSalas("S03", 100000.0, 4)).procesar_operacion()),
            ("prueba 10. Cálculo polimórfico avanzado de tarifa", lambda: f"Tarifa personalizada calculada: ${AsesoriaExperta('A02', 250000.0, False).calcular_tarifa_flexible(incluir_impuesto=False, porcentaje_desc=10.0)}")
        ]

        for idx, (descripcion_prueba, funcion_lambda) in enumerate(casos_prueba_estudiantes, 1):
            self.escribir_consola(f"[{idx}] Evaluando: {descripcion_prueba}")
            try:
                res = funcion_lambda()
                if res:
                    self.escribir_consola(f"    -> Resultado: {res}")
                else:
                    self.escribir_consola("    -> Operación ejecutada de forma exitosa.")
            except excepcionpersonalizadaFJ as ex_personalizada:
                self.escribir_consola(f"    ⚠️ [EXCEPCIÓN CONTROLADA]: {ex_personalizada}")
            except Exception as ex_general:
                self.escribir_consola(f"    ❌ [ERROR INESPERADO]: {ex_general}")
            self.escribir_consola("-" * 65)

        self.escribir_consola("\n=== SIMULACIÓN FINALIZADA CON ÉXITO ===")
        messagebox.showinfo("Proceso Terminado", "Las 10 operaciones se han ejecutado correctamente. Revise el archivo 'sistema.log' generado.")

if __name__ == "__main__":
    ventana_principal = tk.Tk()
    app = AppSoftwareFJ(ventana_principal)
    ventana_principal.mainloop()