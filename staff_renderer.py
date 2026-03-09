# -*- coding: utf-8 -*-
"""
五线谱渲染模块
功能：将 ABC 记谱法转换为可视化五线谱图片
"""

# 依赖安装：pip install music21 pillow
from music21 import converter, stream
# 正确导入异常类，兼容不同版本，添加 type ignore 消除 Pylance 静态检查警告
try:
    from music21.exceptions import ConverterException  # type: ignore[import-not-found]
except ImportError:
    ConverterException = Exception

from PIL import Image, ImageTk
import tempfile
import os


class StaffRenderer:
    """五线谱渲染器"""
    
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
        将乐谱渲染为图片
        
        Args:
            score: music21.stream.Stream 对象
            width: 图片宽度 (备用方案使用)
            height: 图片高度 (备用方案使用)
            
        Returns:
            PIL.Image 对象
        """
        # 使用 NamedTemporaryFile 避免竞态条件
        temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        temp_path = temp_file.name
        temp_file.close()
        
        try:
            # 执行渲染，直接指定格式无需修改 UserSettings
            score.write('png', fp=temp_path)
            
            # 检查文件是否生成
            if not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
                raise FileNotFoundError("渲染生成的图片文件为空")
            
            img = Image.open(temp_path)
            return img.convert('RGB')
        except Exception as e:
            # 备用方案：手动绘制简化五线谱
            print(f"主渲染失败，使用备用方案：{e}")
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