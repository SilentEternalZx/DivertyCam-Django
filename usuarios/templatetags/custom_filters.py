from django import template
import json

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Obtiene un elemento de un diccionario o lista usando una clave o índice.
    Maneja múltiples tipos de datos para mayor robustez.
    """
    if dictionary is None:
        return None
    
    try:
        # Si es un string JSON, intentar parsear
        if isinstance(dictionary, str):
            dictionary = json.loads(dictionary)
            
        # Si es un diccionario, acceder directamente
        if isinstance(dictionary, dict):
            return dictionary.get(str(key))
        
        # Si es una lista, intentar acceder por índice
        if isinstance(dictionary, list):
            index = int(key)
            if 0 <= index < len(dictionary):
                return dictionary[index]
            
    except (ValueError, TypeError, json.JSONDecodeError):
        pass
    
    return None