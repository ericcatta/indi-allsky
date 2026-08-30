#!/usr/bin/env python3

import ast
import copy
import hashlib
import json
import sys
from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import is_dataclass
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from indi_allsky.modern_admin_settings_runtime import ModernAdminFullConfigAcquisitionModeParser
from indi_allsky.modern_admin_settings_runtime import ModernAdminFullConfigCameraConnectionParser
from indi_allsky.modern_admin_settings_runtime import ModernAdminFullConfigExposureGainParser
from indi_allsky.modern_admin_settings_runtime import ModernAdminFullConfigLensGeometryParser
from indi_allsky.modern_admin_settings_runtime import ModernAdminFullConfigLensMetadataParser
from indi_allsky.modern_admin_settings_runtime import ModernAdminFullConfigPayloadPreparationService
from indi_allsky.modern_admin_settings_runtime import ModernAdminFullConfigStationIdentityParser


VIEWS_PATH = Path(__file__).resolve().parents[1] / 'indi_allsky' / 'flask' / 'views.py'


@dataclass(frozen=True)
class FullConfigParserResult:
    config: dict
    reload_on_save: bool
    config_note: str


class LegacyFullConfigParserHarness:
    """Execute the pure mutation block of AjaxConfigView for parity checks."""

    JSON_FIELDS = (
        'FILETRANSFER__LIBCURL_OPTIONS',
        'INDI_CONFIG_DEFAULTS',
        'INDI_CONFIG_DAY',
    )

    COLOR_FIELDS = (
        'TEXT_PROPERTIES__FONT_COLOR',
        'CARDINAL_DIRS__FONT_COLOR',
        'ORB_PROPERTIES__SUN_COLOR',
        'ORB_PROPERTIES__MOON_COLOR',
        'IMAGE_BORDER__COLOR',
        'LIGHTGRAPH_OVERLAY__DAY_COLOR',
        'LIGHTGRAPH_OVERLAY__DUSK_COLOR',
        'LIGHTGRAPH_OVERLAY__NIGHT_COLOR',
        'LIGHTGRAPH_OVERLAY__MOONMODE_COLOR',
        'LIGHTGRAPH_OVERLAY__HOUR_COLOR',
        'LIGHTGRAPH_OVERLAY__BORDER_COLOR',
        'LIGHTGRAPH_OVERLAY__NOW_COLOR',
        'LIGHTGRAPH_OVERLAY__FONT_COLOR',
    )

    GOLDEN_FINGERPRINTS = {
        'standard': '5447b4ca1db321a02ad5fb24689d3621120f1ccc97a58cce410d96fd6d30fdaa',
        'roi_disabled': '99488173572f652ea383680a082bb19721d3dfb7d3df844e434b0445427bf9e6',
        'invalid_color': 'e73182498be70a84834d303141ffac48c607f99bbce8cf293b9f89660b069fa2',
        'compat': 'b158691cfbb3e7ca3bf79c97d044c99da12e58f5fee14eec6bf70a8849085291',
    }

    HYBRID_PARSERS = (
        ModernAdminFullConfigCameraConnectionParser,
        ModernAdminFullConfigStationIdentityParser,
        ModernAdminFullConfigLensMetadataParser,
        ModernAdminFullConfigLensGeometryParser,
        ModernAdminFullConfigExposureGainParser,
        ModernAdminFullConfigAcquisitionModeParser,
    )

    def __init__(self, source_path=VIEWS_PATH):
        self.source_path = Path(source_path)
        self.parser_statements = self.extract_parser_statements()
        self.code = compile(
            ast.fix_missing_locations(ast.Module(body=self.parser_statements, type_ignores=[])),
            str(self.source_path),
            'exec',
        )
        self.direct_payload_keys, self.optional_payload_keys = self.extract_payload_keys()
        self.required_payload_keys = tuple(sorted(
            set(self.direct_payload_keys)
            | {
                field_name
                for parser_class in self.HYBRID_PARSERS
                for field_name in parser_class.REQUIRED_FIELDS
            }
        ))


    def extract_parser_statements(self):
        tree = ast.parse(self.source_path.read_text())
        ajax_class = next(
            node for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == 'AjaxConfigView'
        )
        dispatch = next(
            node for node in ajax_class.body
            if isinstance(node, ast.FunctionDef) and node.name == 'dispatch_request'
        )

        start_index = next(
            index for index, statement in enumerate(dispatch.body)
            if 'full_config_payload_preparation_service().prepare' in ast.unparse(statement)
        )
        end_index = next(
            index for index, statement in enumerate(dispatch.body[start_index + 1:], start_index + 1)
            if isinstance(statement, ast.If) and 'LOGIN_DISABLED' in ast.unparse(statement.test)
        )
        return dispatch.body[start_index + 1:end_index]


    def extract_payload_keys(self):
        direct_keys = set()
        optional_keys = set()
        module = ast.Module(body=self.parser_statements, type_ignores=[])

        for node in ast.walk(module):
            if isinstance(node, ast.Subscript) and ast.unparse(node.value) == 'request.json':
                if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
                    direct_keys.add(node.slice.value)

            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == 'get'
                and ast.unparse(node.func.value) == 'request.json'
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
            ):
                optional_keys.add(node.args[0].value)

        return tuple(sorted(direct_keys)), tuple(sorted(optional_keys))


    def build_payload(self, overrides=None):
        payload = {
            key: 1
            for key in set(self.required_payload_keys) | set(self.optional_payload_keys)
        }
        for key in self.JSON_FIELDS:
            payload[key] = '{}'
        for key in self.COLOR_FIELDS:
            payload[key] = '1,2,3'
        payload['YOUTUBE__TAGS_STR'] = 'alpha, beta, alpha'
        payload['CONFIG_NOTE'] = 'Parity corpus save'

        if overrides:
            payload.update(overrides)
        return payload


    def prepare_config(self, initial_config=None):
        config = copy.deepcopy({} if initial_config is None else initial_config)
        return ModernAdminFullConfigPayloadPreparationService().prepare(config)


    def execute_legacy(self, config, payload):
        namespace = {
            'json': json,
            'request': SimpleNamespace(json=payload),
            'self': SimpleNamespace(
                indi_allsky_config=config,
                full_config_camera_connection_parser=(
                    lambda: ModernAdminFullConfigCameraConnectionParser()
                ),
                full_config_station_identity_parser=(
                    lambda: ModernAdminFullConfigStationIdentityParser()
                ),
                full_config_lens_metadata_parser=(
                    lambda: ModernAdminFullConfigLensMetadataParser()
                ),
                full_config_lens_geometry_parser=(
                    lambda: ModernAdminFullConfigLensGeometryParser()
                ),
                full_config_exposure_gain_parser=(
                    lambda: ModernAdminFullConfigExposureGainParser()
                ),
                full_config_acquisition_mode_parser=(
                    lambda: ModernAdminFullConfigAcquisitionModeParser()
                ),
            ),
        }
        exec(self.code, namespace)
        return FullConfigParserResult(
            config=config,
            reload_on_save=namespace['reload_on_save'],
            config_note=namespace['config_note'],
        )


    def run_legacy(self, initial_config=None, payload=None):
        return self.execute_legacy(
            self.prepare_config(initial_config),
            self.build_payload() if payload is None else payload,
        )


    def capture(self, parser, config, payload):
        try:
            return ('result', parser(config, payload))
        except Exception as error:
            return ('error', error.__class__, str(error), config)


    def canonicalize(self, value, path=()):
        if is_dataclass(value):
            return self.canonicalize(asdict(value), path)
        if isinstance(value, type):
            return '{0:s}.{1:s}'.format(value.__module__, value.__qualname__)
        if isinstance(value, dict):
            return {
                key: self.canonicalize(item, path + (key,))
                for key, item in value.items()
            }
        if isinstance(value, (list, tuple)):
            canonical_items = [
                self.canonicalize(item, path + (index,))
                for index, item in enumerate(value)
            ]
            if path[-2:] == ('YOUTUBE', 'TAGS'):
                return sorted(canonical_items)
            return canonical_items
        return value


    def fingerprint(self, value):
        canonical_json = json.dumps(
            self.canonicalize(value),
            sort_keys=True,
            separators=(',', ':'),
            default=str,
        )
        return hashlib.sha256(canonical_json.encode()).hexdigest()


    def assert_parity(self, candidate_parser, initial_config=None, payload=None):
        payload = self.build_payload() if payload is None else payload
        expected = self.capture(
            self.execute_legacy,
            self.prepare_config(initial_config),
            payload,
        )
        actual = self.capture(
            candidate_parser,
            self.prepare_config(initial_config),
            payload,
        )
        assert actual == expected


