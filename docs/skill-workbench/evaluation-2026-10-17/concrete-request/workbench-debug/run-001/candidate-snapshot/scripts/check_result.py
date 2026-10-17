#!/usr/bin/env python3
"""Check shape, missing-input status and literal evidence; not action semantics."""
import datetime
import json
import sys
from pathlib import Path


def check(inp, out):
    errors = []
    if not isinstance(inp, dict) or set(inp) != {'transcript', 'reference_date'}:
        return ['input must contain exactly transcript and reference_date']
    transcript = inp['transcript']
    date = inp['reference_date']
    if transcript is not None and not isinstance(transcript, str):
        return ['transcript must be a string or null']
    if date is not None:
        try:
            if not isinstance(date, str) or datetime.date.fromisoformat(date).isoformat() != date:
                raise ValueError()
        except (ValueError, TypeError):
            errors.append('reference_date must be YYYY-MM-DD or null')
    if not isinstance(out, dict) or set(out) != {'status', 'actions'}:
        return errors + ['output must contain exactly status and actions']
    required_status = 'NEEDS_INPUT' if transcript is None or not transcript.strip() else 'READY'
    if out['status'] != required_status:
        errors.append('incorrect status for transcript')
    if not isinstance(out['actions'], list):
        return errors + ['actions must be an array']
    if required_status == 'NEEDS_INPUT' and out['actions']:
        errors.append('missing transcript requires empty actions')
    for i, action in enumerate(out['actions']):
        if not isinstance(action, dict) or set(action) != {'text', 'owner', 'deadline', 'evidence'}:
            errors.append(f'actions[{i}] has incorrect fields')
            continue
        for key in ('text', 'evidence'):
            if not isinstance(action[key], str) or not action[key].strip():
                errors.append(f'actions[{i}].{key} must be nonempty string')
        for key in ('owner', 'deadline'):
            if action[key] is not None and (not isinstance(action[key], str) or not action[key].strip()):
                errors.append(f'actions[{i}].{key} must be nonempty string or null')
        if isinstance(action['evidence'], str) and (not isinstance(transcript, str) or action['evidence'] not in transcript):
            errors.append(f'actions[{i}].evidence is not an exact transcript substring')
    return errors


def main():
    try:
        if len(sys.argv) != 3:
            raise ValueError('usage: check_result.py INPUT.json OUTPUT.json')
        inp, out = [json.loads(Path(p).read_text(encoding='utf-8')) for p in sys.argv[1:]]
        errors = check(inp, out)
    except (OSError, ValueError) as exc:
        errors = [str(exc)]
    print(json.dumps({'status': 'FAIL' if errors else 'PASS', 'errors': errors}, ensure_ascii=False))
    return bool(errors)


if __name__ == '__main__':
    sys.exit(main())
