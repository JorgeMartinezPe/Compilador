class GeneradorIntermedio:
    def __init__(self):
        self.codigo_intermedio = []  # Lista de instrucciones TAC
        self.contador_temporales = 0
        self.contador_etiquetas = 0
        self.etiquetas_saltos = {}  # Para manejar etiquetas de saltos
    
    def nuevo_temporal(self):
        """Genera un nuevo nombre de variable temporal"""
        temporal = f"t{self.contador_temporales}"
        self.contador_temporales += 1
        return temporal
    
    def nueva_etiqueta(self, prefijo="L"):
        """Genera una nueva etiqueta para saltos"""
        etiqueta = f"{prefijo}{self.contador_etiquetas}"
        self.contador_etiquetas += 1
        return etiqueta
    
    def agregar_instruccion(self, instruccion):
        """Agrega una instrucción al código intermedio"""
        self.codigo_intermedio.append(instruccion)
    
    def generar_codigo(self, arbol):
        """Genera código intermedio a partir del AST"""
        self.codigo_intermedio = []  # Reiniciar código
        self.contador_temporales = 0
        self.contador_etiquetas = 0
        
        # Procesar el programa completo
        self._generar_nodo(arbol)
        
        return self.codigo_intermedio
    
    def _generar_nodo(self, nodo):
        """Genera código para un nodo del AST"""
        metodo_generador = getattr(self, f"_generar_{nodo.nombre}", None)
        if metodo_generador:
            return metodo_generador(nodo)
        else:
            # Por defecto, procesar hijos
            for hijo in nodo.hijos:
                self._generar_nodo(hijo)
            return None
    
    def _generar_Program(self, nodo):
        """Genera código para un programa completo"""
        for hijo in nodo.hijos:
            self._generar_nodo(hijo)
    
    def _generar_Asignacion(self, nodo):
        """Genera código para una asignación: x = expresión"""
        variable = nodo.hijos[0]  # Nodo Variable
        expresion = nodo.hijos[1] # Nodo Expresión
        
        # Generar código para la expresión
        temp_resultado = self._generar_nodo(expresion)
        
        # Si la expresión devolvió un temporal, asignarlo
        if temp_resultado:
            self.agregar_instruccion(f"{variable.valor} = {temp_resultado}")
            return variable.valor
    
    def _generar_BinOp(self, nodo):
        """Genera código para operaciones binarias: t1 = a + b"""
        operador = nodo.valor
        izquierda = nodo.hijos[0]
        derecha = nodo.hijos[1]
        
        # Generar código para los operandos
        temp_izq = self._generar_nodo(izquierda)
        temp_der = self._generar_nodo(derecha)
        
        # Crear nuevo temporal para el resultado
        temp_resultado = self.nuevo_temporal()
        
        # Mapear operadores a su representación en TAC
        op_map = {
            "SUMA": "+",
            "RESTA": "-", 
            "MULTIPLICACION": "*",
            "DIVISION": "/",
            "MODULO": "%",
            "AND_LOGICO": "&&",
            "OR_LOGICO": "||",
            "IGUAL_IGUAL": "==",
            "DIFERENTE": "!=",
            "MENOR_QUE": "<",
            "MAYOR_QUE": ">",
            "MENOR_IGUAL": "<=",
            "MAYOR_IGUAL": ">="
        }
        
        operador_tac = op_map.get(operador, operador)
        self.agregar_instruccion(f"{temp_resultado} = {temp_izq} {operador_tac} {temp_der}")
        
        return temp_resultado
    
    def _generar_Numero(self, nodo):
        """Genera código para literales numéricos"""
        return nodo.valor
    
    def _generar_Variable(self, nodo):
        """Genera código para variables"""
        return nodo.valor
    
    def _generar_Booleano(self, nodo):
        """Genera código para booleanos"""
        return "1" if nodo.valor == "true" else "0"
    
    def _generar_Bloque(self, nodo):
        """Genera código para bloques de código"""
        for hijo in nodo.hijos:
            self._generar_nodo(hijo)
    
    def _generar_If(self, nodo):
        """Genera código para sentencias if"""
        condicion = nodo.hijos[0]
        bloque_if = nodo.hijos[1]
        bloque_else = nodo.hijos[2] if len(nodo.hijos) > 2 else None
        
        # Generar código para la condición
        temp_cond = self._generar_nodo(condicion)
        
        # Crear etiquetas
        etiqueta_else = self.nueva_etiqueta("else")
        etiqueta_fin = self.nueva_etiqueta("endif")
        
        # Saltar a else si condición es falsa
        self.agregar_instruccion(f"if {temp_cond} == 0 goto {etiqueta_else}")
        
        # Código del bloque if
        self._generar_nodo(bloque_if)
        self.agregar_instruccion(f"goto {etiqueta_fin}")
        
        # Etiqueta y código del else (si existe)
        self.agregar_instruccion(f"{etiqueta_else}:")
        if bloque_else:
            self._generar_nodo(bloque_else)
        
        # Etiqueta de fin del if
        self.agregar_instruccion(f"{etiqueta_fin}:")
    def _generar_Break(self, nodo):
        """Genera código para break"""
        # Buscar la etiqueta de fin del bucle más interno
        if hasattr(self, 'etiqueta_fin_bucle'):
            self.agregar_instruccion(f"goto {self.etiqueta_fin_bucle}")
        else:
            # Si no estamos en un bucle, es un error (pero lo manejamos)
            self.agregar_instruccion("goto #ERROR_BREAK_FUERA_DE_BUCLE")

    def _generar_Continue(self, nodo):
        """Genera código para continue"""
        # Buscar la etiqueta de inicio del bucle más interno
        if hasattr(self, 'etiqueta_inicio_bucle'):
            self.agregar_instruccion(f"goto {self.etiqueta_inicio_bucle}")
        else:
            # Si no estamos en un bucle, es un error (pero lo manejamos)
            self.agregar_instruccion("goto #ERROR_CONTINUE_FUERA_DE_BUCLE")    
    def _generar_While(self, nodo):
        """Genera código para sentencias while"""
        condicion = nodo.hijos[0]
        bloque_while = nodo.hijos[1]
        
        # Crear etiquetas
        etiqueta_inicio = self.nueva_etiqueta("while")
        etiqueta_fin = self.nueva_etiqueta("endwhile")
        
        # ✅ GUARDAR ETIQUETAS PARA BREAK/CONTINUE
        etiqueta_inicio_anterior = getattr(self, 'etiqueta_inicio_bucle', None)
        etiqueta_fin_anterior = getattr(self, 'etiqueta_fin_bucle', None)
        self.etiqueta_inicio_bucle = etiqueta_inicio
        self.etiqueta_fin_bucle = etiqueta_fin
        
        # Etiqueta de inicio del while
        self.agregar_instruccion(f"{etiqueta_inicio}:")
        
        # Generar código para la condición
        temp_cond = self._generar_nodo(condicion)
        
        # Saltar al final si condición es falsa
        self.agregar_instruccion(f"if {temp_cond} == 0 goto {etiqueta_fin}")
        
        # Código del bloque while
        self._generar_nodo(bloque_while)
        
        # Volver al inicio
        self.agregar_instruccion(f"goto {etiqueta_inicio}")
        
        # Etiqueta de fin del while
        self.agregar_instruccion(f"{etiqueta_fin}:")
        
        #
        if etiqueta_inicio_anterior is not None:
            self.etiqueta_inicio_bucle = etiqueta_inicio_anterior
            self.etiqueta_fin_bucle = etiqueta_fin_anterior
        else:
            # Si no había bucle anterior, eliminar las etiquetas
            if hasattr(self, 'etiqueta_inicio_bucle'):
                delattr(self, 'etiqueta_inicio_bucle')
            if hasattr(self, 'etiqueta_fin_bucle'):
                delattr(self, 'etiqueta_fin_bucle')
    
    def _generar_For(self, nodo):
        """Genera código para sentencias for"""
        inicializacion = nodo.hijos[0]
        condicion = nodo.hijos[1] 
        incremento = nodo.hijos[2]
        bloque_for = nodo.hijos[3]
        
        # Crear etiquetas
        etiqueta_inicio = self.nueva_etiqueta("for")
        etiqueta_fin = self.nueva_etiqueta("endfor")
        
        # ✅ GUARDAR ETIQUETAS PARA BREAK/CONTINUE
        etiqueta_inicio_anterior = getattr(self, 'etiqueta_inicio_bucle', None)
        etiqueta_fin_anterior = getattr(self, 'etiqueta_fin_bucle', None)
        self.etiqueta_inicio_bucle = etiqueta_inicio
        self.etiqueta_fin_bucle = etiqueta_fin
        
        # Código de inicialización
        if inicializacion:
            self._generar_nodo(inicializacion)
        
        # Etiqueta de inicio del for
        self.agregar_instruccion(f"{etiqueta_inicio}:")
        
        # Código de condición (si existe)
        if condicion:
            temp_cond = self._generar_nodo(condicion)
            self.agregar_instruccion(f"if {temp_cond} == 0 goto {etiqueta_fin}")
        
        # Código del bloque for
        self._generar_nodo(bloque_for)
        
        # Código de incremento (si existe)
        if incremento:
            self._generar_nodo(incremento)
        
        # Volver al inicio para verificar condición
        self.agregar_instruccion(f"goto {etiqueta_inicio}")
        
        # Etiqueta de fin del for
        self.agregar_instruccion(f"{etiqueta_fin}:")
        
        # ✅ RESTAURAR ETIQUETAS ANTERIORES
        if etiqueta_inicio_anterior is not None:
            self.etiqueta_inicio_bucle = etiqueta_inicio_anterior
            self.etiqueta_fin_bucle = etiqueta_fin_anterior
        else:
            # Si no había bucle anterior, eliminar las etiquetas
            if hasattr(self, 'etiqueta_inicio_bucle'):
                delattr(self, 'etiqueta_inicio_bucle')
            if hasattr(self, 'etiqueta_fin_bucle'):
                delattr(self, 'etiqueta_fin_bucle')
    
    def _generar_FunctionCall(self, nodo):
        """Genera código para llamadas a función"""
        nombre_funcion = nodo.valor
        argumentos = nodo.hijos[0]  # Nodo Argumentos
        
        # Generar código para los argumentos
        temps_argumentos = []
        for arg in argumentos.hijos:
            temp_arg = self._generar_nodo(arg)
            temps_argumentos.append(temp_arg)
        
        # Crear temporal para el resultado
        temp_resultado = self.nuevo_temporal()
        
        # Generar llamada a función
        args_str = ", ".join(temps_argumentos)
        self.agregar_instruccion(f"{temp_resultado} = call {nombre_funcion}, {args_str}")
        
        return temp_resultado
    
    def _generar_Return(self, nodo):
        """Genera código para sentencias return"""
        if nodo.hijos:
            expresion = nodo.hijos[0]
            temp_valor = self._generar_nodo(expresion)
            self.agregar_instruccion(f"return {temp_valor}")
        else:
            self.agregar_instruccion("return")
    
    def imprimir_codigo(self):
        """Imprime el código intermedio generado"""
        print("\n" + "="*60)
        print("CÓDIGO INTERMEDIO (TAC)")
        print("="*60)
        for i, instruccion in enumerate(self.codigo_intermedio):
            print(f"{i:3d}: {instruccion}")