def test_parity_corpus_covers_current_legacy_parser_contract():
    harness = LegacyFullConfigParserHarness()

    assert len(harness.direct_payload_keys) == 691
    assert len(harness.required_payload_keys) == 719
    for parser_class in harness.HYBRID_PARSERS:
        assert set(parser_class.REQUIRED_FIELDS).issubset(harness.required_payload_keys)
    assert set(harness.JSON_FIELDS).issubset(harness.required_payload_keys)
    assert set(harness.COLOR_FIELDS).issubset(harness.required_payload_keys)
    assert 'YOUTUBE__TAGS_STR' in harness.required_payload_keys
    assert 'RELOAD_ON_SAVE' in harness.required_payload_keys
    assert 'CONFIG_NOTE' in harness.required_payload_keys


def test_camera_connection_parser_preserves_legacy_casting_and_required_fields():
    parser = ModernAdminFullConfigCameraConnectionParser()
    config = {}
    payload = {
        'CAMERA_INTERFACE': 42,
        'INDI_SERVER': 'localhost',
        'INDI_PORT': '7624',
        'INDI_CAMERA_NAME': True,
    }

    assert parser.apply(config, payload) is config
    assert config == {
        'CAMERA_INTERFACE': '42',
        'INDI_SERVER': 'localhost',
        'INDI_PORT': 7624,
        'INDI_CAMERA_NAME': 'True',
    }

    for missing_field in parser.REQUIRED_FIELDS:
        incomplete_payload = dict(payload)
        incomplete_payload.pop(missing_field)
        try:
            parser.apply({}, incomplete_payload)
        except KeyError as error:
            assert error.args == (missing_field,)
        else:
            raise AssertionError('{0:s} should remain required'.format(missing_field))


