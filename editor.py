# -*- coding: utf-8 -*-
"""
音乐笔记 - 编辑器模块
功能：Markdown 编辑、五线谱插入、笔记保存
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, colorchooser
from datetime import datetime
import os
from staff_renderer import StaffRenderer
from PIL import Image, ImageTk


class MusicNoteEditor:
    """音乐笔记编辑器窗口类"""
    
    def __init__(self, parent, file_path=None):
        """
        初始化编辑器窗口
        
        Args:
            parent: 父窗口
            file_path: 笔记文件路径，None 表示新建
        """
        self.parent = parent
        self.file_path = file_path
        self.modified = False
        
        # 创建顶级窗口
        self.window = tk.Toplevel(parent)
        self.window.title("新建笔记" if not file_path else f"编辑：{os.path.basename(file_path)}")
        self.window.geometry("1000x700")
        
        # 初始化变量
        self.content_text = None
        self.status_label = None
        self.line_number_label = None
        
        # 加载已有内容或创建新内容
        self.content = self._load_content()
        
        # 设置界面
        self._setup_ui()
        
        # 绑定保存快捷键
        self.window.bind("<Control-s>", lambda e: self._save_note())
        self.window.bind("<Control-S>", lambda e: self._save_note())
        
        # 窗口关闭事件
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _load_content(self):
        """加载笔记内容"""
        if self.file_path and os.path.exists(self.file_path):
            with open(self.file_path, "r", encoding="utf-8") as f:
                return f.read()
        else:
            # 新建笔记的默认内容
            return f"# 新笔记\n\n创建时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    def _setup_ui(self):
        """设置用户界面"""
        # 主容器
        main_frame = tk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # === 顶部工具栏 ===
        toolbar = tk.Frame(main_frame, bg="#f0f0f0", height=50)
        toolbar.pack(fill=tk.X)
        toolbar.pack_propagate(False)
        
        # 工具栏按钮配置
        btn_config = {
            "font": ("微软雅黑", 10),
            "width": 10,
            "height": 1,
            "bd": 1,
            "relief": tk.RAISED
        }
        
        # 保存按钮
        tk.Button(
            toolbar,
            text="💾 保存",
            bg="#3498DB",
            fg="white",
            command=self._save_note,
            **btn_config
        ).pack(side=tk.LEFT, padx=5, pady=10)
        
        # 插入五线谱按钮
        tk.Button(
            toolbar,
            text="🎼 插入五线谱",
            bg="#9B59B6",
            fg="white",
            command=self._insert_staff,
            **btn_config
        ).pack(side=tk.LEFT, padx=5, pady=10)
        
        # 插入和弦按钮
        tk.Button(
            toolbar,
            text="🎸 插入和弦",
            bg="#E67E22",
            fg="white",
            command=self._insert_chord,
            **btn_config
        ).pack(side=tk.LEFT, padx=5, pady=10)
        
        # 插入歌词按钮
        tk.Button(
            toolbar,
            text="📝 插入歌词",
            bg="#2ECC71",
            fg="white",
            command=self._insert_lyrics,
            **btn_config
        ).pack(side=tk.LEFT, padx=5, pady=10)
        
        # 预览按钮
        tk.Button(
            toolbar,
            text="👁️ 预览",
            bg="#34495E",
            fg="white",
            command=self._preview,
            **btn_config
        ).pack(side=tk.RIGHT, padx=5, pady=10)
        
        # === 编辑区域 ===
        editor_frame = tk.Frame(main_frame)
        editor_frame.pack(fill=tk.BOTH, expand=True)
        
        # 行号区域
        line_number_frame = tk.Frame(editor_frame, bg="#f0f0f0", width=40)
        line_number_frame.pack(side=tk.LEFT, fill=tk.Y)
        line_number_frame.pack_propagate(False)
        
        self.line_number_label = tk.Label(
            line_number_frame,
            text="",
            bg="#f0f0f0",
            fg="#666",
            font=("Consolas", 12),
            anchor=tk.NW,
            justify=tk.LEFT
        )
        self.line_number_label.pack(fill=tk.Y, expand=True)
        
        # 文本编辑区域
        text_frame = tk.Frame(editor_frame)
        text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.content_text = tk.Text(
            text_frame,
            font=("Consolas", 12),
            wrap=tk.WORD,
            undo=True,
            autoseparators=True,
            maxundo=-1
        )
        self.content_text.pack(fill=tk.BOTH, expand=True)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(text_frame, command=self.content_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.content_text.config(yscrollcommand=scrollbar.set)
        
        # 绑定内容变化事件
        self.content_text.bind("<KeyRelease>", self._on_content_change)
        self.content_text.bind("<ButtonRelease>", self._update_line_numbers)
        
        # 插入初始内容
        self.content_text.insert("1.0", self.content)
        self.modified = False
        
        # === 底部状态栏 ===
        status_frame = tk.Frame(main_frame, bg="#ecf0f1", height=25)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        status_frame.pack_propagate(False)
        
        self.status_label = tk.Label(
            status_frame,
            text="就绪",
            font=("微软雅黑", 9),
            bg="#ecf0f1",
            fg="#7f8c8d",
            anchor=tk.W
        )
        self.status_label.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        
        # 字数统计
        self.word_count_label = tk.Label(
            status_frame,
            text="0 字",
            font=("微软雅黑", 9),
            bg="#ecf0f1",
            fg="#7f8c8d"
        )
        self.word_count_label.pack(side=tk.RIGHT, padx=10)
        
        # 更新行号和字数
        self._update_line_numbers()
        self._update_word_count()
        # 在 === 编辑区域 === 之后添加五线谱预览区域
        # === 五线谱预览区域 ===
        staff_preview_frame = tk.Frame(main_frame, bg="#f0f0f0", height=200)
        staff_preview_frame.pack(fill=tk.X, side=tk.BOTTOM)
        staff_preview_frame.pack_propagate(False)
        # 预览标题
        tk.Label(
            staff_preview_frame,
            text="🎼 五线谱预览",
            font=("微软雅黑", 10, "bold"),
            bg="#f0f0f0",
            fg="#333"
        ).pack(anchor=tk.W, padx=10, pady=5)

        # 预览画布
        self.staff_canvas = tk.Canvas(
            staff_preview_frame,
            bg="white",
            width=780,
            height=150
        )
        self.staff_canvas.pack(padx=10, pady=5)

        # 预览标签
        self.staff_preview_label = tk.Label(
            staff_preview_frame,
            text="在编辑器中输入 ABC 记谱法代码块可预览五线谱",
            font=("微软雅黑", 9),
            bg="#f0f0f0",
            fg="#666"
        )
        self.staff_preview_label.pack(pady=5)

        # 自动渲染按钮
        tk.Button(
            staff_preview_frame,
            text="🔄 刷新预览",
            font=("微软雅黑", 9),
            bg="#9B59B6",
            fg="white",
            command=self._render_staff_preview
        ).pack(pady=5)
                
    
    def _on_content_change(self, event=None):
        """内容变化处理"""
        self.modified = True
        self._update_line_numbers()
        self._update_word_count()
        self._update_title()
    
    def _update_line_numbers(self, event=None):
        """更新行号显示"""
        if not self.line_number_label:
            return
        
        total_lines = int(self.content_text.index("end-1c").split(".")[0])
        line_numbers = "\n".join(str(i) for i in range(1, total_lines + 1))
        self.line_number_label.config(text=line_numbers)
    
    def _update_word_count(self):
        """更新字数统计"""
        content = self.content_text.get("1.0", "end-1c")
        char_count = len(content)
        word_count = len(content.split())
        self.word_count_label.config(text=f"{char_count} 字符 | {word_count} 单词")
    
    def _update_title(self):
        """更新窗口标题"""
        base_title = os.path.basename(self.file_path) if self.file_path else "新建笔记"
        if self.modified:
            self.window.title(f"*{base_title} (已修改)")
        else:
            self.window.title(base_title)
    
    def _insert_staff(self):
        """插入五线谱内容"""
        dialog = StaffInsertDialog(self.window)
        if dialog.result:
            # 插入 ABC 记谱法格式的五线谱
            staff_text = f"\n```abc\n{dialog.result}\n```\n"
            self.content_text.insert(tk.INSERT, staff_text)
            self._on_content_change()
            self.status_label.config(text="已插入五线谱")
        
            # 自动渲染预览
            self.window.after(500, self._render_staff_preview)
    
    def _insert_chord(self):
        """插入和弦标记"""
        dialog = ChordInsertDialog(self.window)
        if dialog.result:
            chord_text = f" **{dialog.result}** "
            self.content_text.insert(tk.INSERT, chord_text)
            self._on_content_change()
            self.status_label.config(text="已插入和弦")
    
    def _insert_lyrics(self):
        """插入歌词块"""
        self.content_text.insert(tk.INSERT, "\n> 🎤 歌词:\n> \n")
        self._on_content_change()
        self.status_label.config(text="已插入歌词块")
    
    def _save_note(self):
        """保存笔记"""
        content = self.content_text.get("1.0", "end-1c")
        
        if not self.file_path:
            # 新建笔记，选择保存位置
            default_name = datetime.now().strftime("笔记_%Y%m%d_%H%M%S.md")
            file_path = filedialog.asksaveasfilename(
                title="保存笔记",
                defaultextension=".md",
                filetypes=[("Markdown 文件", "*.md"), ("所有文件", "*.*")],
                initialfile=default_name
            )
            if not file_path:
                return
            self.file_path = file_path
            self.window.title(f"编辑：{os.path.basename(file_path)}")
        
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                f.write(content)
            self.modified = False
            self._update_title()
            self.status_label.config(text=f"已保存：{os.path.basename(self.file_path)}")
            messagebox.showinfo("保存成功", "笔记已保存！")
        except Exception as e:
            messagebox.showerror("保存失败", f"保存时出错：{str(e)}")
    
    def _preview(self):
        """预览笔记"""
        preview_window = tk.Toplevel(self.window)
        preview_window.title("笔记预览")
        preview_window.geometry("800x600")
        
        text_widget = tk.Text(preview_window, font=("微软雅黑", 12), wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True)
        
        content = self.content_text.get("1.0", "end-1c")
        text_widget.insert("1.0", content)
        text_widget.config(state=tk.DISABLED)
        
        scrollbar = ttk.Scrollbar(preview_window, command=text_widget.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_widget.config(yscrollcommand=scrollbar.set)
    
    def _on_close(self):
        """窗口关闭处理"""
        if self.modified:
            response = messagebox.askyesnocancel(
                "未保存的更改",
                "笔记有未保存的更改，是否保存？"
            )
            if response is None:
                return
            elif response:
                self._save_note()
        self.window.destroy()
    def _render_staff_preview(self):
        """渲染五线谱预览"""
        try:
            content = self.content_text.get("1.0", "end-1c")
            
            # 查找 ABC 代码块
            import re
            abc_pattern = r'```abc\n(.*?)\n```'
            matches = re.findall(abc_pattern, content, re.DOTALL)
            
            if not matches:
                self.staff_canvas.delete("all")
                self.staff_preview_label.config(text="未找到 ABC 记谱法代码块")
                return
            
            # 渲染最后一个 ABC 代码块
            abc_text = matches[-1]
            tk_image = StaffRenderer.abc_to_tkimage(abc_text, width=780, height=150)
            
            # 保存引用防止垃圾回收
            self.current_staff_image = tk_image
            
            # 在画布上显示
            self.staff_canvas.delete("all")
            self.staff_canvas.create_image(390, 75, image=tk_image, anchor=tk.CENTER)
            self.staff_preview_label.config(text=f"已渲染 {len(matches)} 个五线谱片段")
            
        except Exception as e:
            self.staff_canvas.delete("all")
            self.staff_preview_label.config(text=f"渲染失败：{str(e)}")

    def _on_content_change(self, event=None):
        """内容变化处理"""
        self.modified = True
        self._update_line_numbers()
        self._update_word_count()
        self._update_title()
        
        # 自动检测 ABC 代码块变化并更新预览
        content = self.content_text.get("1.0", "end-1c")
        if '```abc' in content:
            # 延迟渲染避免频繁刷新
            self.window.after(1000, self._render_staff_preview)


class StaffInsertDialog:
    """五线谱插入对话框"""
    
    def __init__(self, parent):
        """初始化对话框"""
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("插入五线谱")
        self.dialog.geometry("600x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 说明标签
        tk.Label(
            self.dialog,
            text="使用 ABC 记谱法输入五线谱内容",
            font=("微软雅黑", 10),
            fg="#666"
        ).pack(pady=5)
        
        # 输入框
        self.text_input = tk.Text(self.dialog, font=("Consolas", 11), height=8)
        self.text_input.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)
        
        # 绑定内容变化
        self.text_input.bind("<KeyRelease>", self._on_text_change)
        
        # 预览区域
        preview_frame = tk.Frame(self.dialog, bg="#f0f0f0")
        preview_frame.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)
        
        tk.Label(
            preview_frame,
            text="实时预览:",
            font=("微软雅黑", 9),
            bg="#f0f0f0"
        ).pack(anchor=tk.W, padx=5)
        
        self.preview_canvas = tk.Canvas(
            preview_frame,
            bg="white",
            width=500,
            height=150
        )
        self.preview_canvas.pack(padx=5, pady=5)
        
        self.preview_label = tk.Label(
            preview_frame,
            text="输入 ABC 代码后自动预览",
            font=("微软雅黑", 9),
            bg="#f0f0f0",
            fg="#666"
        )
        self.preview_label.pack(pady=5)
        
        # 示例
        example = """示例:
