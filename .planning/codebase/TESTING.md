# Testing Patterns

**Analysis Date:** 2026-05-11

## Test Framework

**Runner:** pytest >= 8.0
**Config:** `pyproject.toml` `[tool.pytest.ini_options]`

**Plugins:**
- `pytest-mock >= 3.6.0` — `mocker` fixture and `@patch` support
- `pytest-cov >= 5.0` — coverage reporting

**Assertion Library:** pytest built-in assertions (no extra library)

**Run Commands:**
```bash
uv run pytest                                              # Run all tests (verbose, short traceback)
uv run pytest tests/test_eq_report.py                     # Single file
uv run pytest -m "not slow"                               # Skip slow tests
uv run pytest -m "not integration"                        # Skip integration tests (require Odoo)
uv run pytest --cov --cov-report=term-missing             # With coverage
uv run pytest --cov --cov-report=term-missing --cov-report=xml  # CI mode
```

**Default pytest flags** (`addopts`): `-v --tb=short`

## Test File Organization

**Location:** `tests/` directory (separate from source, not co-located)

**Naming:**
- Files: `test_<source_module>.py`
- Classes: `Test<ClassName>` grouping related tests
- Functions: `test_<behavior_description>`

**Structure:**
```
tests/
├── __init__.py
├── conftest.py                       # All shared fixtures
├── fixtures/                         # Static YAML fixture files
│   ├── sample_connection.yaml
│   ├── sample_report.yaml
│   └── sample_report_multicompany.yaml
├── yaml_test/                        # Minimal YAML for utility tests
│   ├── test.yaml
│   └── test2.yaml
├── test_cli.py                       # CLI entry point tests
├── test_eq_odoo_connection.py        # EqOdooConnection tests
├── test_eq_report.py                 # EqReport tests
├── test_eq_utils.py                  # eq_utils tests
├── test_exceptions.py                # Exception class tests
├── test_helper_utils.py              # odoo_report_helper/utils tests (circular import issue)
├── test_lang_utils.py                # lang_utils tests
├── test_logging.py                   # logging_config tests
├── test_odoo_connection.py           # OdooConnection base class tests
├── test_progress.py                  # progress bar tests
└── test_report.py                    # Report base class tests
```

**Total:** 12 test files, ~369 tests.

## Test Structure

**Suite organization using classes:**
```python
class TestOdooConnectionConstructor:
    """Verify constructor calls prepare_connection and handles errors."""

    @patch("odoo_report_helper.odoo_connection.utils.prepare_connection")
    def test_constructor_calls_prepare_connection(self, mock_prepare):
        ...

    @patch("odoo_report_helper.odoo_connection.utils.prepare_connection")
    def test_constructor_raises_odoo_connection_error_on_url_error(self, mock_prepare):
        ...


class TestOdooConnectionLogin:
    """Verify login behavior and error handling."""
    ...
```

**Section headers** — test files use comment separators for readability:
```python
# ---------------------------------------------------------------------------
# Constructor tests
# ---------------------------------------------------------------------------
```

**Helper factory functions** — used instead of fixtures when construction requires overrides:
```python
def _make_report(**overrides):
    """Create an EqReport with sensible defaults, allowing per-test overrides."""
    defaults = {
        "entry_name": {"de_DE": "Verkaufsauftrag", "en_US": "Sales_Order"},
        "report_name": "eq_fr_core_sale_order",
        ...
    }
    defaults.update(overrides)
    return EqReport(**defaults)
```

## Mocking

**Primary pattern:** `@patch` decorator targeting the import path where the symbol is **used** (not where it is defined):

```python
# Correct: patch where utils is imported in odoo_connection module
@patch("odoo_report_helper.odoo_connection.utils.prepare_connection")
def test_something(self, mock_prepare):
    mock_prepare.return_value = MagicMock()
    ...

# Correct: patch ODOO class where it is used in utils module
with patch("odoo_report_helper.utils.ODOO") as mock_odoo_cls:
    ...
```

**Core fixture — `mock_odoorpc`** (in `conftest.py`):
```python
@pytest.fixture
def mock_odoorpc():
    """Patch odoo_report_helper.utils.ODOO to prevent real network connections."""
    with patch("odoo_report_helper.utils.ODOO") as mock_odoo_cls:
        mock_instance = MagicMock()
        mock_instance.version = "18.0"
        mock_instance.env = MagicMock()
        mock_instance.env.context = {}
        mock_instance.config = {}
        mock_odoo_cls.return_value = mock_instance
        yield mock_odoo_cls
```

**Extended fixture — `mock_odoo_env`** (builds on `mock_odoorpc`):
```python
@pytest.fixture
def mock_odoo_env(mock_odoorpc):
    """Mock Odoo environment with common models."""
    # Provides: ir.model, ir.model.fields, ir.actions.report,
    #           ir.module.module, res.lang
    # Usage: mock_odoo_env["ir.actions.report"].create.return_value = 1
```

