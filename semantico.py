from copy import deepcopy
class AnalizadorSemantico:
    def __init__(self):
        self.funciones = {}  # nombre -> (tipo_retorno, parametros)
        self.funcion_actual = None
        self.tipo_retorno_actual = None

def verificar_funciones(nodo, pila_ambitos, funcion_actual, funciones_registradas, errores):
    if nodo.nombre == "Funcion":
        nombre_funcion = nodo.valor
        tipo_retorno = nodo.hijos[0].valor  # TipoRetorno
        parametros = nodo.hijos[1]
        bloque = nodo.hijos[2]
        
        # Registrar función
        funciones_registradas[nombre_funcion] = {
            'tipo_retorno': tipo_retorno,
            'parametros': [p.tipo for p in parametros.hijos],
            'nodo': nodo
        }
        
        # Crear ámbito para parámetros
        pila_ambitos.append({})
        for param in parametros.hijos:
            pila_ambitos[-1][param.valor] = param.tipo
        
        # Verificar bloque con seguimiento de retorno
        tiene_retorno = verificar_bloque_con_retorno(bloque, pila_ambitos, tipo_retorno, errores)
        
        if tipo_retorno != "void" and not tiene_retorno:
            errores.append(f"Error semántico: función '{nombre_funcion}' debe retornar un valor")
        
        pila_ambitos.pop()
        return

def verificar_bloque_con_retorno(nodo, pila_ambitos, tipo_retorno_esperado, errores):
    """
    Verifica que todas las rutas de ejecución retornen un valor del tipo correcto
    """
    if nodo.nombre == "Return":
        expresion = nodo.hijos[0] if nodo.hijos else None
        
        if tipo_retorno_esperado == "void" and expresion is not None:
            errores.append("Error semántico: función void no puede retornar un valor")
            return True
        elif tipo_retorno_esperado != "void" and expresion is None:
            errores.append(f"Error semántico: se esperaba retornar un valor de tipo '{tipo_retorno_esperado}'")
            return True
        elif expresion is not None:
            tipo_expresion = verificar_tipos(expresion, pila_ambitos, errores)
            if tipo_expresion != tipo_retorno_esperado:
                errores.append(f"Error semántico: tipo de retorno '{tipo_expresion}' no coincide con '{tipo_retorno_esperado}'")
        return True
    
    elif nodo.nombre == "If":
        # Verificar si ambas ramas retornan
        bloque_if = nodo.hijos[1]
        tiene_retorno_if = verificar_bloque_con_retorno(bloque_if, pila_ambitos, tipo_retorno_esperado, errores)
        
        if len(nodo.hijos) > 2:
            bloque_else = nodo.hijos[2]
            tiene_retorno_else = verificar_bloque_con_retorno(bloque_else, pila_ambitos, tipo_retorno_esperado, errores)
            return tiene_retorno_if and tiene_retorno_else
        else:
            return False  # If sin else puede no retornar
    
    elif nodo.nombre == "Bloque":
        # Verificar todas las instrucciones del bloque
        for hijo in nodo.hijos:
            if verificar_bloque_con_retorno(hijo, pila_ambitos, tipo_retorno_esperado, errores):
                return True
        return False
    
    # Para otras instrucciones, no contribuyen al retorno
    return False