X:1
T:小星星
M:4/4
L:1/4
K:C
C C G G | A A G2 | F F E E | D D C2"""
        
        tk.Label(
            self.dialog,
            text=example,
            font=("Consolas", 9),
            bg="#f5f5f5",
            justify=tk.LEFT
        ).pack(padx=20, pady=5, fill=tk.X)
        
        # 按钮区域
        btn_frame = tk.Frame(self.dialog)
        btn_frame.pack(pady=10)
        
        tk.Button(
            btn_frame,
            text="确定",
            width=10,
            command=self._confirm
        ).pack(side=tk.LEFT, padx=10)
        
        tk.Button(
            btn_frame,
            text="取消",
            width=10,
            command=self.dialog.destroy
        ).pack(side=tk.LEFT, padx=10)
        
        # 初始化预览图片引用
        self.current_preview_image = None
        
        self.dialog.wait_window()
    
    def _on_text_change(self, event=None):
        """文本变化时更新预览"""
        abc_text = self.text_input.get("1.0", "end-1c").strip()
        if abc_text:
            try:
                self.dialog.after(500, lambda: self._update_preview(abc_text))
            except:
                pass
    
    def _update_preview(self, abc_text):
        """更新预览"""
        try:
            tk_image = StaffRenderer.abc_to_tkimage(abc_text, width=500, height=150)
            self.current_preview_image = tk_image
            self.preview_canvas.delete("all")
            self.preview_canvas.create_image(250, 75, image=tk_image, anchor=tk.CENTER)
            self.preview_label.config(text="预览成功")
        except Exception as e:
            self.preview_canvas.delete("all")
            self.preview_label.config(text=f"预览失败：{str(e)}")
    
    def _confirm(self):
        """确认输入"""
        self.result = self.text_input.get("1.0", "end-1c").strip()
        if self.result:
            self.dialog.destroy()


class ChordInsertDialog:
    """和弦插入对话框"""
    
    def __init__(self, parent):
        """初始化对话框"""
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("插入和弦")
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 和弦选择区域
        chord_frame = tk.Frame(self.dialog)
        chord_frame.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)
        
        # 根音
        tk.Label(chord_frame, text="根音:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.root_var = tk.StringVar(value="C")
        root_options = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        root_menu = ttk.Combobox(chord_frame, textvariable=self.root_var, values=root_options, width=5)
        root_menu.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        # 和弦类型
        tk.Label(chord_frame, text="类型:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.type_var = tk.StringVar(value="")
        type_options = ["", "m", "7", "maj7", "m7", "dim", "aug", "sus4", "sus2"]
        type_menu = ttk.Combobox(chord_frame, textvariable=self.type_var, values=type_options, width=8)
        type_menu.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # 预览
        self.preview_label = tk.Label(
            chord_frame,
            text="C",
            font=("微软雅黑", 24, "bold"),
            fg="#9B59B6"
        )
        self.preview_label.grid(row=2, column=0, columnspan=2, pady=20)
        
        # 绑定更新
        self.root_var.trace("w", lambda *args: self._update_preview())
        self.type_var.trace("w", lambda *args: self._update_preview())
        
        # 按钮
        btn_frame = tk.Frame(self.dialog)
        btn_frame.pack(pady=10)
        
        tk.Button(
            btn_frame,
            text="确定",
            width=10,
            command=self._confirm
        ).pack(side=tk.LEFT, padx=10)
        
        tk.Button(
            btn_frame,
            text="取消",
            width=10,
            command=self.dialog.destroy
        ).pack(side=tk.LEFT, padx=10)
        
        self.dialog.wait_window()
    
    def _update_preview(self):
        """更新和弦预览"""
        chord = self.root_var.get() + self.type_var.get()
        self.preview_label.config(text=chord)
    
    def _confirm(self):
        """确认选择"""
        self.result = self.root_var.get() + self.type_var.get()
        self.dialog.destroy()