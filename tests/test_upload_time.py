"""Run with the backend Python environment; no existing diary data is accessed."""
import importlib.util
import gc
from sqlalchemy.orm import close_all_sessions
import io
import os
from pathlib import Path
import tempfile
import unittest
from datetime import datetime, timezone
from fastapi import UploadFile
from PIL import Image
from starlette.datastructures import Headers


class UploadTimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        cls.old_dir = os.environ.get('PLOG_DATA_DIR')
        os.environ['PLOG_DATA_DIR'] = cls.temp.name
        spec = importlib.util.spec_from_file_location('diary_time_test', Path(__file__).parents[1] / 'backend' / 'main.py')
        cls.api = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.api)

    @classmethod
    def tearDownClass(cls):
        close_all_sessions()
        gc.collect()
        cls.api.engine.dispose()
        if cls.old_dir is None:
            os.environ.pop('PLOG_DATA_DIR', None)
        else:
            os.environ['PLOG_DATA_DIR'] = cls.old_dir
        cls.temp.cleanup()

    def test_midnight_and_legacy_utc(self):
        self.assertEqual(str(self.api.diary_day(datetime(2026, 11, 20, 16, 1, tzinfo=timezone.utc))), '2026-11-21')
        self.assertEqual(str(self.api.diary_day(datetime(2026, 11, 20, 15, 59, tzinfo=timezone.utc))), '2026-11-20')
        self.assertEqual(self.api.utc_timestamp(datetime(2026, 11, 21, 4, 57)), '2026-11-21T04:57:00Z')

    def test_upload_and_list_return_the_same_timezone(self):
        group = self.api.create_group(self.api.GroupCreate(name='隔离测试'))
        upload = UploadFile(file=io.BytesIO(b'test-image'), filename='test.jpg', headers=Headers({'content-type': 'image/jpeg'}))
        result = self.api.upload_moment(group['id'], group['owner_member_id'], '时区回归', upload, None)
        self.assertTrue(result['created_at'].endswith('Z'))
        self.assertEqual(result['day'], str(self.api.diary_day()))
        listed = self.api.list_moments(group['id'], None)
        self.assertEqual(listed[0]['created_at'], result['created_at'])
        self.assertEqual(listed[0]['caption'], '时区回归')

    def test_heic_upload_is_served_as_a_resized_jpeg(self):
        group = self.api.create_group(self.api.GroupCreate(name='HEIC 测试'))
        with io.BytesIO() as payload, Image.new('RGB', (1800, 100), '#b47985') as sample:
            sample.save(payload, format='HEIF')
            payload.seek(0)
            upload = UploadFile(
                file=payload,
                filename='camera.HEIC',
                headers=Headers({'content-type': 'image/heic'}),
            )
            result = self.api.upload_moment(group['id'], group['owner_member_id'], '', upload, None)

        filename = Path(result['media_url']).name
        self.assertEqual(Path(filename).suffix, '.jpg')
        with Image.open(self.api.UPLOADS / filename) as saved:
            self.assertEqual(saved.format, 'JPEG')
            self.assertEqual(saved.width, 1600)


if __name__ == '__main__':
    unittest.main()