def verificar_usos(nodo, pila_ambitos, errores, tokens_info=None):
    """
    Verifica uso correcto de variables con mejores mensajes de error
    """
    def agregar_error(mensaje, nodo_error=None):
        if tokens_info and hasattr(nodo_error, '_token_pos'):
            num_linea, columna, _, linea_original = tokens_info[nodo_error._token_pos]
            error_completo = f"Error semántico en línea {num_linea}, columna {columna}:\n"
            error_completo += f"  {mensaje}\n"
            error_completo += f"  Línea: {linea_original}\n"
            error_completo += f"  {' ' * (columna-1)}^"
            errores.append(error_completo)
        else:
            errores.append(f"Error semántico: {mensaje}")
    
    if nodo.nombre == "Asignacion":
        var_node = nodo.hijos[0]
        nombre_var = var_node.valor
        tipo_var = var_node.tipo
        
        if tipo_var is not None:  # Declaración
            # ✅ PERMITIR SHADOWING - siempre insertar en ámbito actual
            # No verificamos si ya existe en ámbito actual porque el parser ya lo hizo
            pila_ambitos[-1][nombre_var] = tipo_var
        else:  # Asignación
            # Buscar en todos los ámbitos (padres incluidos)
            if buscar_en_ambitos(pila_ambitos, nombre_var) is None:
                agregar_error(f"La variable '{nombre_var}' no ha sido declarada", var_node)

    elif nodo.nombre == "Variable":
        nombre_var = nodo.valor
        if buscar_en_ambitos(pila_ambitos, nombre_var) is None:
            agregar_error(f"La variable '{nombre_var}' no ha sido declarada", nodo)

    elif nodo.nombre == "Bloque":
        # Crear un nuevo ámbito local
        pila_ambitos.append({})
        for hijo in nodo.hijos:
            verificar_usos(hijo, pila_ambitos, errores)
        pila_ambitos.pop()
        return

    # ESTRUCTURAS DE CONTROL DE FLUJO
    elif nodo.nombre == "If":
        # Verificar condición en ámbito actual
        condicion = nodo.hijos[0]
        verificar_usos(condicion, pila_ambitos, errores)
        
        # Bloque if (ámbito propio)
        pila_ambitos.append({})
        verificar_usos(nodo.hijos[1], pila_ambitos, errores)
        pila_ambitos.pop()
        
        # Bloque else si existe (ámbito propio)
        if len(nodo.hijos) > 2:
            pila_ambitos.append({})
            verificar_usos(nodo.hijos[2], pila_ambitos, errores)
            pila_ambitos.pop()
        return

    elif nodo.nombre == "While":
        # Verificar condición en ámbito actual
        condicion = nodo.hijos[0]
        verificar_usos(condicion, pila_ambitos, errores)
        
        # Bloque while (ámbito propio)
        pila_ambitos.append({})
        verificar_usos(nodo.hijos[1], pila_ambitos, errores)
        pila_ambitos.pop()
        return

    elif nodo.nombre == "For":
        # CREAR ÁMBITO ESPECÍFICO PARA EL FOR
        pila_ambitos.append({})  # Nuevo ámbito para el for
        
        # INICIALIZACIÓN: se verifica en el NUEVO ámbito del for
        inicializacion = nodo.hijos[0]
        if inicializacion is not None:
            verificar_usos(inicializacion, pila_ambitos, errores)
        
        # CONDICIÓN: se verifica en el MISMO ámbito del for  
        condicion = nodo.hijos[1]
        if condicion is not None:
            verificar_usos(condicion, pila_ambitos, errores)
        
        # INCREMENTO: se verifica en el MISMO ámbito del for
        incremento = nodo.hijos[2]
        if incremento is not None:
            verificar_usos(incremento, pila_ambitos, errores)
        
        # BLOQUE: se verifica en el MISMO ámbito del for
        verificar_usos(nodo.hijos[3], pila_ambitos, errores)
        
        pila_ambitos.pop()  # Salir del ámbito del for
        return
    elif nodo.nombre == "Break" or nodo.nombre == "Continue":
        # Verificar que estamos dentro de un bucle
        # Por simplicidad, por ahora no verificamos esto
        return
    # Verificar hijos (recursión) - solo si no es una estructura ya procesada
    if nodo.nombre not in ["If", "While", "For", "Bloque"]:
        for hijo in nodo.hijos:
            verificar_usos(hijo, pila_ambitos, errores)


def buscar_en_ambitos(pila_ambitos, nombre_var):
    """
    Busca una variable desde el ámbito más interno hacia el global.
    Permite shadowing - la variable más interna oculta las de ámbitos externos.
    """
    # Buscar desde el ámbito más reciente al más antiguo
    for i in range(len(pila_ambitos) - 1, -1, -1):
        if nombre_var in pila_ambitos[i]:
            return pila_ambitos[i][nombre_var]
    return None 

