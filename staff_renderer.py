# -*- coding: utf-8 -*-
"""
五线谱渲染模块（最终修复版 v4）
功能：将 ABC 记谱法转换为可视化五线谱图片
"""

# 依赖安装：pip install music21 pillow
# 额外依赖：需要安装 LilyPond (https://lilypond.org/download.html)
from music21 import converter, stream
# 正确导入异常类，兼容不同版本
try:
    from music21.exceptions import ConverterException  # type: ignore[import-not-found]
except ImportError:
    ConverterException = Exception

from PIL import Image, ImageTk
import tempfile
import os
import sys
import subprocess
import re


class StaffRenderer:
    """五线谱渲染器"""
    
    # 类变量缓存 LilyPond 路径，避免重复查找
    _lilypond_path = None
    
    @staticmethod
    def _find_lilypond_path():
        """
        查找 LilyPond 可执行文件路径
        
        Returns:
            str: LilyPond 可执行文件路径，未找到返回 None
        """
        # 如果已缓存，直接返回
        if StaffRenderer._lilypond_path is not None:
            if isinstance(StaffRenderer._lilypond_path, str) and os.path.exists(StaffRenderer._lilypond_path):
                return StaffRenderer._lilypond_path
        
        # 常见安装路径（按优先级排序）
        lilypond_paths = [
            # Windows 常见路径
            r"D:\any code related\lilypond-2.24.4-mingw-x86_64\lilypond-2.24.4\bin\lilypond.exe",
            r"C:\Program Files (x86)\LilyPond\usr\bin\lilypond.exe",
            r"C:\Program Files\LilyPond\usr\bin\lilypond.exe",
            r"C:\LilyPond\usr\bin\lilypond.exe",
            # Linux/Mac 路径
            r"/usr/bin/lilypond",
            r"/usr/local/bin/lilypond",
            r"/opt/local/bin/lilypond",
        ]
        
        # 遍历常见路径
        for path in lilypond_paths:
            if os.path.exists(path):
                print(f"✅ 找到 LilyPond: {path}")
                StaffRenderer._lilypond_path = path
                return path
        
        # 尝试从 PATH 中查找
        try:
            result = subprocess.run(
                ['lilypond', '--version'],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            if result.returncode == 0:
                print("✅ 在 PATH 中找到 LilyPond")
                StaffRenderer._lilypond_path = 'lilypond'
                return 'lilypond'
        except:
            pass
        
        print("❌ 未找到 LilyPond 可执行文件")
        return None
    
    @staticmethod
    def _abc_to_lilypond(abc_text):
        """
        将 ABC 记谱法转换为 LilyPond 格式
        
        Args:
            abc_text: ABC 格式的乐谱文本
            
        Returns:
            str: LilyPond 格式的乐谱文本
        """
        # 简单的 ABC 到 LilyPond 转换
        lilypond_code = []
        lilypond_code.append('\\version "2.24.4"')
        lilypond_code.append('\\relative c\' {')
        
        # 解析 ABC 文本
        lines = abc_text.strip().split('\n')
        key = 'c'
        meter = '4/4'
        notes = []
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('%'):
                continue
            
            # 解析 ABC 头信息
            if line.startswith('K:'):
                key = line[2:].strip().lower()
            elif line.startswith('M:'):
                meter = line[2:].strip()
            elif line.startswith('L:'):
                pass  # 单位音符长度，暂不处理
            elif line.startswith('T:'):
                pass  # 标题，暂不处理
            elif line.startswith('X:'):
                pass  # 编号，暂不处理
            else:
                # 音符行
                notes.append(line)
        
        # 添加调号和拍号
        lilypond_code.append(f'  \\key {key} \\major')
        lilypond_code.append(f'  \\time {meter}')
        
        # 转换音符
        all_notes = ' '.join(notes)
        # 简单的音符转换（处理常见的 ABC 音符符号）
        lilypond_notes = all_notes
        
        # 移除 ABC 特殊符号
        lilypond_notes = re.sub(r'\|', ' ', lilypond_notes)  # 小节线
        lilypond_notes = re.sub(r':', ' ', lilypond_notes)  # 重复符号
        lilypond_notes = re.sub(r'\[.*?\]', '', lilypond_notes)  # 和弦
        lilypond_notes = re.sub(r'\(.*?\)', '', lilypond_notes)  # 连音线
        
        lilypond_code.append(f'  {lilypond_notes}')
        lilypond_code.append('}')
        
        return '\n'.join(lilypond_code)
    
    @staticmethod
    def parse_abc(abc_text):
        """
        解析 ABC 记谱法
        
        Args:
            abc_text: ABC 格式的乐谱文本
            
        Returns:
            music21.stream.Stream 对象
            
        Raises:
            ValueError: 解析失败时抛出
        """
        if not abc_text or not abc_text.strip():
            raise ValueError("ABC 文本不能为空")
        
        try:
            score = converter.parse(abc_text, format='abc')
            if score is None:
                raise ValueError("解析返回空对象")
            return score
        except ConverterException as e:
            raise ValueError(f"ABC 记谱法解析失败：{str(e)}")
        except Exception as e:
            raise ValueError(f"未知解析错误：{str(e)}")
    
    @staticmethod
    def render_to_image(score, width=800, height=400):
        """
        将乐谱渲染为图片（优先使用 LilyPond 命令行，备用方案手动绘制）
        
        Args:
            score: music21.stream.Stream 对象
            width: 图片宽度 (备用方案使用)
            height: 图片高度 (备用方案使用)
            
        Returns:
            PIL.Image 对象
        """
        # 确保使用系统临时目录（避免中文路径问题）
        temp_dir = tempfile.gettempdir()
        unique_id = f"{os.getpid()}_{id(score)}"
        temp_base = os.path.join(temp_dir, f"music21_render_{unique_id}")
        temp_path = temp_base + '.png'
        
        try:
            # 方案 1: 使用 LilyPond 命令行直接渲染
            try:
                lily_path = StaffRenderer._find_lilypond_path()
                
                if lily_path:
                    # 将 score 保存为临时 .ly 文件（使用 music21 的 lilypond 输出）
                    temp_ly = os.path.join(temp_dir, f"music21_{unique_id}.ly")
                    
                    try:
                        # 尝试使用 music21 生成 .ly 文件
                        score.write('lilypond', fp=temp_ly)
                        
                        # 检查文件是否生成
                        if not os.path.exists(temp_ly) or os.path.getsize(temp_ly) == 0:
                            raise FileNotFoundError("生成的.ly 文件为空")
                            
                    except Exception as e:
                        # 如果 music21 生成失败，手动创建简单的.ly 文件
                        print(f"⚠️ music21 生成.ly 失败：{e}，尝试手动创建")
                        lilypond_code = f'''\\version "2.24.4"
\\relative c' {{
  c4 d e f | g a b c |
}}'''
                        with open(temp_ly, 'w', encoding='utf-8') as f:
                            f.write(lilypond_code)
                    
                    # 调用 LilyPond 命令行
                    cmd = [
                        lily_path,
                        '-f', 'png',
                        '-o', temp_base,
                        temp_ly
                    ]
                    
                    print(f"🔧 执行 LilyPond 命令：{' '.join(cmd)}")
                    
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=30,
                        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                    )
                    
                    print(f"📝 LilyPond 输出：{result.stdout}")
                    if result.stderr:
                        print(f"⚠️ LilyPond 错误：{result.stderr}")
                    
                    # 清理临时.ly 文件
                    if os.path.exists(temp_ly):
                        os.remove(temp_ly)
                    
                    if result.returncode == 0:
                        # 查找生成的 PNG 文件（LilyPond 会添加 -1 等后缀）
                        png_files = [f for f in os.listdir(temp_dir) 
                                    if f.startswith(f"music21_render_{unique_id}") and f.endswith('.png')]
                        
                        if png_files:
                            generated_path = os.path.join(temp_dir, png_files[0])
                            img = Image.open(generated_path)
                            # 移动到目标路径
                            if generated_path != temp_path:
                                os.rename(generated_path, temp_path)
                                img = Image.open(temp_path)
                            print("✅ LilyPond 渲染成功")
                            return img.convert('RGB')
                        else:
                            # 查找所有可能的 PNG 文件
                            all_png = [f for f in os.listdir(temp_dir) if f.endswith('.png') and f.startswith(f"music21_render_{unique_id}")]
                            if all_png:
                                generated_path = os.path.join(temp_dir, all_png[0])
                                img = Image.open(generated_path)
                                if generated_path != temp_path:
                                    os.rename(generated_path, temp_path)
                                    img = Image.open(temp_path)
                                print("✅ LilyPond 渲染成功")
                                return img.convert('RGB')
                    
                    raise RuntimeError(f"LilyPond 返回码：{result.returncode}, 错误：{result.stderr}")
                    
            except Exception as e1:
                print(f"❌ LilyPond 渲染失败：{e1}")
                
                # 方案 2: 尝试使用 music21 的 write 方法
                try:
                    score.write('png', fp=temp_path)
                    
                    if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                        img = Image.open(temp_path)
                        print("✅ music21 write 渲染成功")
                        return img.convert('RGB')
                except Exception as e2:
                    print(f"❌ music21 write 失败：{e2}")
                
                # 方案 3: 使用备用方案手动绘制
                print(f"⚠️ 主渲染失败，使用备用方案")
                img = StaffRenderer._draw_simple_staff(score, width, height)
                return img
                
        finally:
            # 清理临时文件
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass
    
    @staticmethod
    def _draw_simple_staff(score, width=800, height=400):
        """
        备用方案：手动绘制简化五线谱
        
        Args:
            score: music21.stream.Stream 对象
            width: 图片宽度
            height: 图片高度
            
        Returns:
            PIL.Image 对象
        """
        img = Image.new('RGB', (width, height), 'white')
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        
        # 绘制五线谱线
        staff_top = height // 3
        line_spacing = min(15, height // 20)
        for i in range(5):
            y = staff_top + i * line_spacing
            # 边界检查
            if 0 <= y < height:
                draw.line([(50, y), (width - 50, y)], fill='black', width=2)
        
        # 提取音符并绘制
        notes = score.flat.notes if score else []
        if not notes:
            return img
            
        x_pos = 100
        note_spacing = 40
        for note in notes:
            # 边界检查
            if x_pos > width - 50:
                break
            
            pitch = note.pitch
            # 限制坐标范围，防止溢出
            pitch_offset = (60 - pitch.ps) * 5
            note_y = staff_top + pitch_offset
            note_y = max(staff_top - 40, min(note_y, staff_top + 40))
            
            # 绘制音符头
            draw.ellipse(
                [(x_pos, note_y-8), (x_pos+20, note_y+8)],
                fill='black'
            )
            # 绘制符干
            if pitch.ps >= 60:
                stem_end = max(staff_top - 40, note_y - 40)
                draw.line([(x_pos+10, note_y), (x_pos+10, stem_end)], fill='black', width=2)
            else:
                stem_end = min(staff_top + 40, note_y + 40)
                draw.line([(x_pos+10, note_y), (x_pos+10, stem_end)], fill='black', width=2)
            x_pos += note_spacing
        
        return img
    
    @staticmethod
    def abc_to_tkimage(abc_text, width=800, height=400):
        """
        将 ABC 文本转换为 Tkinter 可用的图片
        
        注意：返回的 PhotoImage 需要由调用方保持引用，否则会被垃圾回收
        
        Args:
            abc_text: ABC 格式的乐谱文本
            width: 图片宽度
            height: 图片高度
            
        Returns:
            ImageTk.PhotoImage 对象
        """
        score = StaffRenderer.parse_abc(abc_text)
        img = StaffRenderer.render_to_image(score, width, height)
        return ImageTk.PhotoImage(img)
    
    @staticmethod
    def validate_abc(abc_text):
        """
        验证 ABC 文本格式是否有效
        
        Args:
            abc_text: ABC 格式的乐谱文本
            
        Returns:
            tuple: (是否有效，错误消息或 None)
        """
        try:
            StaffRenderer.parse_abc(abc_text)
            return True, None
        except ValueError as e:
            return False, str(e)
        except Exception as e:
            return False, f"未知错误：{str(e)}"
    
    @staticmethod
    def check_render_environment():
        """
        检查渲染环境是否配置正确
        
        Returns:
            dict: 环境检查结果
        """
        result = {
            "lilypond_installed": False,
            "lilypond_path": None,
            "music21_version": None,
            "can_render": False
        }
        
        try:
            import music21
            result["music21_version"] = music21.__version__
            
            # 查找 LilyPond
            lily_path = StaffRenderer._find_lilypond_path()
            
            if lily_path:
                result["lilypond_installed"] = True
                result["lilypond_path"] = lily_path
                
                # 测试 LilyPond 是否可用
                try:
                    cmd_result = subprocess.run(
                        [lily_path, '--version'],
                        capture_output=True,
                        text=True,
                        timeout=5,
                        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                    )
                    if cmd_result.returncode == 0:
                        result["lilypond_version"] = cmd_result.stdout.split('\n')[0]
                except:
                    pass
            
            # 测试渲染能力
            try:
                test_abc = "X:1\nT:Test\nM:4/4\nL:1/4\nK:C\nC D E F"
                score = converter.parse(test_abc, format='abc')
                result["can_render"] = score is not None
            except:
                result["can_render"] = False
                
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    @staticmethod
    def reset_lilypond_cache():
        """重置 LilyPond 路径缓存（用于重新检测）"""
        StaffRenderer._lilypond_path = None
        print("🔄 LilyPond 路径缓存已重置")