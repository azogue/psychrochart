# -*- coding: utf-8 -*-
"""
A python library to make psychrometric charts and overlay information in them.

"""

COLOR_PALETTE = {
    'capacidad_gen': [0.886, 0.0, 0.102],
    'color_amarillo_q_sol': [1.0, 0.749, 0.0],
    'color_azul_cl_q_ve': [0.0, 0.8, 0.6],
    'color_azul_claro': [0.498, 0.875, 1.0],
    'color_azul_oscuro': [0.0, 0.125, 0.376],
    'color_azul_q_tr_w': [0.498, 0.624, 1.0],
    'color_azul_refrig': [0.0, 0.2, 0.8],
    'color_azul_refrig_atenuado': [0.0, 0.498, 1.0],
    'color_berenjena': [0.251, 0.0, 0.502],
    'color_blanco': [1.0, 1.0, 1.0],
    'color_castanyo': [0.502, 0.0, 0.251],
    'color_ciruela': [0.498, 0.0, 0.498],
    'color_cumple': [0.0, 0.573, 0.247],
    'color_cumple_fondo': [0.773, 0.91, 0.749],
    'color_energia_biomasa': [0.259, 0.447, 0.102],
    'color_energia_biomasa_dens': [0.212, 0.365, 0.098],
    'color_energia_carbon': [0.247, 0.188, 0.039],
    'color_energia_electricidad': [0.102, 0.314, 0.518],
    'color_energia_gas_natural': [0.698, 0.431, 0.875],
    'color_energia_gasoleo_c': [0.573, 0.322, 0.067],
    'color_energia_glp': [0.573, 0.106, 0.318],
    'color_energia_solar_fv': [0.161, 0.973, 0.584],
    'color_energia_solar_term': [0.569, 0.969, 0.188],
    'color_escala_iee_clase_a': [0.475, 0.612, 0.075],
    'color_escala_iee_clase_b': [0.592, 0.745, 0.051],
    'color_escala_iee_clase_c': [0.831, 0.839, 0.0],
    'color_escala_iee_clase_d': [0.992, 0.765, 0.0],
    'color_escala_iee_clase_e': [0.949, 0.58, 0.0],
    'color_escala_iee_clase_f': [0.914, 0.369, 0.059],
    'color_escala_iee_clase_g': [0.886, 0.0, 0.102],
    'color_gris': [0.737, 0.737, 0.737],
    'color_gris_claro': [0.859, 0.859, 0.859],
    'color_gris_claro_fondo': [0.984, 0.973, 0.984],
    'color_gris_hierro': [0.298, 0.298, 0.298],
    'color_gris_menos_claro_fondo': [0.765, 0.722, 0.78],
    'color_gris_oscuro': [0.376, 0.376, 0.376],
    'color_marca_agua_no_cumple': [1.0, 0.486, 0.502],
    'color_marron_q_tr_op': [0.6, 0.298, 0.0],
    'color_morado_claro': [0.765, 0.663, 0.918],
    'color_morado_q_int_l': [0.8, 0.0, 0.8],
    'color_morado_q_int_s': [0.6, 0.0, 0.6],
    'color_naranja_claro': [1.0, 0.769, 0.533],
    'color_naranja_fondo': [0.98, 0.749, 0.561],
    'color_naranja_q_acople': [1.0, 0.498, 0.0],
    'color_naranja_q_acople_osc': [0.75, 0.374, 0.0],
    'color_negro': [0.0, 0.0, 0.0],
    'color_negro_q_edif': [0.298, 0.0, 0.075],
    'color_no_cumple': [0.855, 0.145, 0.114],
    'color_no_cumple_fondo': [0.973, 0.769, 0.753],
    'color_rojo': [1.0, 0.0, 0.0],
    'color_rojo_calef': [1.0, 0.0, 0.247],
    'color_rojo_calef_atenuado': [1.0, 0.498, 0.624],
    'color_salmon': [1.0, 0.4, 0.4],
    'color_verde_flora': [0.4, 1.0, 0.4],
    'color_verde_valor_medio': [0.0, 0.498, 0.0],
    'consumo_calor': [0.859, 0.0, 0.6],
    'consumo_frio': [0.427, 0.004, 0.855],
    'consumo_gen': [0.855, 0.004, 0.278],
    'fcp': [0.243, 0.216, 0.416],
    'rendimiento_calor': [0.376, 0.502, 0.0],
    'rendimiento_frio': [0.0, 0.502, 0.337],
    'rendimiento_gen': [0.0, 0.498, 0.0],
    'temp_ext': [0.855, 0.278, 0.004]
}