def test_station_identity_parser_preserves_legacy_casting_and_required_fields():
    parser = ModernAdminFullConfigStationIdentityParser()
    config = {'WEBSITE': {'LEGACY_VALUE': 'preserve'}}
    payload = {
        'WEBSITE__TITLE': 42,
        'OWNER': True,
    }

    assert parser.apply(config, payload) is config
    assert config == {
        'WEBSITE': {
            'LEGACY_VALUE': 'preserve',
            'TITLE': '42',
        },
        'OWNER': 'True',
    }

    for missing_field in parser.REQUIRED_FIELDS:
        incomplete_payload = dict(payload)
        incomplete_payload.pop(missing_field)
        try:
            parser.apply({'WEBSITE': {}}, incomplete_payload)
        except KeyError as error:
            assert error.args == (missing_field,)
        else:
            raise AssertionError('{0:s} should remain required'.format(missing_field))


def test_lens_metadata_parser_preserves_legacy_casting_and_required_fields():
    parser = ModernAdminFullConfigLensMetadataParser()
    config = {}
    payload = {
        'LENS_NAME': 42,
        'LENS_FOCAL_LENGTH': '2.5',
        'LENS_FOCAL_RATIO': 2,
    }

    assert parser.apply(config, payload) is config
    assert config == {
        'LENS_NAME': '42',
        'LENS_FOCAL_LENGTH': 2.5,
        'LENS_FOCAL_RATIO': 2.0,
    }

    for missing_field in parser.REQUIRED_FIELDS:
        incomplete_payload = dict(payload)
        incomplete_payload.pop(missing_field)
        try:
            parser.apply({}, incomplete_payload)
        except KeyError as error:
            assert error.args == (missing_field,)
        else:
            raise AssertionError('{0:s} should remain required'.format(missing_field))


