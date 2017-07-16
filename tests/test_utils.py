# -*- coding: utf-8 -*-
"""
Tests utilities

"""
import json
import os
from unittest import TestCase


basedir = os.path.dirname(os.path.abspath(__file__))
PATH_CONFIG_UPDATE = os.path.join(basedir, 'test_chart_config_update.json')


class TestsPsychroUtils(TestCase):
    """Unit Tests to check the psychrometric equations."""

    def test_load_plot_config(self):
        """Test the plot custom styling with JSON files/dicts."""
        from psychrochart.util import load_config, DEFAULT_CHART_CONFIG_FILE

        # Test load default config
        default_config = load_config()

        # Test passing dict vs JSON path:
        config_2 = load_config(styles=DEFAULT_CHART_CONFIG_FILE)
        with open(DEFAULT_CHART_CONFIG_FILE) as f:
            config_3 = load_config(styles=json.load(f))
        self.assertEqual(config_2, config_3)

        # Test update config:
        config_custom = load_config(styles=PATH_CONFIG_UPDATE,
                                    verbose=True)
        self.assertNotEqual(default_config, config_custom)
        self.assertIn('constant_h', config_custom)
        self.assertIn('constant_v', config_custom)
        self.assertNotIn('test_fake_param', config_custom)

        # Test config styles:
        default_config_s = load_config(
            styles="default", verbose=True)
        self.assertEqual(default_config, default_config_s)

        ashrae_config_s = load_config(
            styles="ashrae", verbose=True)
        self.assertNotEqual(default_config, ashrae_config_s)


class TestsCLI(TestCase):
    """Unit Tests to check the CLI."""

    def test_cli_main(self):
        """Unit test for the CLI entry point."""
        # noinspection PyUnresolvedReferences
        import psychrochart.agg
        from psychrochart.__main__ import main

        main()


class TestsColorUtils(TestCase):
    """Unit Tests to check some color modification methods."""

    def test_color_palette(self):
        """Test rgba utilities."""
        from psychrochart.util import mod_color

        def _to_8bit_color(color):
            return tuple([int(round(255 * c)) if i < 3 else c
                          for i, c in enumerate(color)])

        color_base = [0.475, 0.612, 0.075]
        self.assertEqual(_to_8bit_color(color_base), (121, 156, 19))

        color_light_20 = mod_color(color_base, 20)
        self.assertEqual(_to_8bit_color(color_light_20), (145, 187, 23))

        color_dark_40 = mod_color(color_base, -40)
        self.assertEqual(_to_8bit_color(color_dark_40), (73, 94, 11))

        color_alpha_08 = mod_color(color_base, .8)
        self.assertEqual(_to_8bit_color(color_alpha_08), (121, 156, 19, 0.8))
