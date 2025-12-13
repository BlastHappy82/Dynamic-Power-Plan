# Contributing to Dynamic Power Plan

Thank you for your interest in contributing to Dynamic Power Plan! This document provides guidelines and instructions for contributing.

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Windows OS (for full functionality testing)
- Git

### Setting Up Development Environment

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/DynamicPowerPlan.git
   cd DynamicPowerPlan
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   python main.py
   ```

## How to Contribute

### Reporting Bugs

Before creating a bug report, please check existing issues to avoid duplicates.

When filing a bug report, include:
- Your operating system and version
- Python version
- Steps to reproduce the issue
- Expected behavior vs actual behavior
- Any error messages or logs

### Suggesting Features

Feature requests are welcome! Please:
- Check if the feature has already been suggested
- Provide a clear description of the feature
- Explain the use case and why it would be valuable

### Submitting Changes

1. Create a new branch for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes following the code style guidelines below

3. Test your changes thoroughly

4. Commit your changes with clear, descriptive messages:
   ```bash
   git commit -m "Add feature: description of what you added"
   ```

5. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

6. Create a Pull Request on GitHub

## Code Style Guidelines

### Python Code

- Follow PEP 8 style guidelines
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep functions focused and single-purpose
- Use type hints where appropriate

### File Organization

- `main.py` - Application entry point
- `src/config.py` - Configuration management
- `src/monitor.py` - System monitoring (CPU/GPU)
- `src/power_manager.py` - Power plan and fan control
- `src/tray_app.py` - System tray interface

### Commit Messages

- Use present tense ("Add feature" not "Added feature")
- Use imperative mood ("Move cursor to..." not "Moves cursor to...")
- Keep the first line under 50 characters
- Reference issues when applicable

## Testing

Before submitting a pull request:

1. Test on Windows with actual power plans configured
2. Verify the system tray icon appears and menu works
3. Check that CPU/GPU monitoring functions correctly
4. Test manual mode switching
5. Verify configuration loading/saving works

## Pull Request Process

1. Ensure your code follows the style guidelines
2. Update documentation if needed
3. Add yourself to CONTRIBUTORS.md if you'd like
4. Your PR will be reviewed by maintainers
5. Address any feedback or requested changes
6. Once approved, your PR will be merged

## Questions?

If you have questions about contributing, feel free to open an issue with the "question" label.

Thank you for contributing!
