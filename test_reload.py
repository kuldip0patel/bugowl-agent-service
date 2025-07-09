#!/usr/bin/env python3
"""
Test script to verify auto-reload functionality.
Create this file in the bugowl directory and modify it to test if Daphne restarts.
"""

import datetime

# Modify this comment to test auto-reload: Test 1
print(f'Auto-reload test script loaded at {datetime.datetime.now()}')


def test_function():
	"""Test function - modify this to trigger reload"""
	return 'Auto-reload is working!'


if __name__ == '__main__':
	print(test_function())