def test_lens_geometry_parser_preserves_legacy_casting_and_required_fields():
    parser = ModernAdminFullConfigLensGeometryParser()
    config = {}
    payload = {
        'LENS_IMAGE_CIRCLE': '3000',
        'LENS_OFFSET_X': '-12',
        'LENS_OFFSET_Y': 34,
        'LENS_ALTITUDE': '90.0',
        'LENS_AZIMUTH': 180,
    }

    assert parser.apply(config, payload) is config
    assert config == {
        'LENS_IMAGE_CIRCLE': 3000,
        'LENS_OFFSET_X': -12,
        'LENS_OFFSET_Y': 34,
        'LENS_ALTITUDE': 90.0,
        'LENS_AZIMUTH': 180.0,
    }

    for missing_field in parser.REQUIRED_FIELDS:
        incomplete_payload = dict(payload)
        incomplete_payload.pop(missing_field)
        try:
            parser.apply({}, incomplete_payload)
        except KeyError as error:
            assert error.args == (missing_field,)
        else:
            raise AssertionError('{0:s} should remain required'.format(missing_field))


def test_exposure_gain_parser_preserves_legacy_casting_and_rounding():
    parser = ModernAdminFullConfigExposureGainParser()
    config = {
        'CCD_CONFIG': {
            'NIGHT': {},
            'MOONMODE': {},
            'DAY': {},
        },
    }
    payload = {
        'CCD_CONFIG__NIGHT__GAIN': '12.3456',
        'CCD_CONFIG__MOONMODE__GAIN': 23.4567,
        'CCD_CONFIG__DAY__GAIN': '34.5678',
        'CCD_EXPOSURE_MAX': '1.1234567',
        'CCD_EXPOSURE_DEF': 2.2345678,
        'CCD_EXPOSURE_MIN': '0.0000014',
        'CCD_EXPOSURE_MIN_DAY': 0.0000026,
        'CCD_EXPOSURE_TIMEOUT': '330',
        'EXPOSURE_PERIOD': '45.5',
        'EXPOSURE_PERIOD_DAY': 15,
    }

    assert parser.apply_night_gain(config, payload) is config
    assert parser.apply_moonmode_gain(config, payload) is config
    assert parser.apply_day_gain(config, payload) is config
    assert parser.apply_exposure_limits(config, payload) is config
    assert parser.apply_exposure_periods(config, payload) is config
    assert config == {
        'CCD_CONFIG': {
            'NIGHT': {'GAIN': 12.35},
            'MOONMODE': {'GAIN': 23.46},
            'DAY': {'GAIN': 34.57},
        },
        'CCD_EXPOSURE_MAX': 1.123457,
        'CCD_EXPOSURE_DEF': 2.234568,
        'CCD_EXPOSURE_MIN': 0.000001,
        'CCD_EXPOSURE_MIN_DAY': 0.000003,
        'CCD_EXPOSURE_TIMEOUT': 330,
        'EXPOSURE_PERIOD': 45.5,
        'EXPOSURE_PERIOD_DAY': 15.0,
    }


