---
applyTo: "**/*.py"
---

# Python 项目通用编码标准

## **命名约定 (Naming Conventions)**

* **模块 (Modules)**: lower_snake_case (例如：my_module.py)  
* **包 (Packages)**: lower_snake_case (例如：my_package)  
* **类 (Classes)**: PascalCase (例如：MyClass)  
* **异常 (Exceptions)**: PascalCase，并以 Error 结尾 (例如：MyCustomError)  
* **函数 (Functions)**: lower_snake_case (例如：def my_function():)  
* **方法 (Methods)**: lower_snake_case (例如：def my_method(self):)  
* **实例变量 (Instance Variables)**: lower_snake_case (例如：self.instance_var)  
* **函数参数 (Function Arguments)**: lower_snake_case (例如：def func(arg_one, arg_two):)  
* **局部变量 (Local Variables)**: lower_snake_case (例如：local_var = 1)  
* **常量 (Constants)**: ALL_CAPS_SNAKE_CASE (例如：GLOBAL_CONSTANT = 42)  
* **私有成员 (Private Members)**: 以单下划线开头 _private_member (约定俗成，非强制)  
* **"受保护"成员 (Protected Members for Subclassing)**: 以单下划线开头 _protected_member  
* **名称修饰 (Name Mangling for Class-Private Names)**: 以双下划线开头 __very_private_member (避免在子类中意外覆盖)

## **代码布局 (Code Layout)**

* **缩进 (Indentation)**: 使用4个空格进行缩进，不要使用制表符 (Tab)。  
* **行长度 (Line Length)**: 每行代码不超过79个字符 (PEP 8 推荐)。注释或文档字符串每行不超过72个字符。  
* 空行 (Blank Lines):  
  - 顶级函数和类定义之间用两个空行隔开。  
  - 类中的方法定义之间用一个空行隔开。  
  - 在函数内部，可以使用空行来分隔逻辑上不同的代码块。  
* 导入 (Imports):  
  - 导入语句应始终位于文件顶部，在模块注释和文档字符串之后，全局变量和常量定义之前。  
  - 导入应按以下顺序分组：  
  1. 标准库导入 (例如：import os)  
  2. 相关第三方库导入 (例如：import requests)  
  3. 本地应用程序/库特定导入 (例如：from my_package import my_module)  
  - 每组导入之间用一个空行隔开。  
  - 推荐使用绝对导入。

## **注释 (Comments)**

* **块注释 (Block Comments)**: 通常用于注释掉代码块或解释紧随其后的代码块。以 # 和一个空格开头，并与它们注释的代码具有相同的缩进级别。  
* **行内注释 (Inline Comments)**: 应谨慎使用。行内注释是与语句在同一行上的注释。它们应该与语句至少隔开两个空格，并以 # 和一个空格开头。  
* 文档字符串 (Docstrings):  
  - 为所有公共模块、函数、类和方法编写文档字符串。  
  - 文档字符串应以简洁的摘要开始，然后是更详细的解释（如果需要）。  
  - 对于函数和方法，文档字符串应描述其作用、参数和返回值。  
  - 使用三重双引号 """Docstring goes here."""。  
  - 遵循 PEP 257 文档字符串约定。
  - 示例如下：
    ```python
    class UserService:
        """用户服务类
        
        提供用户相关的业务逻辑处理
        """
        
        async def create_user(self, user_data: UserCreate) -> User:
            """创建新用户
            
            Args:
                user_data: 用户创建数据
                
            Returns:
                创建的用户对象
                
            Raises:
                ValueError: 当用户数据无效时
                DuplicateError: 当用户已存在时
            """
            pass
    ```

## **类型提示 (Type Hints)**

* **强烈推荐**在新代码中使用类型提示 (Python 3.13+)。  
* 使用 typing 模块来定义复杂的类型。  
* 类型提示可以提高代码的可读性和可维护性，并帮助静态分析工具捕获错误。  

* 例如：  
  ```python
  def greet(name: str) -> str:  
      return f"Hello, {name}"

  from typing import List, Dict  
  def process_data(data: List[Dict[str, int]]) -> None:  
      # ...  
      pass
    ```

## **错误处理 (Error Handling)**

* 使用 try...except 块来处理可能发生的异常。  
* 捕获具体的异常，而不是通用的 Exception (除非有充分理由)。  
* 在 except 块中提供有意义的错误信息或日志。  
* 适当时使用 finally 块来确保资源得到释放 (例如，文件句柄)。  
* 考虑自定义异常来表示应用程序特定的错误情况。  
    ```python
    class MyCustomError(Exception):  
        """A custom error for my application."""  
        pass

    try:  
        # Code that might raise an error  
        risky_operation()  
    except FileNotFoundError:  
        logger.error("Configuration file not found.")  
    except MyCustomError as e:  
        logger.error(f"An application specific error occurred: {e}")  
    except Exception as e:  
        logger.critical(f"An unexpected error occurred: {e}", exc_info=True)  
    finally:  
        # Cleanup code  
        pass
    ```

## **编程建议 (Programming Recommendations)**

* **遵循 PEP 8**: Python Enhancement Proposal 8，是 Python 代码的风格指南。使用 ruff 或 pylint 等工具来检查代码是否符合 PEP 8。  
* **保持简单 (Keep It Simple, Stupid - KISS)**: 编写清晰、简洁、易于理解的代码。  
* **不要重复自己 (Don't Repeat Yourself - DRY)**: 避免代码冗余，通过函数、类或模块来重用代码。  
* **显式优于隐式 (Explicit is better than implicit)**: 代码应该清晰地表达其意图。  
* **使用列表推导式 (List Comprehensions) 和生成器表达式 (Generator Expressions)**: 当合适的时候，使用它们来创建列表或迭代器，使代码更简洁高效。  
* **上下文管理器 (Context Managers - with statement)**: 用于管理资源 (如文件、数据库连接、锁)，确保它们在使用完毕后正确释放。 
    ```python 
    with open('myfile.txt', 'r') as f:  
        content = f.read()
    ```

* **日志 (Logging)**: 使用 logging 模块进行日志记录，而不是 print() 语句，特别是在库和应用程序中。  
* **测试 (Testing)**: 编写单元测试 (使用 unittest 或 pytest 等框架) 来确保代码的正确性和可靠性。

## **其他**

* **文件编码 (File Encoding)**: 默认使用 UTF-8 编码。  
* **Shebang Line (for executable scripts)**: 如果脚本是可执行的，在文件顶部添加代码头注释：
    ```text
    """
    @Author: li
    @Email: lijianqiao2906@live.com
    @FileName: <当前文件名>
    @DateTime: <当前时间>
    @Docs: <当前模块功能>
    """
    ```