#!/usr/bin/env python3
#
# -*- coding: utf-8 -*-
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#  Author: Mauro Soria

from pathlib import Path
import unittest


PROJECT_ROOT = Path(__file__).resolve().parent
TEST_ROOT = PROJECT_ROOT / "tests"


def discover_tests():
    return unittest.TestLoader().discover(
        str(TEST_ROOT), pattern="test_*.py", top_level_dir=str(PROJECT_ROOT)
    )


def main():
    result = unittest.TextTestRunner().run(discover_tests())
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
