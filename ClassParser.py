import re

class TablaSimbolos:
    def __init__(self, padre=None):
        self.padre = padre
        self.simbolos = {}
        self.funciones = {}
        
    
    def insertar_variable(self, nombre, tipo, ambito="global", inicializada=False):
        if nombre in self.simbolos:
            return False
        
        self.simbolos[nombre] = {
            'tipo': tipo,
            'ambito': ambito,
            'inicializada': inicializada,
            'usada': False,
            'tipo_simbolo': 'variable'
        }
        return True
    
    def insertar_funcion(self, nombre, tipo_retorno, parametros):
        if nombre in self.funciones:
            return False
        
        self.funciones[nombre] = {
            'tipo_retorno': tipo_retorno,
            'parametros': parametros,
            'tipo_simbolo': 'funcion'
        }
        return True
    
    def buscar_variable(self, nombre):
        if nombre in self.simbolos:
            return self.simbolos[nombre]
        elif self.padre:
            return self.padre.buscar_variable(nombre)
        else:
            return None
    
    def buscar_funcion(self, nombre):
        if nombre in self.funciones:
            return self.funciones[nombre]
        elif self.padre:
            return self.padre.buscar_funcion(nombre)
        else:
            return None
    
    def marcar_usada(self, nombre):
        simbolo = self.buscar_variable(nombre)
        if simbolo:
            simbolo['usada'] = True
    
    def marcar_inicializada(self, nombre):
        simbolo = self.buscar_variable(nombre)
        if simbolo:
            simbolo['inicializada'] = True
    
    def obtener_variables_no_usadas(self):
        return [nombre for nombre, info in self.simbolos.items() 
                if not info['usada']]
    
    def obtener_variables_no_inicializadas(self):
        return [nombre for nombre, info in self.simbolos.items() 
                if not info['inicializada']]
    
    def imprimir_tabla(self):
        print("\n" + "="*60)
        print("TABLA DE SÍMBOLOS")
        print("="*60)
        
        if self.simbolos:
            print("\n--- VARIABLES ---")
            for nombre, info in self.simbolos.items():
                estado = "✓" if info['inicializada'] else "✗"
                usada = "✓" if info['usada'] else "✗"
                print(f"  {nombre}: {info['tipo']} | ámbito: {info['ambito']} | inicializada: {estado} | usada: {usada}")
        
        if self.funciones:
            print("\n--- FUNCIONES ---")
            for nombre, info in self.funciones.items():
                params_str = ", ".join([f"{p[0]} {p[1]}" for p in info['parametros']])
                print(f"  {nombre}: {info['tipo_retorno']} ({params_str})")
        
        print("="*60)

