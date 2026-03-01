# Technical Documentation Standards for AI Coding Assistants

## Inline Comments

Always write inline comments to explain complex logic, non-obvious decisions, or potential pitfalls. Never use comments to restate the obvious.

When you encounter a function or block of code that is not immediately clear, add a comment explaining its purpose, assumptions, and any side effects.

Do not leave commented-out code in the codebase. If code is no longer needed, remove it.

**Good Example:**
```python
def calculate_discount(price: float, discount_percentage: float) -> float:
    # Calculate the final price after applying the discount.
    # Assumes discount_percentage is between 0.0 and 1.0.
    if not (0.0 <= discount_percentage <= 1.0):
        raise ValueError("Discount percentage must be between 0.0 and 1.0")
    return price * (1 - discount_percentage)
```

**Bad Example:**
```python
def add(a, b):
    # This function adds two numbers.
    return a + b
```

## README Structure

Always include a `README.md` file at the root of every project. This file must provide a comprehensive overview of the project.

Your `README.md` must include the following sections, in order:
1.  **Project Title:** A clear and concise title for the project.
2.  **Description:** A brief explanation of what the project does and its purpose.
3.  **Features:** A list of key functionalities or features.
4.  **Installation:** Step-by-step instructions on how to set up and install the project.
5.  **Usage:** Examples of how to use the project, including code snippets if applicable.
6.  **Contributing:** Guidelines for contributing to the project.
7.  **License:** Information about the project's license.

When you update the project's functionality or dependencies, immediately update the `README.md` to reflect these changes.

Do not include redundant information in the `README.md` that is better suited for other documentation (e.g., detailed API specifications).

**Good Example (README.md snippet):**
```markdown
# My Awesome Project

## Description
This project provides a robust solution for managing user authentication and authorization in web applications.

## Installation
```bash
# Clone the repository
git clone https://github.com/your-org/my-awesome-project.git
cd my-awesome-project

# Install dependencies
pip install -r requirements.txt
```
```

## API Documentation

Always generate and maintain up-to-date API documentation for all public-facing APIs. You must use a standard format like OpenAPI (Swagger) for REST APIs or JSDoc/Sphinx for code-level documentation.

When you create or modify an API endpoint, immediately update its documentation to reflect the changes in parameters, return types, and error codes.

Your API documentation must include:
1.  **Endpoint Description:** A clear explanation of what the endpoint does.
2.  **HTTP Method:** The HTTP method used (GET, POST, PUT, DELETE, etc.).
3.  **Parameters:** A list of all request parameters, including their type, description, and whether they are required.
4.  **Responses:** Descriptions of possible responses, including status codes and example payloads.
5.  **Authentication/Authorization:** Details on how to authenticate and authorize requests.

Do not release an API without corresponding, accurate, and complete documentation.

**Good Example (OpenAPI snippet):**
```yaml
paths:
  /users/{userId}:
    get:
      summary: Get user by ID
      parameters:
        - in: path
          name: userId
          schema:
            type: integer
          required: true
          description: Numeric ID of the user to retrieve
      responses:
        '200':
          description: A user object
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
```

## Changelogs

Always maintain a `CHANGELOG.md` file at the root of the project. This file must document all significant changes made to the project, following the [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format.

When you complete a feature, fix a bug, or make a breaking change, add an entry to the `CHANGELOG.md` under the appropriate section (Added, Changed, Deprecated, Removed, Fixed, Security).

Each entry must include:
1.  The type of change (e.g., `Added`, `Fixed`).
2.  A concise description of the change.
3.  The relevant issue or pull request number, if applicable.

Do not include trivial changes or commit-level details in the changelog. Focus on user-facing or significant developer-facing changes.

**Good Example (CHANGELOG.md snippet):**
```markdown
# Changelog

## [1.0.0] - 2023-10-26

### Added
- Initial release of the user management API. (#123)
- Implemented JWT-based authentication.

### Fixed
- Corrected an issue where user passwords were not being hashed correctly. (#45)
```

## Architecture Decision Records (ADRs)

Always create an Architecture Decision Record (ADR) for every significant architectural decision made in the project. You must store ADRs in a dedicated `docs/adr/` directory.

When you make a decision that has a significant impact on the project's architecture, create a new ADR using a standard template. Each ADR must include:
1.  **Title:** A concise title describing the decision.
2.  **Status:** (Proposed, Accepted, Rejected, Superseded).
3.  **Context:** The forces and background leading to the decision.
4.  **Decision:** The chosen solution.
5.  **Consequences:** The positive and negative impacts of the decision.

Do not make significant architectural changes without documenting them in an ADR. This ensures that the rationale behind decisions is preserved.

**Good Example (ADR snippet):**
```markdown
# 0001-use-postgresql-for-data-storage.md

## Title
Use PostgreSQL for Data Storage

## Status
Accepted

## Context
Our application requires a robust and scalable relational database. We need ACID compliance and strong support for complex queries.

## Decision
We will use PostgreSQL as our primary data storage solution.

## Consequences
Positive:
- Strong data integrity.
- Excellent support for complex queries and transactions.
- Large community and extensive tooling.

Negative:
- Higher operational overhead compared to NoSQL solutions.
- Requires careful schema design.
```