# COLOR_PALETTE = {
#     'color_amarillo_q_sol': (255, 191, 0),
#     'color_morado_q_int_l': (204, 0, 204),
#     'color_morado_q_int_s': (153, 0, 153),
#     'color_rojo': (255, 0, 0),
#     'color_rojo_calef': (255, 0, 63),
#     'color_rojo_calef_atenuado': (255, 127, 159),
#     'color_azul_refrig': (0, 51, 204),
#     'color_azul_refrig_atenuado': (0, 127, 255),
#     'color_azul_cl_q_ve': (0, 204, 153),
#     'color_azul_claro': (127, 223, 255),
#     'color_marron_q_tr_op': (153, 76, 0),
#     'color_azul_q_tr_w': (127, 159, 255),
#     'color_negro_q_edif': (76, 0, 19),
#     'color_naranja_q_acople': (255, 127, 0),
#     'color_naranja_q_acople_osc': (191.25, 95.25, 0),
#     'color_verde_valor_medio': (0, 127, 0),
#     'color_blanco': (255, 255, 255),
#     'color_gris': (188, 188, 188),
#     'color_gris_claro': (219, 219, 219),
#     'color_gris_oscuro': (96, 96, 96),
#     'consumo_calor': (219, 0, 153),
#     'consumo_frio': (109, 1, 218),
#     'consumo_gen': (218, 1, 71),
#     'rendimiento_calor': (96, 128, 0),
#     'rendimiento_frio': (0, 128, 86),
#     'rendimiento_gen': (0, 127, 0),
#     'capacidad_gen': (226, 0, 26),
#     'temp_ext': (218, 71, 1),
#     'fcp': (62, 55, 106),
#     'color_energia_electricidad': (26, 80, 132),
#     'color_energia_gas_natural': (178, 110, 223),
#     'color_energia_gasoleo_c': (146, 82, 17),
#     'color_energia_glp': (146, 27, 81),
#     'color_energia_carbon': (63, 48, 10),
#     'color_energia_biomasa': (66, 114, 26),
#     'color_energia_biomasa_dens': (54, 93, 25),
#     'color_energia_solar_term': (145, 247, 48),
#     'color_energia_solar_fv': (41, 248, 149),
#     'color_castanyo': (128, 0, 64),
#     'color_berenjena': (64, 0, 128),
#     'color_ciruela': (127, 0, 127),
#     'color_salmon': (255, 102, 102),
#     'color_verde_flora': (102, 255, 102),
#     'color_gris_hierro': (76, 76, 76),
#     'color_escala_iee_clase_a': (121, 156, 19),
#     'color_escala_iee_clase_b': (151, 190, 13),
#     'color_escala_iee_clase_c': (212, 214, 0),
#     'color_escala_iee_clase_d': (253, 195, 0),
#     'color_escala_iee_clase_e': (242, 148, 0),
#     'color_escala_iee_clase_f': (233, 94, 15),
#     'color_escala_iee_clase_g': (226, 0, 26),
#     'color_gris_claro_fondo': (251, 248, 251),
#     'color_gris_menos_claro_fondo': (195, 184, 199),
#     'color_morado_claro': (195, 169, 234),
#     'color_naranja_claro': (255, 196, 136),
#     'color_negro': (0, 0, 0),
#     'color_cumple': (0, 146, 63),
#     'color_cumple_fondo': (197, 232, 191),
#     'color_no_cumple': (218, 37, 29),
#     'color_no_cumple_fondo': (248, 196, 192),
#     'color_marca_agua_no_cumple': (255, 124, 128),
#     'color_naranja_fondo': (250, 191, 143),
#     'color_azul_oscuro': (0, 32, 96),
# }


def _mod_color(color, modification):
    if abs(modification) < .999:  # is alpha level
        color = list(color) + [modification]
    else:
        color = [max(0., min(1., c * (1 + modification / 100)))
                 for c in color]
    return color


def _rgba(color, nivel_alpha=None):
    # color = [c / 255 for c in color]
    if nivel_alpha is not None:
        color = _mod_color(color, nivel_alpha)
    return color


def get_color_palette(key_color, alpha=None):
    """Return a color from the palette as 3/4 [0,1] values."""
    color = COLOR_PALETTE[key_color]
    if alpha is not None:
        return _rgba(color, alpha)
    else:
        return _rgba(color)