class ParserAsignacion:
    def __init__(self, tokens_con_ubicacion, tokens_simple=None):
       
        self.tokens_con_ubicacion = tokens_con_ubicacion
        
        if tokens_simple is None:
           
            self.tokens = [(t[2], t[3]) for t in tokens_con_ubicacion]
        else:
           
            self.tokens = tokens_simple
            
        self.tokens.append(("EOF", "EOF"))
        self.pos = 0
        self.tabla_global = TablaSimbolos()
        self.tabla_actual = self.tabla_global
        self.ambito_actual = "global"
        
    def get_ubicacion_actual(self):
        """Obtiene información de ubicación del token actual"""
        if self.pos < len(self.tokens_con_ubicacion):
            num_linea, columna, _, valor, linea_original = self.tokens_con_ubicacion[self.pos]
            return num_linea, columna, valor, linea_original
        return None, None, None, None
    def entrar_ambito(self, nombre_ambito):
        nueva_tabla = TablaSimbolos(padre=self.tabla_actual)
        self.tabla_actual = nueva_tabla
        self.ambito_actual = nombre_ambito

    def salir_ambito(self):
        if self.tabla_actual.padre:
            self.tabla_actual = self.tabla_actual.padre
            self.ambito_actual = "global" if self.tabla_actual.padre is None else "local"

    def current_token(self):
        return self.tokens[self.pos]

    def eat(self, token_type):
        tok_type, tok_val = self.current_token()
        num_linea, columna, _, linea_original = self.get_ubicacion_actual()
        
        print(f"[DEBUG] Esperado: {token_type}, Encontrado: {tok_type} ({tok_val})")
        if tok_type == token_type:
            self.pos += 1
            return tok_val
        else:
            #  MEJOR MENSAJE DE ERROR con ubicación
            error_msg = f"Error sintáctico en línea {num_linea}, columna {columna}:\n"
            error_msg += f"  Se esperaba '{token_type}', pero se encontró '{tok_val}'\n"
            error_msg += f"  Línea: {linea_original}\n"
            error_msg += f"  {' ' * (columna-1)}^"
            raise SyntaxError(error_msg)
    
    def parse_instruccion(self):
        tok_type, tok_val = self.current_token()

        if tok_type == "LLAVE_APERTURA":
            return self.parse_bloque()
        elif tok_type == "IF":
            return self.if_statement()
        elif tok_type == "WHILE":
            return self.while_statement() 
        elif tok_type == "FOR":
            return self.for_statement()
        elif tok_type == "BREAK":  
            return self.break_statement()
        elif tok_type == "CONTINUE": 
            return self.continue_statement() 
        elif tok_type == "RETURN":
            return self.return_statement()
        elif tok_type == "TIPO_DATO":
            if (self.pos + 2 < len(self.tokens) and 
                self.tokens[self.pos + 1][0] == "VARIABLE" and 
                self.tokens[self.pos + 2][0] == "PARENTESIS_APERTURA"):
                return self.function_declaration()
            else:
                return self.assignment()
        elif tok_type == "VARIABLE":
            # Detectar llamada a función como expresión
            if (self.pos + 1 < len(self.tokens) and 
                self.tokens[self.pos + 1][0] == "PARENTESIS_APERTURA"):
                expr = self.expression()
                self.eat("PUNTO_COMA")
                return expr
            else:
                return self.assignment()
        elif tok_type == "EOF":
            return None
        else:
            raise SyntaxError(f"Instrucción inesperada: {tok_type} ({tok_val})")
    def break_statement(self):
        """Maneja la instrucción break"""
        print(f"[DEBUG BREAK] Iniciando break. Token: {self.current_token()}")
        self.eat("BREAK")
        self.eat("PUNTO_COMA")
        print(f"[DEBUG BREAK] Break completado exitosamente")
        return ASTNode("Break")

    def continue_statement(self):
        """Maneja la instrucción continue"""
        print(f"[DEBUG CONTINUE] Iniciando continue. Token: {self.current_token()}")
        self.eat("CONTINUE")
        self.eat("PUNTO_COMA")
        print(f"[DEBUG CONTINUE] Continue completado exitosamente")
        return ASTNode("Continue")
    def function_declaration(self):
        print(f"[DEBUG FUNCTION] Iniciando función. Token: {self.current_token()}")
        
        tipo_retorno = self.eat("TIPO_DATO")
        nombre_funcion = self.eat("VARIABLE")
        
        print(f"[DEBUG FUNCTION] Función: {tipo_retorno} {nombre_funcion}")
        
        self.eat("PARENTESIS_APERTURA")
        
        
        self.entrar_ambito(nombre_funcion)
        
        parametros = self.parameters()
        self.eat("PARENTESIS_CIERRE")
        
        
        param_info = [(p.tipo, p.valor) for p in parametros.hijos]
        self.tabla_global.insertar_funcion(nombre_funcion, tipo_retorno, param_info)
        
        # Registrar parámetros como variables en ámbito local
        for param in parametros.hijos:
            self.tabla_actual.insertar_variable(param.valor, param.tipo, nombre_funcion, inicializada=True)
        
        # Procesar el bloque de la función
        bloque_funcion = self.block()
        
        
        self.salir_ambito()
        
        tipo_retorno_node = ASTNode("TipoRetorno", tipo_retorno)
        return ASTNode("Funcion", nombre_funcion, 
                      hijos=[tipo_retorno_node, parametros, bloque_funcion], 
                      tipo=tipo_retorno)

    def parameters(self):
        parametros = []
        
        if self.current_token()[0] == "PARENTESIS_CIERRE":
            return ASTNode("Parametros", hijos=parametros)
        
        if self.current_token()[0] == "TIPO_DATO":
            tipo = self.eat("TIPO_DATO")
            nombre = self.eat("VARIABLE")
            parametros.append(ASTNode("Parametro", nombre, tipo=tipo))
            
            while self.current_token()[0] == "COMA":
                self.eat("COMA")
                tipo = self.eat("TIPO_DATO")
                nombre = self.eat("VARIABLE")
                parametros.append(ASTNode("Parametro", nombre, tipo=tipo))
        
        return ASTNode("Parametros", hijos=parametros)

    def assignment(self):
        # Verificar si es declaración (tiene tipo explícito) o asignación
        tok_type, tok_val = self.current_token()
        es_declaracion = (tok_type == "TIPO_DATO")
        
        if es_declaracion:
            tipo_var = self.eat("TIPO_DATO")
        else:
            tipo_var = None

        var_name = self.eat("VARIABLE")
        self.eat("ASIGNACION")
        expr_node = self.expression()
        self.eat("PUNTO_COMA")

        #  NUEVO: USAR TABLA DE SÍMBOLOS EN LUGAR DE symbol_table
        if es_declaracion:
            if not self.tabla_actual.insertar_variable(var_name, tipo_var, self.ambito_actual, inicializada=True):
                raise SyntaxError(f"Variable '{var_name}' ya declarada en este ámbito")
        else:
            # Verificar que la variable existe
            simbolo = self.tabla_actual.buscar_variable(var_name)
            if not simbolo:
                raise SyntaxError(f"Variable '{var_name}' no declarada")
            self.tabla_actual.marcar_inicializada(var_name)
        
        # Marcar como usada
        self.tabla_actual.marcar_usada(var_name)

        # Obtener tipo para el nodo AST
        tipo_ast = tipo_var
        if not tipo_ast:
            simbolo = self.tabla_actual.buscar_variable(var_name)
            tipo_ast = simbolo['tipo'] if simbolo else None

        var_node = ASTNode("Variable", var_name, tipo=tipo_ast)
        return ASTNode("Asignacion", hijos=[var_node, expr_node])

    # ... (los demás métodos se mantienen igual: return_statement, parse_bloque, program, block, if_statement, while_statement, for_statement)

    def expression(self):
        return self.logical_or()

    def logical_or(self):
        nodo = self.logical_and()
        while self.current_token()[0] == "OR_LOGICO":
            op = self.eat("OR_LOGICO")
            derecho = self.logical_and()
            nodo = ASTNode("BinOp", op, [nodo, derecho], tipo="bool")
        return nodo

    def logical_and(self):
        nodo = self.equality()
        while self.current_token()[0] == "AND_LOGICO":
            op = self.eat("AND_LOGICO")
            derecho = self.equality()
            nodo = ASTNode("BinOp", op, [nodo, derecho], tipo="bool")
        return nodo

    def equality(self):
        nodo = self.comparison()
        while self.current_token()[0] in ("IGUAL_IGUAL", "DIFERENTE"):
            op = self.eat(self.current_token()[0])
            derecho = self.comparison()
            nodo = ASTNode("BinOp", op, [nodo, derecho], tipo="bool")
        return nodo

    def comparison(self):
        nodo = self.term()
        while self.current_token()[0] in ("MAYOR_QUE", "MENOR_QUE", "MAYOR_IGUAL", "MENOR_IGUAL"):
            op = self.eat(self.current_token()[0])
            derecho = self.term()
            nodo = ASTNode("BinOp", op, [nodo, derecho], tipo="bool")
        return nodo

    def term(self):
        nodo = self.factor()
        while self.current_token()[0] in ("SUMA", "RESTA"):
            op = self.eat(self.current_token()[0])
            derecho = self.factor()
            tipo_resultado = "float" if nodo.tipo == "float" or derecho.tipo == "float" else "int"
            nodo = ASTNode("BinOp", op, [nodo, derecho], tipo=tipo_resultado)
        return nodo

    def factor(self):
        nodo = self.primary()
        while self.current_token()[0] in ("MULTIPLICACION", "DIVISION", "MODULO"):
            op = self.eat(self.current_token()[0])
            derecho = self.primary()
            tipo_resultado = "float" if nodo.tipo == "float" or derecho.tipo == "float" else "int"
            nodo = ASTNode("BinOp", op, [nodo, derecho], tipo=tipo_resultado)
        return nodo

    def primary(self):
        tok_type, tok_val = self.current_token()
        if tok_type == "NUMERO":
            self.eat("NUMERO")
            tipo = "float" if "." in tok_val else "int"
            return ASTNode("Numero", tok_val, tipo=tipo)
        elif tok_type == "VARIABLE":
            self.eat("VARIABLE")
            
            # MARCAR VARIABLE COMO USADA EN TABLA DE SÍMBOLOS
            self.tabla_actual.marcar_usada(tok_val)
            
            # Obtener tipo de la tabla de símbolos
            simbolo = self.tabla_actual.buscar_variable(tok_val)
            tipo_var = simbolo['tipo'] if simbolo else None
            
            # Detectar llamada a función
            if self.current_token()[0] == "PARENTESIS_APERTURA":
                return self.function_call(tok_val)
            else:
                return ASTNode("Variable", tok_val, tipo=tipo_var)
        elif tok_type in ("TRUE", "FALSE"):
            self.eat(tok_type)
            return ASTNode("Booleano", tok_val, tipo="bool")
        elif tok_type == "PARENTESIS_APERTURA":
            self.eat("PARENTESIS_APERTURA")
            expr = self.expression()
            self.eat("PARENTESIS_CIERRE")
            return expr
        else:
            raise SyntaxError(f"Factor inválido: {tok_val}")

    def function_call(self, nombre_funcion):
        print(f"[DEBUG FUNCTION CALL] Llamando función: {nombre_funcion}")
        
        self.eat("PARENTESIS_APERTURA")
        argumentos = self.arguments()
        self.eat("PARENTESIS_CIERRE")
        
        # Obtener información de la función desde la tabla
        info_funcion = self.tabla_global.buscar_funcion(nombre_funcion)
        tipo_retorno = info_funcion['tipo_retorno'] if info_funcion else None
        
        return ASTNode("FunctionCall", nombre_funcion, 
                      hijos=[argumentos], 
                      tipo=tipo_retorno)

    def arguments(self):
        argumentos = []
        
        if self.current_token()[0] == "PARENTESIS_CIERRE":
            return ASTNode("Argumentos", hijos=argumentos)
        
        argumentos.append(self.expression())
        
        while self.current_token()[0] == "COMA":
            self.eat("COMA")
            argumentos.append(self.expression())
        
        return ASTNode("Argumentos", hijos=argumentos)

    def parse_bloque(self):
        self.eat("LLAVE_APERTURA")
        hijos = []
        while self.current_token()[0] != "LLAVE_CIERRE" and self.current_token()[0] != "EOF":
            hijo = self.parse_instruccion()
            if hijo:
                hijos.append(hijo)
        self.eat("LLAVE_CIERRE")
        return ASTNode("Bloque", hijos=hijos)
    
    def program(self):
        sentencias = []
        while self.current_token()[0] != "EOF":
            instruccion = self.parse_instruccion()
            if instruccion:
                sentencias.append(instruccion)
        return ASTNode("Program", hijos=sentencias)

    def block(self):
        self.eat("LLAVE_APERTURA")
        
        # SOLO CREAR NUEVO ÁMBITO SI NO ESTAMOS EN UN FOR
        if self.ambito_actual != "for":
            self.entrar_ambito("block")
        
        sentencias = []
        while self.current_token()[0] != "LLAVE_CIERRE" and self.current_token()[0] != "EOF":
            sentencias.append(self.parse_instruccion())
        
        self.eat("LLAVE_CIERRE")
        
        # SOLO SALIR DEL ÁMBITO SI LO CREAMOS
        if self.ambito_actual == "block":
            self.salir_ambito()
        
        return ASTNode("Bloque", hijos=sentencias)
    
    def if_statement(self):
        self.eat("IF")
        self.eat("PARENTESIS_APERTURA")
        condicion = self.expression()
        self.eat("PARENTESIS_CIERRE")
        
        bloque_if = self.block()
        
        if self.current_token()[0] == "ELSE":
            self.eat("ELSE")
            if self.current_token()[0] == "IF":
                bloque_else = self.if_statement()
            else:
                bloque_else = self.block()
            return ASTNode("If", hijos=[condicion, bloque_if, bloque_else])
        else:
            return ASTNode("If", hijos=[condicion, bloque_if])
        
    def while_statement(self):
        self.eat("WHILE")
        self.eat("PARENTESIS_APERTURA")
        condicion = self.expression()
        self.eat("PARENTESIS_CIERRE")
        bloque_while = self.block()
        return ASTNode("While", hijos=[condicion, bloque_while])
    def for_statement(self):
        self.eat("FOR")
        self.eat("PARENTESIS_APERTURA")
        
        # CREAR NUEVO ÁMBITO PARA EL FOR
        self.entrar_ambito("for")
        
        inicializacion = None
        if self.current_token()[0] != "PUNTO_COMA":
            if self.current_token()[0] == "TIPO_DATO":
                tipo_var = self.eat("TIPO_DATO")
                var_name = self.eat("VARIABLE")
                self.eat("ASIGNACION")
                expr = self.expression()
                
                # ✅ CORREGIDO: PERMITIR SHADOWING - siempre insertar sin verificar
                # El shadowing está permitido en C++ y muchos lenguajes
                self.tabla_actual.insertar_variable(var_name, tipo_var, self.ambito_actual, inicializada=True)
                
                var_node = ASTNode("Variable", var_name, tipo=tipo_var)
                inicializacion = ASTNode("Asignacion", hijos=[var_node, expr])
            else:
                # Asignación sin declaración
                var_name = self.eat("VARIABLE")
                self.eat("ASIGNACION")
                expr = self.expression()
                
                # Buscar en todos los ámbitos (padres incluidos)
                simbolo = self.tabla_actual.buscar_variable(var_name)
                if not simbolo:
                    raise SyntaxError(f"Variable '{var_name}' no declarada")
                
                var_node = ASTNode("Variable", var_name, tipo=simbolo['tipo'])
                inicializacion = ASTNode("Asignacion", hijos=[var_node, expr])
        
        self.eat("PUNTO_COMA")
        
        condicion = None
        if self.current_token()[0] != "PUNTO_COMA":
            condicion = self.expression()
        self.eat("PUNTO_COMA")
        
        incremento = None
        if self.current_token()[0] != "PARENTESIS_CIERRE":
            current_type, current_val = self.current_token()
            next_type = self.tokens[self.pos + 1][0] if self.pos + 1 < len(self.tokens) else None
            
            if current_type == "VARIABLE" and next_type == "ASIGNACION":
                var_name = self.eat("VARIABLE")
                self.eat("ASIGNACION")
                expr = self.expression()
                
                simbolo = self.tabla_actual.buscar_variable(var_name)
                if not simbolo:
                    raise SyntaxError(f"Variable '{var_name}' no declarada")
                
                var_node = ASTNode("Variable", var_name, tipo=simbolo['tipo'])
                incremento = ASTNode("Asignacion", hijos=[var_node, expr])
            else:
                incremento = self.expression()
        
        self.eat("PARENTESIS_CIERRE")
        
        # PROCESAR BLOQUE EN EL MISMO ÁMBITO FOR
        bloque = self.block()
        
        # SALIR DEL ÁMBITO FOR
        self.salir_ambito()
        
        return ASTNode("For", hijos=[inicializacion, condicion, incremento, bloque])

    def return_statement(self):
        print(f"[DEBUG RETURN] Iniciando return. Token: {self.current_token()}")
        self.eat("RETURN")
        
        expresion = None
        current_tok_type = self.current_token()[0]
        
        if current_tok_type != "PUNTO_COMA":
            print(f"[DEBUG RETURN] Procesando expresión completa...")
            print(f"[DEBUG RETURN] Token antes de expression(): {self.current_token()}")
            
            try:
                expresion = self.expression()
                print(f"[DEBUG RETURN] Expresión exitosa: {expresion.nombre}")
                print(f"[DEBUG RETURN] Token después de expression(): {self.current_token()}")
            except Exception as e:
                print(f"[DEBUG RETURN] Error en expresión: {e}")
                raise
        
        print(f"[DEBUG RETURN] Comiendo PUNTO_COMA. Token actual: {self.current_token()}")
        self.eat("PUNTO_COMA")
        print(f"[DEBUG RETURN] Return completado exitosamente")
        
        if expresion:
            return ASTNode("Return", hijos=[expresion])
        else:
            return ASTNode("Return", hijos=[])

class ASTNode:
    def __init__(self, nombre, valor=None, hijos=None, tipo=None):
        self.nombre = nombre
        self.valor = valor
        self.hijos = hijos or []
        self.tipo = tipo