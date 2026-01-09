#!/usr/bin/env python3
"""
Test script to verify the progress bar and offset calculation
in delete_old_files_yadisk function.

This script creates mock data to test the logic without requiring
actual YaDisk credentials.
"""

import os
import sys
import datetime
from unittest.mock import Mock, MagicMock, patch
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def simulate_delete_old_files_yadisk(dir_path, offset=0, limit=100, max_hours=12, all=False):
    """
    Simulated version of delete_old_files_yadisk to test progress bar and offset calculation.
    """
    now = datetime.datetime.now(datetime.timezone.utc)

    # Simulate file list - create mix of old and new files
    # Let's simulate 250 total files in the directory
    # - First 50 files: old (to be deleted)
    # - Next 150 files: new (to be skipped)
    # - Last 50 files: old (to be deleted)

    total_files_in_dir = 250
    files_list = []

    # Determine which files to return based on offset and limit
    start_idx = offset
    end_idx = min(offset + limit, total_files_in_dir)

    print(f'\n=== Simulating batch: offset={offset}, limit={limit} ===')

    if start_idx >= total_files_in_dir:
        print('No more files to process')
        return

    for i in range(start_idx, end_idx):
        mock_file = Mock()
        mock_file.path = f'/path/to/file_{i}.txt'

        # Determine file age based on position
        if i < 50 or i >= 200:
            # Old file (created 24 hours ago)
            mock_file.created = now - datetime.timedelta(hours=24)
        else:
            # New file (created 1 hour ago)
            mock_file.created = now - datetime.timedelta(hours=1)

        files_list.append(mock_file)

    deleted_count = 0
    skipped_count = 0
    print(f'total: {len(files_list)}')

    # Create progress bar for this batch
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
    ) as progress:
        task = progress.add_task(f"[cyan]Processing files (offset={offset})...", total=len(files_list))

        for item in files_list:
            time_diff = now - item.created
            if time_diff.total_seconds() / 60 / 60 > max_hours:
                # Simulate deletion
                deleted_count += 1
            else:
                # File is too new, skip it
                skipped_count += 1
            progress.update(task, advance=1)

    print(f'Deleted {deleted_count} files, skipped {skipped_count} files in {dir_path}.')
    print(f'Next offset should be: {offset + skipped_count}')

    # Recursively process next batch if needed
    # Only continue if there are files to skip AND we got a full batch (otherwise we've reached the end)
    if all and skipped_count > 0 and len(files_list) == limit:
        new_offset = offset + skipped_count
        simulate_delete_old_files_yadisk(dir_path, offset=new_offset, limit=limit, max_hours=max_hours, all=True)
    else:
        print('\n[TERMINATION CONDITION MET]')
        if skipped_count == 0:
            print('  Reason: No files to skip (all files were deleted or no more files)')
        elif len(files_list) < limit:
            print(f'  Reason: Partial batch ({len(files_list)} < {limit}) - reached end of directory')


if __name__ == '__main__':
    print('Testing delete_old_files_yadisk with progress bar and offset calculation')
    print('=' * 80)
    print('\nScenario:')
    print('- Total files: 250')
    print('- Files 0-49: old (will be deleted)')
    print('- Files 50-199: new (will be skipped)')
    print('- Files 200-249: old (will be deleted)')
    print('- Batch size (limit): 100')
    print('- max_hours: 12')
    print('\nExpected behavior:')
    print('- Batch 1 (offset=0): Delete 50, Skip 50 → Next offset = 50')
    print('- Batch 2 (offset=50): Delete 0, Skip 100 → Next offset = 150')
    print('- Batch 3 (offset=150): Delete 0, Skip 50 → Next offset = 200')
    print('- Batch 4 (offset=200): Delete 50, Skip 0 → Done')
    print('=' * 80)

    simulate_delete_old_files_yadisk('test/path', offset=0, limit=100, max_hours=12, all=True)

    print('\n' + '=' * 80)
    print('Test completed!')