def test_acquisition_mode_parser_preserves_legacy_integer_casting():
    parser = ModernAdminFullConfigAcquisitionModeParser()
    config = {
        'CCD_CONFIG': {
            'NIGHT': {},
            'MOONMODE': {},
            'DAY': {},
        },
    }
    payload = {
        'CCD_CONFIG__NIGHT__BINNING': '1',
        'CCD_CONFIG__MOONMODE__BINNING': 2,
        'CCD_CONFIG__DAY__BINNING': '4',
        'CCD_BIT_DEPTH': '16',
    }

    assert parser.apply_night_binning(config, payload) is config
    assert parser.apply_moonmode_binning(config, payload) is config
    assert parser.apply_day_binning(config, payload) is config
    assert parser.apply_bit_depth(config, payload) is config
    assert config == {
        'CCD_CONFIG': {
            'NIGHT': {'BINNING': 1},
            'MOONMODE': {'BINNING': 2},
            'DAY': {'BINNING': 4},
        },
        'CCD_BIT_DEPTH': 16,
    }


def test_ajax_config_view_delegates_camera_connection_parsing():
    harness = LegacyFullConfigParserHarness()
    parser_source = '\n'.join(ast.unparse(statement) for statement in harness.parser_statements)

    assert 'full_config_camera_connection_parser().apply' in parser_source
    for field_name in ModernAdminFullConfigCameraConnectionParser.REQUIRED_FIELDS:
        assert "indi_allsky_config['{0:s}'] =".format(field_name) not in parser_source


def test_ajax_config_view_delegates_station_identity_parsing():
    harness = LegacyFullConfigParserHarness()
    parser_source = '\n'.join(ast.unparse(statement) for statement in harness.parser_statements)

    assert 'full_config_station_identity_parser().apply' in parser_source
    assert "indi_allsky_config['WEBSITE']['TITLE'] =" not in parser_source
    assert "indi_allsky_config['OWNER'] =" not in parser_source


def test_ajax_config_view_delegates_lens_metadata_parsing():
    harness = LegacyFullConfigParserHarness()
    parser_source = '\n'.join(ast.unparse(statement) for statement in harness.parser_statements)

    assert 'full_config_lens_metadata_parser().apply' in parser_source
    for field_name in ModernAdminFullConfigLensMetadataParser.REQUIRED_FIELDS:
        assert "indi_allsky_config['{0:s}'] =".format(field_name) not in parser_source


def test_ajax_config_view_delegates_lens_geometry_parsing():
    harness = LegacyFullConfigParserHarness()
    parser_source = '\n'.join(ast.unparse(statement) for statement in harness.parser_statements)

    assert 'full_config_lens_geometry_parser().apply' in parser_source
    for field_name in ModernAdminFullConfigLensGeometryParser.REQUIRED_FIELDS:
        assert "indi_allsky_config['{0:s}'] =".format(field_name) not in parser_source


def test_ajax_config_view_delegates_exposure_gain_parsing_in_legacy_order():
    harness = LegacyFullConfigParserHarness()
    parser_source = '\n'.join(ast.unparse(statement) for statement in harness.parser_statements)

    expected_calls = (
        'apply_night_gain',
        'apply_moonmode_gain',
        'apply_day_gain',
        'apply_exposure_limits',
        'apply_exposure_periods',
    )
    call_positions = [parser_source.index(call_name) for call_name in expected_calls]
    assert call_positions == sorted(call_positions)
    for field_name in ModernAdminFullConfigExposureGainParser.REQUIRED_FIELDS:
        assert field_name not in harness.direct_payload_keys


def test_ajax_config_view_delegates_acquisition_mode_in_legacy_order():
    harness = LegacyFullConfigParserHarness()
    parser_source = '\n'.join(ast.unparse(statement) for statement in harness.parser_statements)

    expected_calls = (
        'apply_night_gain',
        'apply_night_binning',
        'apply_moonmode_gain',
        'apply_moonmode_binning',
        'apply_day_gain',
        'apply_day_binning',
        'apply_exposure_limits',
        'apply_bit_depth',
        'apply_exposure_periods',
    )
    call_positions = [parser_source.index(call_name) for call_name in expected_calls]
    assert call_positions == sorted(call_positions)
    for field_name in ModernAdminFullConfigAcquisitionModeParser.REQUIRED_FIELDS:
        assert field_name not in harness.direct_payload_keys


