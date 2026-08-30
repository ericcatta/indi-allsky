#!/usr/bin/env python3

import ast
import copy
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from indi_allsky.modern_admin_settings_runtime import ModernAdminFullConfigPayloadPreparationService


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

    def __init__(self, source_path=VIEWS_PATH):
        self.source_path = Path(source_path)
        self.parser_statements = self.extract_parser_statements()
        self.code = compile(
            ast.fix_missing_locations(ast.Module(body=self.parser_statements, type_ignores=[])),
            str(self.source_path),
            'exec',
        )
        self.direct_payload_keys, self.optional_payload_keys = self.extract_payload_keys()


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
            for key in set(self.direct_payload_keys) | set(self.optional_payload_keys)
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
            'self': SimpleNamespace(indi_allsky_config=config),
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

    assert len(harness.direct_payload_keys) == 719
    assert set(harness.JSON_FIELDS).issubset(harness.direct_payload_keys)
    assert set(harness.COLOR_FIELDS).issubset(harness.direct_payload_keys)
    assert 'YOUTUBE__TAGS_STR' in harness.direct_payload_keys
    assert 'RELOAD_ON_SAVE' in harness.direct_payload_keys
    assert 'CONFIG_NOTE' in harness.direct_payload_keys


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
    test_legacy_parser_corpus_executes_success_and_edge_paths()
    test_parity_harness_accepts_equivalent_candidate_and_exceptions()
    test_parity_harness_detects_candidate_drift()
    print('Full config parser parity checks passed')
