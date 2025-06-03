import winreg
import os
import sys
import ctypes
import sys
from loguru import logger

def run_as_admin():
    """
    请求以管理员权限重新运行程序
    """
    if ctypes.windll.shell32.IsUserAnAdmin():
        logger.trace('当前已是管理员权限')
        return True
    
    # 重新以管理员权限运行
    script = os.path.abspath(sys.argv[0])
    params = ' '.join([f'"{x}"' for x in sys.argv[1:]])
    
    # 调用ShellExecuteW以管理员权限运行
    logger.debug('正在请求管理员权限...')
    ret = ctypes.windll.shell32.ShellExecuteW(
        None, 'runas', sys.executable, f'"{script}" {params}', None, 1)
    
    return ret > 32

def add_to_context_menu():
    """
    将'使用ChameleonFileOps删除(E)'选项添加到系统右键菜单
    """
    if not run_as_admin():
        return False
    
    try:
        # 获取当前脚本路径
        script_path = os.path.abspath(sys.argv[0])
        if script_path.endswith('.py'):
            # 如果是.py文件，使用pythonw.exe来运行
            command = f'"{sys.executable}" "{script_path}" "%1"'
        else:
            # 如果是exe文件，直接运行
            command = f'"{script_path}" "%1"'
        
        # 创建注册表项
        logger.info('开始创建注册表项')
        key = winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, r'*\shell\ChameleonFileOps')
        winreg.SetValue(key, '', winreg.REG_SZ, '使用ChameleonFileOps删除(&E)')
        
        # 创建command子项
        command_key = winreg.CreateKey(key, 'command')
        winreg.SetValue(command_key, '', winreg.REG_SZ, command)
        
        winreg.CloseKey(command_key)
        winreg.CloseKey(key)
        logger.success('右键菜单添加成功')
        return True
    except Exception as e:
        logger.error('添加右键菜单失败 | 异常类型:{}', type(e).__name__, exc_info=True)
        return False

def remove_from_context_menu():
    """
    从系统右键菜单中移除'使用ChameleonFileOps删除(E)'选项
    """
    if not run_as_admin():
        return False
    
    try:
        logger.info('开始移除注册表项')
        winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, r'*\shell\ChameleonFileOps\command')
        winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, r'*\shell\ChameleonFileOps')
        logger.success('右键菜单移除成功')
        return True
    except Exception as e:
        logger.error('移除右键菜单失败 | 异常类型:{}', type(e).__name__, exc_info=True)
        return False