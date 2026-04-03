# GEMINI.md - Core Mandates

## Development Lifecycle Automation
The agent shall automatically perform the following actions for code changes:

1.  **Code Review:** Analyze changes for adherence to project conventions, quality standards, and best practices before committing.
2.  **Commit:** Stage all relevant changes and create a commit. Commit messages must be clear, concise, and follow the Conventional Commits specification (e.g., `feat:`, `fix:`, `chore:`).
3.  **Push:** Automatically push the committed changes to the `origin` remote.
4.  **GitHub Best Practices:** Ensure all changes pushed align with general GitHub repository best practices, including clear commit messages and maintaining a clean, manageable commit history.
