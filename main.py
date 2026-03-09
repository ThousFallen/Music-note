# -*- coding: utf-8 -*-
"""
音乐笔记软件 - 主程序入口
功能：打开笔记、创建笔记、及时录音
"""

import tkinter as tk
from tkinter import messagebox, filedialog
import os
from datetime import datetime

# 导入编辑器模块
from editor import MusicNoteEditor


class MusicNotesApp:
    """音乐笔记应用主窗口类"""
    
    def __init__(self, root):
        """初始化主窗口"""
        self.root = root
        self.root.title("音乐笔记")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # 数据目录
        self.data_dir = os.path.join(os.path.dirname(__file__), "data", "projects")
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 初始化界面
        self._setup_ui()
        
    def _setup_ui(self):
        """设置用户界面"""
        # 顶部标题区域
        title_frame = tk.Frame(self.root, bg="#4A90E2", height=80)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(
            title_frame, 
            text="🎵 音乐笔记", 
            font=("微软雅黑", 24, "bold"),
            bg="#4A90E2", 
            fg="white"
        )
        title_label.pack(pady=20)
        
        # 中间功能按钮区域
        button_frame = tk.Frame(self.root, bg="#f5f5f5")
        button_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=40)
        
        # 按钮样式配置
        button_config = {
            "font": ("微软雅黑", 14),
            "width": 20,
            "height": 2,
            "bd": 0,
            "relief": tk.FLAT
        }
        
        # 打开笔记按钮
        self.btn_open = tk.Button(
            button_frame,
            text="📂 打开笔记",
            bg="#3498DB",
            fg="white",
            command=self._open_note,
            **button_config
        )
        self.btn_open.pack(pady=15)
        
        # 创建笔记按钮
        self.btn_create = tk.Button(
            button_frame,
            text="📝 创建笔记",
            bg="#2ECC71",
            fg="white",
            command=self._create_note,
            **button_config
        )
        self.btn_create.pack(pady=15)
        
        # 及时录音按钮
        self.btn_record = tk.Button(
            button_frame,
            text="🎤 及时录音",
            bg="#E74C3C",
            fg="white",
            command=self._start_recording,
            **button_config
        )
        self.btn_record.pack(pady=15)
        
        # 底部状态栏
        status_frame = tk.Frame(self.root, bg="#ecf0f1", height=30)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        status_frame.pack_propagate(False)
        
        self.status_label = tk.Label(
            status_frame,
            text="就绪 | 数据目录：" + self.data_dir,
            font=("微软雅黑", 9),
            bg="#ecf0f1",
            fg="#7f8c8d",
            anchor=tk.W
        )
        self.status_label.pack(padx=10, pady=5)
    
    def _open_note(self):
        """打开已有笔记"""
        file_path = filedialog.askopenfilename(
            title="选择笔记文件",
            filetypes=[("Markdown 文件", "*.md"), ("所有文件", "*.*")],
            initialdir=self.data_dir
        )
        
        if file_path:
            # 打开编辑器窗口
            MusicNoteEditor(self.root, file_path)
            self.status_label.config(text=f"已打开：{os.path.basename(file_path)}")
    
    def _create_note(self):
        """创建新笔记"""
        # 直接打开编辑器窗口（新建模式）
        MusicNoteEditor(self.root, None)
        self.status_label.config(text="已创建新笔记")
    
    def _start_recording(self):
        """开始录音功能"""
        messagebox.showinfo(
            "录音功能", 
            "录音功能即将开发！\n\n后续版本将支持：\n"
            "1. 麦克风录音\n"
            "2. MIDI 输入录制\n"
            "3. 音频保存与播放"
        )


def main():
    """程序入口函数"""
    root = tk.Tk()
    app = MusicNotesApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()