from django.template import Library

register = Library()

@register.filter
def get_dict_value(dictionary, key):
    return dictionary[key]