def verificar_tipos(nodo, pila_ambitos, errores, tokens_info=None):
    """
    Verifica compatibilidad de tipos, respetando los límites de cada ámbito.
    """
    def agregar_error_tipos(mensaje, nodo_error=None):
        if tokens_info and nodo_error and hasattr(nodo_error, '_token_pos'):
            try:
                num_linea, columna, _, valor, linea_original = tokens_info[nodo_error._token_pos]
                error_completo = f" ERROR DE TIPOS - Línea {num_linea}, Columna {columna}:\n"
                error_completo += f"   {mensaje}\n"
                error_completo += f"   {linea_original}\n"
                error_completo += f"   {' ' * (columna-1)}^\n"
                errores.append(error_completo)
            except (IndexError, AttributeError):
                errores.append(f" ERROR DE TIPOS: {mensaje}")
        else:
            errores.append(f" ERROR DE TIPOS: {mensaje}")
    
    if nodo.nombre == "Bloque":
        pila_ambitos.append({})
        for hijo in nodo.hijos:
            verificar_tipos(hijo, pila_ambitos, errores, tokens_info)
        pila_ambitos.pop()
        return None

    # VALIDACIÓN DE ESTRUCTURAS DE CONTROL
    elif nodo.nombre == "If":
        condicion = nodo.hijos[0]
        tipo_cond = verificar_tipos(condicion, pila_ambitos, errores, tokens_info)
        
        # Verificar que la condición sea booleana
        if tipo_cond and tipo_cond != "bool":
            agregar_error_tipos(f"La condición del 'if' debe ser booleana, no '{tipo_cond}'", nodo)
        
        # Verificar bloques
        pila_ambitos.append({})
        verificar_tipos(nodo.hijos[1], pila_ambitos, errores, tokens_info)
        pila_ambitos.pop()
        
        if len(nodo.hijos) > 2:
            pila_ambitos.append({})
            verificar_tipos(nodo.hijos[2], pila_ambitos, errores, tokens_info)
            pila_ambitos.pop()
        return None

    elif nodo.nombre == "While":
        condicion = nodo.hijos[0]
        tipo_cond = verificar_tipos(condicion, pila_ambitos, errores, tokens_info)
        
        # Verificar que la condición sea booleana
        if tipo_cond and tipo_cond != "bool":
            agregar_error_tipos(f"La condición del 'while' debe ser booleana, no '{tipo_cond}'", nodo)
        
        pila_ambitos.append({})
        verificar_tipos(nodo.hijos[1], pila_ambitos, errores, tokens_info)
        pila_ambitos.pop()
        return None

    elif nodo.nombre == "For":
        # Crear ámbito para el bloque for
        pila_ambitos.append({})
        
        # Inicialización
        inicializacion = nodo.hijos[0]
        if inicializacion is not None:
            verificar_tipos(inicializacion, pila_ambitos, errores, tokens_info)
        
        # Condición (debe ser booleana si existe)
        condicion = nodo.hijos[1]
        if condicion is not None:
            tipo_cond = verificar_tipos(condicion, pila_ambitos, errores, tokens_info)
            if tipo_cond and tipo_cond != "bool":
                agregar_error_tipos(f"La condición del 'for' debe ser booleana, no '{tipo_cond}'", nodo)
        
        # Incremento
        incremento = nodo.hijos[2]
        if incremento is not None:
            verificar_tipos(incremento, pila_ambitos, errores, tokens_info)
        
        # Bloque
        verificar_tipos(nodo.hijos[3], pila_ambitos, errores, tokens_info)
        
        pila_ambitos.pop()
        return None

    # OPERACIONES
    elif nodo.nombre == "BinOp":
        tipo_izq = verificar_tipos(nodo.hijos[0], pila_ambitos, errores, tokens_info)
        tipo_der = verificar_tipos(nodo.hijos[1], pila_ambitos, errores, tokens_info)
        op = nodo.valor

        if not tipo_izq or not tipo_der:
            return None

        # Operadores aritméticos
        if op in ["SUMA", "RESTA", "MULTIPLICACION", "DIVISION"]:
            if tipo_izq in ["int", "float"] and tipo_der in ["int", "float"]:
                return "float" if "float" in [tipo_izq, tipo_der] else "int"
            else:
                agregar_error_tipos(f"Operación '{op}' inválida entre '{tipo_izq}' y '{tipo_der}'", nodo)
                return None
        
        # Operadores de comparación
        elif op in ["MAYOR_QUE", "MENOR_QUE", "MAYOR_IGUAL", "MENOR_IGUAL"]:
            if tipo_izq in ["int", "float"] and tipo_der in ["int", "float"]:
                return "bool"
            else:
                agregar_error_tipos(f"Comparación '{op}' inválida entre '{tipo_izq}' y '{tipo_der}'", nodo)
                return None
        
        # Operadores de igualdad
        elif op in ["IGUAL_IGUAL", "DIFERENTE"]:
            if (tipo_izq == tipo_der) or (tipo_izq in ["int", "float"] and tipo_der in ["int", "float"]):
                return "bool"
            else:
                agregar_error_tipos(f"Comparación '{op}' inválida entre '{tipo_izq}' y '{tipo_der}'", nodo)
                return None
        
        # Operadores lógicos
        elif op in ["AND_LOGICO", "OR_LOGICO"]: 
            if tipo_izq == "bool" and tipo_der == "bool":
                return "bool"
            else:
                agregar_error_tipos(f"Operación lógica '{op}' inválida entre '{tipo_izq}' y '{tipo_der}'", nodo)
                return None

    elif nodo.nombre == "Numero":
        return "float" if "." in (nodo.valor or "") else "int"

    elif nodo.nombre == "Booleano":
        return "bool"

    elif nodo.nombre == "Variable":
        return buscar_en_ambitos(pila_ambitos, nodo.valor)

    elif nodo.nombre == "Asignacion":
        var_node = nodo.hijos[0]
        expr_node = nodo.hijos[1]

        tipo_var = var_node.tipo or buscar_en_ambitos(pila_ambitos, var_node.valor)
        tipo_expr = verificar_tipos(expr_node, pila_ambitos, errores, tokens_info)

        if tipo_var is not None and tipo_expr is not None:
            if tipo_var != tipo_expr:
                # Permitir asignar int a float, pero no al revés
                if not (tipo_var == "float" and tipo_expr == "int"):
                    agregar_error_tipos(f"No se puede asignar '{tipo_expr}' a variable '{var_node.valor}' de tipo '{tipo_var}'", nodo)
        return tipo_var

    # Por defecto, revisar hijos
    for hijo in nodo.hijos:
        verificar_tipos(hijo, pila_ambitos, errores, tokens_info)
    return None
