import sqlite3
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import Mock, patch

from lib.core.exceptions import FileExistsException, InvalidRawRequest
from lib.parse.rawrequest import parse_raw
from lib.report.csv_report import CSVReport
from lib.report.html_report import HTMLReport
from lib.report.sqlite_report import SQLiteReport


class EOFGuard(StringIO):
    def __init__(self, value):
        super().__init__(value)
        self.eof_reads = 0

    def readline(self, *args, **kwargs):
        line = super().readline(*args, **kwargs)
        if not line:
            self.eof_reads += 1
            if self.eof_reads > 1:
                raise AssertionError("HTML report parser read past EOF")
        return line


class TestReportExceptionHandling(TestCase):
    def test_csv_report_rejects_wrong_header(self):
        with TemporaryDirectory() as directory:
            report = Path(directory, "report.csv")
            report.write_text("Not,Dirsearch\n")

            with self.assertRaisesRegex(ValueError, "CSV header mismatch.*expected.*got"):
                CSVReport().parse(str(report))

    def test_file_report_validation_chains_parse_error(self):
        with TemporaryDirectory() as directory:
            report = Path(directory, "report.csv")
            report.write_text("Not,Dirsearch\n")

            with self.assertRaises(FileExistsException) as context:
                CSVReport().initiate(str(report))

        self.assertIsInstance(context.exception.__cause__, ValueError)

    def test_html_report_validation_stops_at_end_of_malformed_file(self):
        with TemporaryDirectory() as directory:
            report = Path(directory, "report.html")
            report.write_text("<html>not a dirsearch report</html>\n")
            guarded_file = EOFGuard(report.read_text())

            with patch("lib.report.html_report.open", return_value=guarded_file):
                with self.assertRaises(FileExistsException) as context:
                    HTMLReport().initiate(str(report))

        self.assertIsInstance(context.exception.__cause__, ValueError)
        self.assertEqual(guarded_file.eof_reads, 1)

    def test_html_report_parser_preserves_generated_resources(self):
        resources = [{"status": 200, "url": "https://example.com/admin"}]
        html_report = HTMLReport()

        with TemporaryDirectory() as directory:
            report = Path(directory, "report.html")
            report.write_text(html_report.generate(resources))

            self.assertEqual(html_report.parse(str(report)), resources)

    def test_sqlite_report_rejects_non_sqlite_file(self):
        with TemporaryDirectory() as directory:
            database = Path(directory, "report.sqlite")
            database.write_text("not sqlite")

            with self.assertRaisesRegex(ValueError, "valid SQLite database") as context:
                SQLiteReport().connect(str(database))

        self.assertIsInstance(context.exception.__cause__, sqlite3.DatabaseError)

    def test_sqlite_report_closes_connection_after_validation_failure(self):
        connection = Mock()
        connection.cursor.return_value.execute.side_effect = sqlite3.DatabaseError

        with TemporaryDirectory() as directory:
            database = str(Path(directory, "report.sqlite"))
            with patch(
                "lib.report.sqlite_report.sqlite3.connect", return_value=connection
            ):
                with self.assertRaisesRegex(ValueError, "valid SQLite database"):
                    SQLiteReport().connect(database)

        connection.close.assert_called_once_with()

    def test_raw_request_malformed_input_preserves_invalid_request_type(self):
        with TemporaryDirectory() as directory:
            request = Path(directory, "request.txt")
            request.write_text("\n")

            with self.assertRaises(InvalidRawRequest) as context:
                parse_raw(str(request))

        self.assertIsInstance(context.exception.__cause__, IndexError)
