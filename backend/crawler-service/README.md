# 🐍 Python Hello World Project

A simple Python "Hello World" application to get you started with Python development.

## 📋 Project Structure

```
crawler-service/
├── main.py           # Main application entry point
├── requirements.txt  # Python dependencies
├── README.md        # This documentation
├── venv/           # Virtual environment (created after setup)
└── app/            # Future application modules
    └── spiders/    # Future spider modules
```

## 🚀 Quick Start

### 1. Activate Virtual Environment

If you have an existing virtual environment:

```bash
# On Windows
cd backend/crawler-service
venv\Scripts\activate

# On macOS/Linux
cd backend/crawler-service
source venv/bin/activate
```

### 2. Install Dependencies (Optional)

```bash
pip install -r requirements.txt
```

*Note: This basic project doesn't require external dependencies.*

### 3. Run the Application

```bash
python main.py
```

## ✨ Features

- **Interactive Greeting**: Personalized hello messages
- **System Information**: Display Python and system details
- **User Input**: Interactive mode for custom names
- **Clean Exit**: Graceful handling of Ctrl+C and quit commands

## 🎯 What You'll See

```
==================================================
🚀 Python Hello World Application
==================================================
📅 Current time: 2024-01-15 14:30:25
🐍 Python version: 3.12.0
📁 Working directory: /path/to/your/project
💻 Platform: win32
==================================================
Hello, World! 🐍
Hello, Developer! 🐍

🎯 Interactive Mode:

👋 Enter your name (or 'quit' to exit): 
```

## 🛠️ Development

This is a starter template. You can:

1. **Add new features** to `main.py`
2. **Create modules** in the `app/` directory
3. **Add dependencies** to `requirements.txt`
4. **Expand functionality** as needed

## 📝 Usage Examples

### Basic Usage
```python
from main import greet

message = greet("Alice")
print(message)  # Output: Hello, Alice! 🐍
```

### Interactive Mode
Run the script and follow the prompts to enter different names and see personalized greetings.

## 🔧 Next Steps

- Add more functionality to the main applicationpaa
- Create additional modules in the `app/` directory
- Set up testing with pytest
- Add web framework like FastAPI for API development
- Implement logging and configuration management

## 🎨 Customization

Feel free to modify the greeting messages, add new functions, or expand the application according to your needs!

---

Happy coding! 🚀
