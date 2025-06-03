import os
import time
import psutil
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import reg_operations
from loguru import logger

def get_file_processes(file_path):
    """
    获取正在占用文件的进程列表
    :param file_path: 文件路径
    :return: 占用文件的进程列表
    """
    processes = []
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            for item in proc.open_files():
                if item.path == file_path:
                    processes.append(f"{proc.name()} (PID: {proc.pid})")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return processes

def linux_style_delete(file_path):
    """
    实现Linux风格的文件删除逻辑
    当文件被占用时等待直到可以删除
    :param file_path: 要删除的文件路径
    """
    while True:
        try:
            os.remove(file_path)
            return True
        except PermissionError:
            # 文件被占用，等待后重试
            logger.trace(f"文件被占用，等待1s后重试: {file_path}")
            time.sleep(1)
        except FileNotFoundError:
            # 文件不存在
            logger.warning("文件不存在，可能已经被删除")
            return False
        except Exception as e:
            # 其他错误
            logger.error(f"删除文件失败: {e}")
            logger.error('文件删除异常 | 路径:{} | 异常类型:{}', file_path, type(e).__name__, exc_info=True)
            return False

class FileDeleterApp:
    def __init__(self, root):
        os.makedirs('logs', exist_ok=True)
        logger.add('logs/file_deleter.log', rotation='10 MB', encoding='utf-8')
        self.root = root
        root.title("ChameleonFileOps")
        self.shutdown_flag = False
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # 创建界面组件
        self.label = tk.Label(root, text="选择要删除的文件:")
        self.label.pack(pady=10)
        
        self.select_button = tk.Button(root, text="选择文件", command=self.select_file)
        self.select_button.pack(pady=5)
        
        self.delete_button = tk.Button(root, text="删除文件", command=self.delete_file, state=tk.DISABLED)
        self.delete_button.pack(pady=5)
        
        # 右键菜单管理按钮
        self.add_menu_button = tk.Button(root, text="添加到右键菜单", command=self.add_to_context_menu)
        self.add_menu_button.pack(pady=5)
        
        self.remove_menu_button = tk.Button(root, text="移除右键菜单", command=self.remove_from_context_menu)
        self.remove_menu_button.pack(pady=5)
        
        self.status_label = tk.Label(root, text="")
        self.status_label.pack(pady=10)
        
        # 删除队列列表
        self.queue_label = tk.Label(root, text="删除队列:")
        self.queue_label.pack(pady=5)
        
        self.queue_listbox = tk.Listbox(root, height=10, width=50)
        self.queue_listbox.pack(pady=5)
        
        self.selected_file = []
        self.file_queue = []

        logger.trace('初始化完成')
    
    def select_file(self):
        logger.debug('开始选择文件')
        file_paths = filedialog.askopenfilenames()
        if file_paths:
            self.selected_file = list(file_paths)
            self.delete_button.config(state=tk.NORMAL)
            self.status_label.config(text=f"已选择: {len(self.selected_file)} 个文件")
            logger.info(f'已选择 {len(file_paths)} 个文件: {file_paths}')
    
    def delete_file(self):
        if self.selected_file:
            for file_path in self.selected_file:
                self.file_queue.append(file_path)
                self.queue_listbox.insert(tk.END, file_path)
            self.delete_button.config(state=tk.DISABLED)
            logger.info(f'开始删除队列: {self.selected_file}')
            for file_path in self.selected_file:
                thread = threading.Thread(target=self._delete_in_thread, args=(file_path,))
                thread.daemon = True
                thread.start()
            self.selected_file = []
    
    def _delete_in_thread(self, file_path):
        while not self.shutdown_flag and not linux_style_delete(file_path):
            time.sleep(1)
        if self.shutdown_flag:
            self.root.after(0, lambda: messagebox.showinfo("中断", "删除操作已取消"))
            return
        logger.success(f'文件删除成功: {file_path}')
        self.root.after(0, lambda: self.status_label.config(text=f"已删除: {file_path}"))
        self.root.after(0, lambda: self.delete_button.config(state=tk.DISABLED))
        self.root.after(0, lambda: self.file_queue.remove(file_path))
        self.root.after(0, lambda: self.queue_listbox.delete(self.queue_listbox.get(0, tk.END).index(file_path)))
    
    def add_to_context_menu(self):
        if reg_operations.add_to_context_menu():
            logger.success('添加到右键菜单成功')
            messagebox.showinfo("成功", "已添加到右键菜单")
        else:
            logger.error('添加到右键菜单失败')
            messagebox.showerror("错误", "添加右键菜单失败")
    
    def remove_from_context_menu(self):
        if reg_operations.remove_from_context_menu():
            logger.success('从右键菜单移除成功')
            messagebox.showinfo("成功", "已从右键菜单移除")
        else:
            logger.error('从右键菜单移除失败')
            messagebox.showerror("错误", "移除右键菜单失败")
    
    def on_close(self):
        """
        处理窗口关闭事件
        1. 设置关闭标志位停止后台线程
        2. 销毁Tkinter根窗口
        """
        self.shutdown_flag = True
        logger.info('程序退出')
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = FileDeleterApp(root)
    root.mainloop()