def verificar_division_por_cero(nodo, errores, tokens_info=None):
    """Verifica divisiones por cero"""
    
    if nodo.nombre == "BinOp" and nodo.valor == "/":
        derecho = nodo.hijos[1]
        
        # Verificar división por cero literal
        if derecho.nombre == "Numero" and derecho.valor in ["0", "0.0"]:
            # Buscar posición en tokens_info
            posicion = None
            if tokens_info:
                for i, token in enumerate(tokens_info):
                    num_linea, columna, tipo, valor, linea_original = token
                    if tipo == "DIVISION" and valor == "/":
                        posicion = i
                        break
            
            if posicion is not None:
                num_linea, columna, _, _, linea_original = tokens_info[posicion]
                error_msg = f"❌ ERROR ARITMÉTICO - Línea {num_linea}, Columna {columna}:\n"
                error_msg += f"   DIVISIÓN POR CERO - No se puede dividir entre cero\n"
                error_msg += f"   {linea_original}\n"
                error_msg += f"   {' ' * (columna-1)}^\n"
                errores.append(error_msg)
            else:
                errores.append("❌ ERROR ARITMÉTICO: División por cero detectada")
    
    # Verificar recursivamente en los hijos
    for hijo in nodo.hijos:
        verificar_division_por_cero(hijo, errores, tokens_info)

def analizar_semantica(arbol, tokens_info=None): 
    errores = []
    pila_ambitos = [{}]
    
    print("\n[SEMÁNTICO] Verificando usos y declaraciones...")
    verificar_usos(arbol, pila_ambitos, errores, tokens_info)  
    
    print("\n[SEMÁNTICO] Verificando compatibilidad de tipos...")
    verificar_tipos(arbol, pila_ambitos, errores, tokens_info)  
    
    print("\n[SEMÁNTICO] Verificando divisiones por cero...")
    verificar_division_por_cero(arbol, errores, tokens_info) 
    
    # Verificaciones de tabla de símbolos
    if hasattr(arbol, 'tabla_global') and arbol.tabla_global:
        print("\n[SEMÁNTICO] Verificaciones de tabla de símbolos...")
        verificar_tabla_simbolos(arbol.tabla_global, errores)
        
        # IMPRIMIR TABLA DE SÍMBOLOS
        arbol.tabla_global.imprimir_tabla()
    else:
        print("\n No se encontró tabla de símbolos para verificar")
    
    print("\n[✔] Análisis semántico completado.")
    
    if errores:
        print("\n[ERRORES SEMÁNTICOS DETECTADOS]")
        for error in errores:
            print(f"{error}\n")
    else:
        print("\n No se encontraron errores semánticos")

    return arbol.tabla_global if hasattr(arbol, 'tabla_global') else None, errores

def verificar_tabla_simbolos(tabla, errores):
    """Verifica problemas comunes en la tabla de símbolos"""
    
    # Variables declaradas pero no usadas
    no_usadas = tabla.obtener_variables_no_usadas()
    for var in no_usadas:
        errores.append(f"Advertencia: Variable '{var}' declarada pero no usada")
    
    # Variables no inicializadas (opcional)
    no_inicializadas = tabla.obtener_variables_no_inicializadas()
    for var in no_inicializadas:
        errores.append(f"Advertencia: Variable '{var}' no inicializada")

