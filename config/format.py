import os
import re

def find_yml_files(directory):
    """
    递归查找目录中的所有 .yml 文件。
    """
    yml_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(".yml") or file.lower().endswith(".yaml"):
                file_path = os.path.join(root, file)
                print(f"Found: {file_path}")  # 调试信息
                yml_files.append(file_path)
    return yml_files

def convert_indent_to_spaces(content, spaces=2):
    """
    将缩进转换为指定数量的空格。
    """
    return content.expandtabs(spaces)

def trim_trailing_whitespace(content):
    """
    裁剪每行的尾随空格。
    """
    return "\n".join([line.rstrip() for line in content.splitlines()])

def ensure_newline_at_end(content):
    """
    确保文件末尾以新行结束。
    """
    if content and not content.endswith("\n"):
        content += "\n"
    return content

def fix_comment_spacing(content):
    """
    修复注释中 # 后面缺少空格的问题。
    """
    # 使用正则表达式匹配 # 后面没有空格的情况
    fixed_content = re.sub(r"#(\S)", r"# \1", content)
    return fixed_content

def process_file(file_path):
    """
    处理单个文件：转换缩进、裁剪尾随空格、确保末尾有新行，并修复注释空格。
    """
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()

    # 步骤 1：转换缩进为空格
    content = convert_indent_to_spaces(content)

    # 步骤 2：裁剪尾随空格
    # [brackets] too many spaces inside brackets
    # [trailing-spaces] trailing spaces
    content = trim_trailing_whitespace(content)

    # 步骤 3：确保文件末尾以新行结束
    # [new-line-at-end-of-file] no new line character at the end of file
    content = ensure_newline_at_end(content)

    # 步骤 4：修复注释中 # 后面缺少空格的问题
    # [comments] missing starting space in comment
    content = fix_comment_spacing(content)

    # 写回文件
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(content)

def main(directory):
    """
    主函数：递归处理目录中的所有 .yml 文件。
    """
    yml_files = find_yml_files(directory)
    for file_path in yml_files:
        print(f"Processing: {file_path}")
        process_file(file_path)
    print(f"Processed {len(yml_files)} .yml files.")

if __name__ == "__main__":
    target_directory = "."  # 当前目录
    main(target_directory)