def test_exposure_gain_parser_preserves_partial_mutation_order_on_errors():
    harness = LegacyFullConfigParserHarness()
    invalid_binning = harness.capture(
        harness.execute_legacy,
        harness.prepare_config(),
        harness.build_payload({'CCD_CONFIG__NIGHT__BINNING': 'invalid'}),
    )
    assert invalid_binning[0:3] == (
        'error',
        ValueError,
        "invalid literal for int() with base 10: 'invalid'",
    )
    invalid_binning_config = invalid_binning[3]
    assert invalid_binning_config['CCD_CONFIG']['NIGHT']['GAIN'] == 1.0
    assert 'GAIN' not in invalid_binning_config['CCD_CONFIG']['MOONMODE']
    assert 'CCD_EXPOSURE_MAX' not in invalid_binning_config

    invalid_bit_depth = harness.capture(
        harness.execute_legacy,
        harness.prepare_config(),
        harness.build_payload({'CCD_BIT_DEPTH': 'invalid'}),
    )
    assert invalid_bit_depth[0:2] == ('error', ValueError)
    invalid_bit_depth_config = invalid_bit_depth[3]
    assert invalid_bit_depth_config['CCD_EXPOSURE_TIMEOUT'] == 1
    assert 'EXPOSURE_PERIOD' not in invalid_bit_depth_config


def test_full_config_parser_matches_pre_migration_golden_fingerprints():
    harness = LegacyFullConfigParserHarness()
    roi_disabled_payload = harness.build_payload({
        'ADU_ROI_X2': 0,
        'ADU_ROI_Y2': 0,
        'SQM_ROI_X2': 0,
        'SQM_ROI_Y2': 0,
        'IMAGE_CROP_ROI_X2': 0,
        'IMAGE_CROP_ROI_Y2': 0,
        'RELOAD_ON_SAVE': False,
    })
    invalid_color_payload = harness.build_payload({
        'TEXT_PROPERTIES__FONT_COLOR': 'invalid-color',
    })
    compatibility_config = {
        'CUSTOM_COMPATIBILITY_KEY': {'preserve': True},
        'WEBSITE': {'LEGACY_VALUE': 'preserve'},
        'FITSHEADERS': [
            ['OBSERVER', 'Hybrid'],
            ['', ''],
            ['', ''],
            ['', ''],
            ['', ''],
        ],
    }
    cases = {
        'standard': harness.capture(
            harness.execute_legacy,
            harness.prepare_config(),
            harness.build_payload(),
        ),
        'roi_disabled': harness.capture(
            harness.execute_legacy,
            harness.prepare_config(),
            roi_disabled_payload,
        ),
        'invalid_color': harness.capture(
            harness.execute_legacy,
            harness.prepare_config(),
            invalid_color_payload,
        ),
        'compat': harness.capture(
            harness.execute_legacy,
            harness.prepare_config(compatibility_config),
            harness.build_payload(),
        ),
    }

    assert {
        name: harness.fingerprint(result)
        for name, result in cases.items()
    } == harness.GOLDEN_FINGERPRINTS


def test_golden_fingerprint_normalizes_legacy_unordered_youtube_tags():
    harness = LegacyFullConfigParserHarness()
    first = {'config': {'YOUTUBE': {'TAGS': ['alpha', 'beta']}}}
    second = {'config': {'YOUTUBE': {'TAGS': ['beta', 'alpha']}}}

    assert harness.fingerprint(first) == harness.fingerprint(second)