**What to mock:**
- `odoo_report_helper.utils.ODOO` — always mock to avoid network connections
- `odoo_report_helper.odoo_connection.utils.prepare_connection` — for constructor/login tests
- External CLI prompts and file paths in integration-style tests

**What NOT to mock:**
- Pure logic (lang_utils, exceptions, report field calculations)
- YAML parsing with real fixture files (use `tmp_yaml_dir` or `yaml_test/`)

## Fixtures and Factories

**Report data fixtures** (in `conftest.py`) return plain dicts:

```python
@pytest.fixture
def sample_report_yaml_data():
    """Complete report YAML data (modern locale codes de_DE/en_US)."""
    return {
        "name": {"de_DE": "Verkaufsauftrag", "en_US": "Sales_Order"},
        "report_name": "eq_fr_core_sale_order",
        "eq_export_type": "pdf",
        ...
    }

@pytest.fixture
def sample_report_yaml_data_legacy():
    """Same data with legacy keys ger/eng for backward-compat testing."""
    return {
        "name": {"ger": "Verkaufsauftrag", "eng": "Sales_Order"},
        ...
    }
```

**Filesystem fixtures:**
```python
@pytest.fixture
def tmp_yaml_dir(tmp_path):
    """Temporary directory with a sample YAML file — use for parse_yaml_folder tests."""

@pytest.fixture
def tmp_env_file(tmp_path):
    """Temporary .env file — use for env-var loading tests."""

@pytest.fixture
def fixtures_dir():
    """Path to tests/fixtures/ for static YAML files."""
    return Path(__file__).parent / "fixtures"

@pytest.fixture
def yaml_test_dir():
    """Path to tests/yaml_test/ for existing YAML utility tests."""
    return Path(__file__).parent / "yaml_test"
```

**Static fixture files** (`tests/fixtures/`):
- `sample_connection.yaml` — server connection config
- `sample_report.yaml` — standard report config
- `sample_report_multicompany.yaml` — multi-company report config

## Coverage

**Requirements:** `fail_under = 60` (minimum enforced by `pytest-cov`)

**Sources covered:** `odoo_fast_report_mapper`, `odoo_report_helper`

**Excluded from coverage:**
- `tests/` directory
- `__pycache__/`
- `build/`
- Lines matching `pragma: no cover`, `if __name__ == "__main__":`, `if TYPE_CHECKING:`

**View Coverage:**
```bash
uv run pytest --cov --cov-report=term-missing   # terminal with missing lines
uv run pytest --cov --cov-report=html           # HTML report in htmlcov/
```

## Test Types

**Unit Tests:**
- Pure logic without I/O: `test_lang_utils.py`, `test_exceptions.py`, `test_eq_report.py`, `test_report.py`
- Mocked network: `test_odoo_connection.py`, `test_eq_odoo_connection.py`
- Mocked filesystem: CLI tests using `tmp_path`

**Integration Tests:**
- Marked `@pytest.mark.integration` — require a real Odoo connection
- Excluded from default CI run: `-m "not integration"`

**Slow Tests:**
- Marked `@pytest.mark.slow` — exclude with `-m "not slow"`

## Known Issues

**Circular import in `test_helper_utils.py`:**
- `test_helper_utils.py` cannot be collected when running tests in isolation due to a circular import chain involving `odoo_report_helper` internals
- Tests pass when run as part of the full suite (`pytest tests/`)
- Do not restructure imports to "fix" this without understanding the full import graph

## Common Patterns

**Async Testing:** Not used — all code is synchronous.

**Error Testing:**
```python
with pytest.raises(OdooConnectionError, match="Please check your parameters"):
    OdooConnection(url="https://invalid.example.com", ...)

with pytest.raises(ValueError, match="URL scheme must be http or https"):
    prepare_connection("ftp://bad.example.com", 443)
```

**Verifying mock calls:**
```python
mock_prepare.assert_called_once_with("https://odoo.example.com", 443)
mock_connection.login.assert_called_once_with("test_db", "admin", "secret")
```

**Verifying security behaviors:**
```python
# Password cleared after login
assert conn.password is None

# Password cleared on connection failure
with pytest.raises(OdooConnectionError):
    OdooConnection(url="https://invalid...", ...)
assert conn_attempt.password is None  # via captured exception
```

## CI Configuration

**File:** `.github/workflows/test.yml`

**Triggers:** push and PR to `main` and `develop` branches.

**Matrix:** Python 3.12 and 3.13 (both run in parallel, `fail-fast: false`)

**Steps in order:**
1. Checkout
2. Install `uv` (with caching via `astral-sh/setup-uv@v6`)
3. `uv venv` + `uv pip install -e ".[dev]"`
4. `uv run ruff check .` — lint (blocks on failure)
5. `uv run ruff format --check .` — format check (blocks on failure)
6. `uv run mypy odoo_fast_report_mapper/ odoo_report_helper/` — `continue-on-error: true` (reported but non-blocking)
7. `uv run pytest --cov --cov-report=term-missing --cov-report=xml`
8. Upload `coverage.xml` artifact (Python 3.12 only, retained 7 days)

---

*Testing analysis: 2026-05-11*
