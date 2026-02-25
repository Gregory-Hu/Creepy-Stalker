"""
原子技能（Atomic Skill）

原子技能是执行层的核心：
- 输入明确
- 输出明确
- 无长期上下文
- 无跨 step 状态

每个原子技能都是独立的、可替换的执行单元
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type
from dataclasses import dataclass
import uuid


@dataclass
class SkillSpec:
    """
    技能规格定义
    
    这是技能的"接口定义"，用于：
    - 验证输入
    - 生成提示词
    - 审计执行
    """
    name: str
    description: str
    inputs: Dict[str, Any]      # {param_name: {type, description, required}}
    outputs: Dict[str, Any]     # {output_name: {type, description}}
    constraints: List[str]      # 执行约束


class AtomicSkill(ABC):
    """
    原子技能基类
    
    所有原子技能必须继承此类
    """
    
    name: str = "base_skill"
    description: str = "Base skill"
    
    @abstractmethod
    def execute(self, **inputs) -> str:
        """
        执行技能
        
        参数：
            **inputs: 输入参数，由 Step 定义
        
        返回：
            str: 执行结果（自然语言描述）
        """
        pass
    
    @property
    def spec(self) -> SkillSpec:
        """返回技能规格"""
        return SkillSpec(
            name=self.name,
            description=self.description,
            inputs={},
            outputs={},
            constraints=[],
        )
    
    def validate_inputs(self, inputs: Dict[str, Any]) -> List[str]:
        """
        验证输入参数
        
        返回错误列表，空列表表示验证通过
        """
        errors = []
        spec = self.spec
        
        # 检查必需参数
        for param_name, param_spec in spec.inputs.items():
            if param_spec.get("required", False) and param_name not in inputs:
                errors.append(f"Missing required input: {param_name}")
        
        return errors


# ========== 技能注册表 ==========

class SkillRegistry:
    """
    技能注册表
    
    管理所有可用的原子技能
    """
    
    def __init__(self):
        self._skills: Dict[str, AtomicSkill] = {}
    
    def register(self, skill: AtomicSkill) -> None:
        """注册技能"""
        self._skills[skill.name] = skill
    
    def register_class(self, skill_class: Type[AtomicSkill]) -> None:
        """注册技能类（自动实例化）"""
        skill = skill_class()
        self.register(skill)
    
    def get_skill(self, name: str) -> Optional[AtomicSkill]:
        """获取技能"""
        return self._skills.get(name)
    
    def execute_skill(self, name: str, **inputs) -> str:
        """
        执行技能
        
        这是 Orchestration 调用的方法
        """
        skill = self.get_skill(name)
        if not skill:
            raise ValueError(f"Skill not found: {name}")
        
        # 验证输入
        errors = skill.validate_inputs(inputs)
        if errors:
            raise ValueError(f"Invalid inputs: {', '.join(errors)}")
        
        # 执行
        return skill.execute(**inputs)
    
    def list_skills(self) -> List[str]:
        """列出所有可用技能"""
        return list(self._skills.keys())
    
    def get_skill_specs(self) -> List[SkillSpec]:
        """获取所有技能规格"""
        return [skill.spec for skill in self._skills.values()]


# ========== 内置原子技能 ==========

class ReadFileSkill(AtomicSkill):
    """读取文件内容"""
    
    name = "ReadFileSkill"
    description = "读取文件的完整内容"
    
    def execute(self, file_path: str, max_lines: Optional[int] = None) -> str:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            if max_lines and len(lines) > max_lines:
                content = ''.join(lines[:max_lines])
                return f"文件内容（前{max_lines}行）:\n{content}\n\n[... 文件还有 {len(lines) - max_lines} 行]"
            
            return f"文件内容:\n{''.join(lines)}"
        
        except FileNotFoundError:
            return f"错误：文件不存在 - {file_path}"
        except Exception as e:
            return f"错误：{str(e)}"
    
    @property
    def spec(self) -> SkillSpec:
        return SkillSpec(
            name=self.name,
            description=self.description,
            inputs={
                "file_path": {"type": "string", "description": "文件路径", "required": True},
                "max_lines": {"type": "integer", "description": "最大读取行数", "required": False},
            },
            outputs={
                "content": {"type": "string", "description": "文件内容"},
            },
            constraints=["只能读取文本文件", "大文件会被截断"],
        )


class WriteFileSkill(AtomicSkill):
    """写入文件内容"""
    
    name = "WriteFileSkill"
    description = "创建或覆盖文件"
    
    def execute(self, file_path: str, content: str) -> str:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"文件已创建：{file_path} ({len(content)} 字节)"
        
        except Exception as e:
            return f"错误：{str(e)}"
    
    @property
    def spec(self) -> SkillSpec:
        return SkillSpec(
            name=self.name,
            description=self.description,
            inputs={
                "file_path": {"type": "string", "description": "文件路径", "required": True},
                "content": {"type": "string", "description": "文件内容", "required": True},
            },
            outputs={
                "result": {"type": "string", "description": "执行结果"},
            },
            constraints=["会覆盖已存在的文件"],
        )


class ListFilesSkill(AtomicSkill):
    """列出目录内容"""
    
    name = "ListFilesSkill"
    description = "列出目录中的文件和子目录"
    
    def execute(self, directory: str, pattern: Optional[str] = None) -> str:
        import os
        from pathlib import Path
        
        try:
            path = Path(directory)
            if not path.exists():
                return f"错误：目录不存在 - {directory}"
            
            if pattern:
                import fnmatch
                items = [
                    str(p.relative_to(path))
                    for p in path.iterdir()
                    if fnmatch.fnmatch(p.name, pattern)
                ]
            else:
                items = [str(p.relative_to(path)) for p in path.iterdir()]
            
            dirs = [i for i in items if (path / i).is_dir()]
            files = [i for i in items if (path / i).is_file()]
            
            result = [f"目录：{directory}"]
            if dirs:
                result.append(f"\n目录 ({len(dirs)}):")
                result.extend(f"  [DIR]  {d}" for d in sorted(dirs))
            if files:
                result.append(f"\n文件 ({len(files)}):")
                result.extend(f"  [FILE] {f}" for f in sorted(files))
            
            return '\n'.join(result)
        
        except Exception as e:
            return f"错误：{str(e)}"
    
    @property
    def spec(self) -> SkillSpec:
        return SkillSpec(
            name=self.name,
            description=self.description,
            inputs={
                "directory": {"type": "string", "description": "目录路径", "required": True},
                "pattern": {"type": "string", "description": "文件名模式（支持通配符）", "required": False},
            },
            outputs={
                "listing": {"type": "string", "description": "目录列表"},
            },
            constraints=["只能列出存在的目录"],
        )


class SearchTextSkill(AtomicSkill):
    """在文件中搜索文本"""
    
    name = "SearchTextSkill"
    description = "在文件中搜索包含特定文本的行"
    
    def execute(self, directory: str, pattern: str, file_pattern: Optional[str] = None) -> str:
        import os
        from pathlib import Path
        import fnmatch
        
        try:
            path = Path(directory)
            if not path.exists():
                return f"错误：目录不存在 - {directory}"
            
            results = []
            for file_path in path.rglob('*'):
                if file_path.is_file():
                    # 文件过滤
                    if file_pattern and not fnmatch.fnmatch(file_path.name, file_pattern):
                        continue
                    
                    # 跳过二进制文件
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            for line_num, line in enumerate(f, 1):
                                if pattern.lower() in line.lower():
                                    results.append({
                                        "file": str(file_path.relative_to(path)),
                                        "line": line_num,
                                        "content": line.strip(),
                                    })
                    except (UnicodeDecodeError, PermissionError):
                        continue
            
            if not results:
                return f"未找到匹配 '{pattern}' 的内容"
            
            output = [f"找到 {len(results)} 处匹配 '{pattern}':"]
            for r in results[:20]:  # 限制输出
                output.append(f"  {r['file']}:{r['line']}: {r['content']}")
            
            if len(results) > 20:
                output.append(f"\n... 还有 {len(results) - 20} 处匹配")
            
            return '\n'.join(output)
        
        except Exception as e:
            return f"错误：{str(e)}"
    
    @property
    def spec(self) -> SkillSpec:
        return SkillSpec(
            name=self.name,
            description=self.description,
            inputs={
                "directory": {"type": "string", "description": "搜索目录", "required": True},
                "pattern": {"type": "string", "description": "搜索文本", "required": True},
                "file_pattern": {"type": "string", "description": "文件名模式", "required": False},
            },
            outputs={
                "matches": {"type": "string", "description": "匹配结果"},
            },
            constraints=["只搜索文本文件", "结果限制为前 20 条"],
        )


class ExecuteCommandSkill(AtomicSkill):
    """执行 shell 命令"""
    
    name = "ExecuteCommandSkill"
    description = "执行 shell 命令并返回输出"
    
    def execute(self, command: str, timeout: int = 60) -> str:
        import subprocess
        
        # 安全检查
        dangerous_patterns = ['rm -rf', 'sudo', 'chmod 777', 'dd if=']
        for pattern in dangerous_patterns:
            if pattern in command:
                return f"错误：命令包含危险操作 - {pattern}"
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            
            output = []
            if result.stdout:
                output.append(f"STDOUT:\n{result.stdout}")
            if result.stderr:
                output.append(f"STDERR:\n{result.stderr}")
            if result.returncode != 0:
                output.append(f"返回码：{result.returncode}")
            
            return '\n'.join(output) if output else "命令执行成功，无输出"
        
        except subprocess.TimeoutExpired:
            return f"错误：命令执行超时（{timeout}秒）"
        except Exception as e:
            return f"错误：{str(e)}"
    
    @property
    def spec(self) -> SkillSpec:
        return SkillSpec(
            name=self.name,
            description=self.description,
            inputs={
                "command": {"type": "string", "description": "要执行的命令", "required": True},
                "timeout": {"type": "integer", "description": "超时时间（秒）", "required": False},
            },
            outputs={
                "output": {"type": "string", "description": "命令输出"},
            },
            constraints=[
                "禁止危险操作（rm -rf, sudo 等）",
                "命令必须在安全沙箱中执行",
            ],
        )


class AnalyzeCodeSkill(AtomicSkill):
    """分析代码"""
    
    name = "AnalyzeCodeSkill"
    description = "分析代码结构、质量和问题"
    
    def execute(self, file_path: str, analysis_type: str = "structure") -> str:
        """
        分析类型：
        - structure: 代码结构（类、函数）
        - quality: 代码质量（复杂度、规范）
        - issues: 潜在问题
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if analysis_type == "structure":
                return self._analyze_structure(file_path, content)
            elif analysis_type == "quality":
                return self._analyze_quality(file_path, content)
            elif analysis_type == "issues":
                return self._analyze_issues(file_path, content)
            else:
                return f"未知分析类型：{analysis_type}"
        
        except Exception as e:
            return f"错误：{str(e)}"
    
    def _analyze_structure(self, file_path: str, content: str) -> str:
        import re
        
        # 简单 Python 代码结构分析
        classes = re.findall(r'^class\s+(\w+)', content, re.MULTILINE)
        functions = re.findall(r'^def\s+(\w+)', content, re.MULTILINE)
        
        result = [f"代码结构分析：{file_path}"]
        result.append(f"\n类 ({len(classes)}):")
        for c in classes:
            result.append(f"  - {c}")
        
        result.append(f"\n函数 ({len(functions)}):")
        for f in functions:
            result.append(f"  - {f}")
        
        result.append(f"\n总行数：{len(content.splitlines())}")
        
        return '\n'.join(result)
    
    def _analyze_quality(self, file_path: str, content: str) -> str:
        lines = content.splitlines()
        
        issues = []
        
        # 检查长函数
        in_function = False
        function_start = 0
        function_name = ""
        
        for i, line in enumerate(lines, 1):
            if line.strip().startswith('def '):
                if in_function and i - function_start > 50:
                    issues.append(f"函数过长：{function_name} ({i - function_start}行)")
                in_function = True
                function_start = i
                function_name = line.strip()
        
        # 检查空注释
        for i, line in enumerate(lines, 1):
            if '# TODO' in line or '# FIXME' in line:
                issues.append(f"待处理项：行{i} - {line.strip()}")
        
        result = [f"代码质量分析：{file_path}"]
        if issues:
            result.append(f"\n发现 {len(issues)} 个问题:")
            for issue in issues[:10]:
                result.append(f"  - {issue}")
        else:
            result.append("\n未发现明显问题")
        
        return '\n'.join(result)
    
    def _analyze_issues(self, file_path: str, content: str) -> str:
        import re
        
        issues = []
        
        # 检查潜在问题
        for i, line in enumerate(content.splitlines(), 1):
            # 裸 except
            if re.search(r'except\s*:', line):
                issues.append(f"行{i}: 裸 except，建议指定异常类型")
            
            # 硬编码路径
            if re.search(r'["\'][/\\][\w/\\]+["\']', line):
                if 'open(' in line or 'Path(' not in line:
                    issues.append(f"行{i}: 可能使用硬编码路径")
            
            # 硬编码密码/密钥
            if re.search(r'(password|secret|api_key)\s*=\s*["\'][^"\']+["\']', line, re.I):
                issues.append(f"行{i}: 可能包含硬编码敏感信息")
        
        result = [f"潜在问题分析：{file_path}"]
        if issues:
            result.append(f"\n发现 {len(issues)} 个潜在问题:")
            for issue in issues[:10]:
                result.append(f"  - {issue}")
        else:
            result.append("\n未发现明显潜在问题")
        
        return '\n'.join(result)
    
    @property
    def spec(self) -> SkillSpec:
        return SkillSpec(
            name=self.name,
            description=self.description,
            inputs={
                "file_path": {"type": "string", "description": "文件路径", "required": True},
                "analysis_type": {
                    "type": "string",
                    "description": "分析类型：structure/quality/issues",
                    "required": False,
                },
            },
            outputs={
                "analysis": {"type": "string", "description": "分析结果"},
            },
            constraints=["目前仅支持 Python 代码"],
        )


# ========== 默认技能注册 ==========

def create_default_registry() -> SkillRegistry:
    """创建包含所有内置技能的注册表"""
    registry = SkillRegistry()
    
    # 注册文件操作技能
    registry.register_class(ReadFileSkill)
    registry.register_class(WriteFileSkill)
    registry.register_class(ListFilesSkill)
    registry.register_class(SearchTextSkill)
    
    # 注册命令执行技能
    registry.register_class(ExecuteCommandSkill)
    
    # 注册分析技能
    registry.register_class(AnalyzeCodeSkill)
    
    return registry
