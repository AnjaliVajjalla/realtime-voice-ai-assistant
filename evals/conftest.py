"""Pytest automatically loads this for every test under evals/.

Unlike tests/ (mocked, no API calls), evals/ makes real API calls, so
.env needs to be loaded before any eval runs.
"""
from dotenv import load_dotenv

load_dotenv()
