"""Persist observable per-output results without changing generation algorithms."""


def finish_keogram_task(task, *, camera_id, night, keogram, startrail, video,
                        frames, min_frames, video_enabled, startrail_frames=None):
    outputs = []
    for kind, label, pair in (('keogram', 'Keogram', keogram),
                              ('startrail', 'Startrail', startrail),
                              ('startrail-video', 'Startrail video', video)):
        entry, path = pair
        row = {'kind': kind, 'label': label, 'camera_id': camera_id,
               'record_id': getattr(entry, 'id', None)}
        if kind != 'keogram' and not night:
            row.update(status='not_requested', reason='Night-only output')
        elif kind == 'startrail' and startrail_frames == 0:
            row.update(status='skipped', reason='No eligible frames',
                       eligible_frames=0, minimum_frames=1)
            if entry is not None:
                entry.success = False
        elif kind == 'startrail-video' and not video_enabled:
            row.update(status='not_requested', reason='Disabled in configuration')
        elif kind == 'startrail-video' and frames < min_frames:
            row.update(status='skipped', reason='Insufficient eligible frames',
                       eligible_frames=frames, minimum_frames=min_frames)
        else:
            try:
                exists = path.is_file() and path.stat().st_size > 0
            except OSError:
                exists = False
            successful = bool(entry is not None and entry.success and exists)
            row.update(status='generated' if successful else 'failed',
                       reason='Saved file present' if successful else 'Generation failed or output file missing/empty')
            if entry is not None and not exists:
                entry.success = False
        outputs.append(row)

    generated = sum(row['status'] == 'generated' for row in outputs)
    failures = any(row['status'] == 'failed' for row in outputs)
    skipped = any(row['status'] == 'skipped' for row in outputs)
    status = 'failed' if failures or not generated else 'partial' if skipped else 'complete'
    outcome = {'status': status, 'camera_id': camera_id, 'outputs': outputs}
    task.data = dict(task.data or {}, generation_outcome=outcome)
    parts = []
    for row in outputs:
        if row['status'] == 'not_requested':
            continue
        detail = row['status']
        if row['status'] == 'skipped':
            detail += ' ({0}/{1} eligible frames)'.format(row['eligible_frames'], row['minimum_frames'])
        parts.append(row['label'] + ': ' + detail)
    message = (status.title() + ' generation — ' + '; '.join(parts))[:255]
    # Skipped optional video preserves successful task completion but the result
    # explicitly reports partial output. Actual output failures fail the task.
    if status == 'failed':
        task.setFailed(message)
    else:
        task.setSuccess(message)
    return outcome
