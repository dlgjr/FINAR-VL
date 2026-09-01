import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class DownloadMissingDatasetsTests(unittest.TestCase):
    def test_download_specs_cover_requested_public_sources_and_exclude_finrag(self):
        spec = importlib.util.find_spec("scripts.data.download_missing_datasets")
        self.assertIsNotNone(spec, "下载模块尚未创建")

        from scripts.data.download_missing_datasets import DOWNLOAD_SPECS

        names = {item.name for item in DOWNLOAD_SPECS}
        self.assertTrue(
            {
                "BizFinBench.v2",
                "Finch",
                "FiNER-139",
                "FinMME",
                "MultiHiertt",
                "TAT-DQA",
                "PIXIU-fpb",
                "PIXIU-fiqasa",
                "PIXIU-headlines",
                "PIXIU-ner",
                "PIXIU-convfinqa",
                "PIXIU-sm-bigdata",
                "PIXIU-sm-acl",
                "PIXIU-sm-cikm",
            }.issubset(names)
        )
        self.assertFalse(any("FinRAGBench-V" in item.repo_id for item in DOWNLOAD_SPECS))

        multihiertt = next(item for item in DOWNLOAD_SPECS if item.name == "MultiHiertt")
        self.assertEqual(multihiertt.allow_patterns, ("multihiertt_data/**",))
        fpb = next(item for item in DOWNLOAD_SPECS if item.name == "PIXIU-fpb")
        self.assertEqual(fpb.repo_id, "ChanceFocus/flare-fpb")
        fiqasa = next(item for item in DOWNLOAD_SPECS if item.name == "PIXIU-fiqasa")
        self.assertEqual(fiqasa.repo_id, "ChanceFocus/flare-fiqasa")

        from scripts.data.download_missing_datasets import DUPLICATE_EXISTING_SOURCES

        self.assertEqual(DUPLICATE_EXISTING_SOURCES["PIXIU-finqa"], "finqa")

    def test_snapshot_download_retries_transient_connection_failure(self):
        import scripts.data.download_missing_datasets as download_module

        self.assertTrue(hasattr(download_module, "_snapshot_with_retry"))
        spec = download_module.DownloadSpec("sample", "org/sample", "sample")
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(
                download_module,
                "snapshot_download",
                side_effect=[ConnectionError("temporary"), str(Path(tmp))],
            ) as mocked:
                download_module._snapshot_with_retry(spec, Path(tmp), attempts=2, delay_seconds=0)
        self.assertEqual(mocked.call_count, 2)


if __name__ == "__main__":
    unittest.main()
