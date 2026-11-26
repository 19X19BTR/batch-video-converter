#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
选片语法的单元测试（纯标准库）：

    python -m unittest discover -s tests -t . -v

不依赖 ffmpeg，只测 parse_choice 这个纯函数。
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import batch_convert as bc  # noqa: E402


class TestParseChoiceBasic(unittest.TestCase):
    def test_空输入返回空列表(self):
        self.assertEqual(bc.parse_choice('', 10), [])
        self.assertEqual(bc.parse_choice('   ', 10), [])

    def test_单号(self):
        self.assertEqual(bc.parse_choice('3', 10), [2])

    def test_逗号分隔(self):
        self.assertEqual(bc.parse_choice('1,3,5', 10), [0, 2, 4])

    def test_普通范围(self):
        self.assertEqual(bc.parse_choice('3-5', 10), [2, 3, 4])

    def test_前缀区间(self):
        self.assertEqual(bc.parse_choice('-5', 10), [0, 1, 2, 3, 4])

    def test_后缀区间(self):
        self.assertEqual(bc.parse_choice('8-', 10), [7, 8, 9])

    def test_混合语法(self):
        self.assertEqual(bc.parse_choice('1,3-5,8-', 10), [0, 2, 3, 4, 7, 8, 9])

    def test_乱序输入会排序去重(self):
        self.assertEqual(bc.parse_choice('5,3,3,1', 10), [0, 2, 4])

    def test_带空格也能解析(self):
        self.assertEqual(bc.parse_choice(' 1 , 3 - 5 ', 10), [0, 2, 3, 4])

    def test_末尾逗号被忽略(self):
        self.assertEqual(bc.parse_choice('1,2,', 10), [0, 1])


class TestParseChoiceErrors(unittest.TestCase):
    def test_单号越界(self):
        with self.assertRaises(ValueError):
            bc.parse_choice('11', 10)
        with self.assertRaises(ValueError):
            bc.parse_choice('0', 10)

    def test_范围越界(self):
        with self.assertRaises(ValueError):
            bc.parse_choice('5-11', 10)

    def test_范围反了(self):
        with self.assertRaises(ValueError):
            bc.parse_choice('7-3', 10)

    def test_前缀区间越界(self):
        with self.assertRaises(ValueError):
            bc.parse_choice('-11', 10)

    def test_后缀区间越界(self):
        with self.assertRaises(ValueError):
            bc.parse_choice('11-', 10)

    def test_非数字报错(self):
        with self.assertRaises(ValueError):
            bc.parse_choice('abc', 10)


class TestParseChoiceEdge(unittest.TestCase):
    def test_只有一个文件时全选(self):
        self.assertEqual(bc.parse_choice('1', 1), [0])
        self.assertEqual(bc.parse_choice('-1', 1), [0])
        self.assertEqual(bc.parse_choice('1-', 1), [0])

    def test_首尾相接的范围(self):
        self.assertEqual(bc.parse_choice('1-1', 10), [0])
        self.assertEqual(bc.parse_choice('10-10', 10), [9])


if __name__ == '__main__':
    unittest.main()