def test_legacy_parser_corpus_executes_success_and_edge_paths():
    harness = LegacyFullConfigParserHarness()
    initial_config = {
        'CUSTOM_COMPATIBILITY_KEY': {'preserve': True},
        'WEBSITE': {'LEGACY_VALUE': 'preserve'},
        'FITSHEADERS': [
            ['OBSERVER', 'Hybrid'],
            ['', ''],
            ['', ''],
            ['', ''],
            ['', ''],
        ],
    }

    result = harness.run_legacy(initial_config=initial_config)
    assert result.config['CUSTOM_COMPATIBILITY_KEY'] == {'preserve': True}
    assert result.config['WEBSITE']['LEGACY_VALUE'] == 'preserve'
    assert result.config['FITSHEADERS'] is not initial_config['FITSHEADERS']
    assert result.config['ADU_ROI'] == [1, 1, 1, 1]
    assert sorted(result.config['YOUTUBE']['TAGS']) == ['alpha', 'beta']
    assert result.reload_on_save is True
    assert result.config_note == 'Parity corpus save'

    disabled_roi = harness.run_legacy(payload=harness.build_payload({
        'ADU_ROI_X2': 0,
        'ADU_ROI_Y2': 0,
        'SQM_ROI_X2': 0,
        'SQM_ROI_Y2': 0,
        'IMAGE_CROP_ROI_X2': 0,
        'IMAGE_CROP_ROI_Y2': 0,
        'RELOAD_ON_SAVE': False,
    }))
    assert disabled_roi.config['ADU_ROI'] == []
    assert disabled_roi.config['SQM_ROI'] == []
    assert disabled_roi.config['IMAGE_CROP_ROI'] == []
    assert disabled_roi.reload_on_save is False


def test_parity_harness_accepts_equivalent_candidate_and_exceptions():
    harness = LegacyFullConfigParserHarness()

    harness.assert_parity(harness.execute_legacy)
    harness.assert_parity(
        harness.execute_legacy,
        payload=harness.build_payload({'TEXT_PROPERTIES__FONT_COLOR': 'invalid-color'}),
    )


def test_parity_harness_detects_candidate_drift():
    harness = LegacyFullConfigParserHarness()

    def divergent_candidate(config, payload):
        result = harness.execute_legacy(config, payload)
        result.config['CCD_EXPOSURE_TIMEOUT'] = 999
        return result

    try:
        harness.assert_parity(divergent_candidate)
    except AssertionError:
        pass
    else:
        raise AssertionError('Parity harness failed to detect candidate drift')


if __name__ == '__main__':
    test_parity_corpus_covers_current_legacy_parser_contract()
    test_camera_connection_parser_preserves_legacy_casting_and_required_fields()
    test_station_identity_parser_preserves_legacy_casting_and_required_fields()
    test_lens_metadata_parser_preserves_legacy_casting_and_required_fields()
    test_lens_geometry_parser_preserves_legacy_casting_and_required_fields()
    test_exposure_gain_parser_preserves_legacy_casting_and_rounding()
    test_acquisition_mode_parser_preserves_legacy_integer_casting()
    test_ajax_config_view_delegates_camera_connection_parsing()
    test_ajax_config_view_delegates_station_identity_parsing()
    test_ajax_config_view_delegates_lens_metadata_parsing()
    test_ajax_config_view_delegates_lens_geometry_parsing()
    test_ajax_config_view_delegates_exposure_gain_parsing_in_legacy_order()
    test_ajax_config_view_delegates_acquisition_mode_in_legacy_order()
    test_exposure_gain_parser_preserves_partial_mutation_order_on_errors()
    test_full_config_parser_matches_pre_migration_golden_fingerprints()
    test_golden_fingerprint_normalizes_legacy_unordered_youtube_tags()
    test_legacy_parser_corpus_executes_success_and_edge_paths()
    test_parity_harness_accepts_equivalent_candidate_and_exceptions()
    test_parity_harness_detects_candidate_drift()
    print('Full config parser parity checks passed')
