## Unit Tests

Always write unit tests for all pure functions, components, and small, isolated modules. Ensure unit tests cover all logical branches and error conditions within the tested unit.

**Good:**
```python
def add(a, b):
    return a + b

def test_add():
    assert add(1, 2) == 3
    assert add(-1, 1) == 0
    assert add(0, 0) == 0
```

**Bad:**
```python
def add_and_save(a, b):
    result = a + b
    # Imagine this saves to a database
    # save_to_db(result)
    return result

def test_add_and_save():
    # This test is not a unit test because it involves external dependencies
    assert add_and_save(1, 2) == 3
```

When writing unit tests, isolate the unit under test from its dependencies using mocks or stubs. Do not allow unit tests to interact with databases, file systems, or external APIs.

## Integration Tests

Always write integration tests to verify the interaction between two or more integrated components or services. Focus on the interfaces and data flow between these components.

When testing API endpoints, ensure integration tests cover successful requests, various input validations, and error responses.

**Good:**
```python
# Assuming a service `UserService` and a repository `UserRepository`
def test_user_service_creates_user(user_service, user_repository):
    user_data = {"name": "Test User", "email": "test@example.com"}
    created_user = user_service.create_user(user_data)
    assert created_user.name == "Test User"
    assert user_repository.get_user_by_email("test@example.com") is not None
```

**Bad:**
```python
def test_full_system_flow():
    # This is too broad for an integration test; it's closer to an E2E test
    # It involves too many components and external systems
    pass
```

## E2E Tests

Always write end-to-end (E2E) tests to simulate real user scenarios and verify the entire system from the user interface to the backend services and database. Use E2E tests sparingly due to their cost and flakiness, focusing on critical user journeys.

When writing E2E tests, use a dedicated testing environment that closely mirrors production. Do not run E2E tests against development or production environments unless explicitly configured for specific monitoring purposes.

## Test Naming

Always name test files and functions clearly and descriptively. Use the `test_` prefix for all test functions and files to ensure discoverability by test runners.

For unit tests, use the pattern `test_<unit_name>_<scenario_description>`.
For integration tests, use `test_integration_<component_a>_and_<component_b>_<scenario_description>`.
For E2E tests, use `test_e2e_<user_journey_description>`.

**Good:**
```python
# File: test_calculator.py
def test_add_two_positive_numbers():
    pass

# File: test_integration_user_service_and_repository_creates_user.py
def test_integration_user_service_creates_user_successfully():
    pass

# File: test_e2e_user_registration_and_login.py
def test_e2e_new_user_can_register_and_login():
    pass
```

**Bad:**
```python
def test1(): # Unclear purpose
    pass

def my_test_function(): # Missing 
