# coding:utf-8
"""
自动将 贴图通道进行 融合
"""

# TODO:
from __future__ import unicode_literals, division, print_function

# python元数据，用于描述作者等信息
__author__ = "timmyliang"
__email__ = "820472580@qq.com"
__date__ = "2020-05-12 11:31:30"


import os
import re
import json
import tempfile         # NOTE 临时文件夹
import subprocess
import contextlib
from functools import partial
from PIL import Image   # NOTE PIL 图片处理库

# NOTE Python 3 & 2 兼容
try:
    import tkinter as tk
    from tkinter import ttk
    from tkinter import filedialog, messagebox
except:
    import ttk
    import Tkinter as tk
    import tkFileDialog as filedialog
    import tkMessageBox as messagebox

# TODO:Decorator
def error_log(func):
    def wrapper(*args, **kwargs):
        try:
            # TODO:position arguments & keyword arguments
            res = func(*args, **kwargs)
            return res
        except:
            import traceback
            messagebox.showerror("程序错误", u"程序错误 | 请联系 梁伟添 timmyliang\n\n%s" % traceback.format_exc())
    return wrapper

# 这个类用于自动保存和加载Tkinter变量的配置
class ConfigDumperMixin(object):
    """ConfigDumperMixin
    自动记录 Tkinter Variable 配置
    """

    loading = False

    @staticmethod
    def dumper_auto_load(func):
        def wrapper(self, *args, **kwargs):
            res = func(self, *args, **kwargs)
            self.load_config()
            return res

        return wrapper

    @property
    def _dumper_config_path(self):
        base = os.path.splitext(os.path.basename(__file__))[0]
        path = f"{base}_{self.__class__.__name__}.json"
        path = os.path.join(tempfile.gettempdir(), path)
        return path

    def _dumper_tkinter_varaible(self):
        return [var for var in dir(self) if isinstance(getattr(self, var), tk.Variable)]

    @staticmethod
    def load_deco(func):
        def wrapper(self, *args, **kwargs):
            self.loading = True
            res = func(self, *args, **kwargs)
            self.loading = False
            return res

        return wrapper

    @load_deco.__func__
    def load_config(self, *args, **kwargs):
        path = kwargs.get("path", "")
        path = path if path else self._dumper_config_path
        if not os.path.exists(path):
            return

        with open(path, "r") as f:
            config = json.load(f)
            [getattr(self, var).set(val) for var, val in config.items()]

    def dump_config(self, *args, **kwargs):
        # NOTE 跳过读取阶段的 dump
        if self.loading:
            return

        path = kwargs.get("path", "")
        path = path if path else self._dumper_config_path
        data = {var: getattr(self, var).get() for var in self._dumper_tkinter_varaible()}
        with open(path, "w") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)


class TextWidget(tk.Frame):
    def __init__(self, *args, **kwargs):
        label_text = kwargs.pop("label_text", "")
        path_text = kwargs.pop("path_text", "")
        super(TextWidget, self).__init__(*args, **kwargs)

        self.grid_columnconfigure(1, weight=1)

        if label_text:
            self.label = tk.Label(self, text=label_text)
            self.label.grid(row=0, column=0, sticky="nsew")

        prop = {"width": 25}
        prop.update(
            {"text": path_text}
            if isinstance(path_text, tk.Variable)
            else {"textvariable": path_text}
        )
        self.edit = tk.Entry(self, **prop)
        self.edit.grid(row=0, column=1, sticky="nsew", padx=10)

    # 获取输入框的值
    def get(self):
        return self.edit.get()

    # 设置输入框的值
    def set(self, text):
        self.clear()
        self.edit.insert(0, text)

    def clear(self):
        self.edit.delete(0, tk.END)


class PickPathWidget(TextWidget):
    def __init__(self, *args, **kwargs):
        # 提取参数，如果没有提供，则使用默认值""和self.run_command
        button_text = kwargs.pop("button_text", "")
        button_command = kwargs.pop("button_command", self.run_command)
        super(PickPathWidget, self).__init__(*args, **kwargs)

        btn = tk.Button(self, text=button_text, command=button_command)
        btn.grid(row=0, column=2, sticky="nsew")

    def run_command(self):
        pass

# 通道配置
class ChannelWidget(tk.Frame):
    def __init__(self, *args, **kwargs):
        label_text = kwargs.pop("label_text", "")
        radio_var = kwargs.pop("radio_var", {})
        radio_config = kwargs.pop("radio_config", {})

        # 调用父类tk的Frame初始化方法，传递所有位置参数和关键字参数
        super(ChannelWidget, self).__init__(*args, **kwargs)

        # 配置列的权重
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        self.grid_columnconfigure(2, weight=2)

        self.label = tk.Label(self, text=label_text)
        self.label.grid(row=0, column=0, sticky="nsew")

        for i, (name, val) in enumerate(radio_config.items(), 1):
            radio = tk.Radiobutton(self, text=name, variable=radio_var, value=val)
            radio.grid(row=0, column=i, sticky="nsew")


@contextlib.contextmanager
def TKFrame(*args, **kwargs):
    Frame = tk.Frame(*args)
    yield Frame                 # 暂停函数执行，并返回Frame对象给调用者
    Frame.pack(**kwargs)


@contextlib.contextmanager
def TKLabelFrame(*args, **kwargs):
    frame = kwargs.get("frame", {})     # 获取关键字参数，如果没有，则返回空字典
    pack = kwargs.get("pack", {})
    args = frame.pop("__args__", [])
    args.extend(args)
    Frame = tk.LabelFrame(*args, **frame)
    yield Frame
    Frame.pack(**pack)


class ProgressDialog(tk.Toplevel):

    canceled = False

    def __init__(self, *args, **kwargs):
        self.parent = kwargs.pop("parent", None)
        tk.Toplevel.__init__(self, self.parent, *args, **kwargs)

        # NOTE 阻断其他窗口
        self.grab_set()
        self.progress = ttk.Progressbar(
            self, orient=tk.HORIZONTAL, length=100, mode="determinate"
        )
        self.progress.pack(side="top", fill="x", expand=1, padx=5, pady=5)
        self.button = tk.Button(
            self, text="Cancel", command=lambda: [None for self.canceled in [True]]
        )
        self.button.pack()

    @classmethod
    def loop(cls, seq, **kwargs):
        self = cls(**kwargs)
        maximum = len(seq)
        for i, item in enumerate(seq):
            if self.canceled:
                break

            try:
                yield i, item  # with body executes here
            except:
                import traceback

                traceback.print_exc()
                self.destroy()

            self.progress["value"] = i / maximum * 100
            self.update()

        self.destroy()

# 这个类继承自configDumperMixin，继承了ConfigDumperMixin 和 tk.Frame，实现了图形界面和图像通道合并的主要逻辑。
class MainApplication(ConfigDumperMixin, tk.Frame):
    @ConfigDumperMixin.dumper_auto_load
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)

        self.parent = parent
        parent.title("贴图通道合并工具")

        self.input_path_1 = tk.StringVar()
        self.input_path_1.trace("w", self.dump_config)
        self.input_path_2 = tk.StringVar()
        self.input_path_2.trace("w", self.dump_config)
        self.output_path = tk.StringVar()
        self.output_path.trace("w", self.dump_config)

        pack_config = {"side": "top", "fill": "x", "padx": 5, "pady": 5}
        with TKLabelFrame(
            frame={"text": "目录输入输出"},
            pack=pack_config,
        ) as Frame:
            config = {
                "label_text": "第一种贴图目录",
                "path_text": self.input_path_1,
                "button_text": "选择路径",
                "button_command": partial(self.choose_directory, self.input_path_1),
            }
            PickPathWidget(Frame, **config).pack(
                side="top", fill="both", padx=5, pady=5
            )
            config.update(
                {
                    "label_text": "第二种贴图目录",
                    "path_text": self.input_path_2,
                    "button_command": partial(self.choose_directory, self.input_path_2),
                }
            )
            PickPathWidget(Frame, **config).pack(
                side="top", fill="both", padx=5, pady=5
            )
            config.update(
                {
                    "label_text": "合成贴图输出目录",
                    "path_text": self.output_path,
                    "button_command": partial(self.choose_directory, self.output_path),
                }
            )
            PickPathWidget(Frame, **config).pack(
                side="top", fill="both", padx=5, pady=5
            )

        self.R = tk.StringVar(self, "1")
        self.R.trace("w", self.dump_config)
        self.G = tk.StringVar(self, "1")
        self.G.trace("w", self.dump_config)
        self.B = tk.StringVar(self, "1")
        self.B.trace("w", self.dump_config)
        self.A = tk.StringVar(self, "1")
        self.A.trace("w", self.dump_config)

        with TKLabelFrame(
            frame={"text": "通道配置"},
            pack=pack_config,
        ) as Frame:
            raido_conifg = {
                "第一种": "1",
                "第二种": "2",
            }
            ChannelWidget(
                Frame,
                label_text="R 通道",
                radio_var=self.R,
                radio_config=raido_conifg,
            ).pack(side="top", fill="both", padx=5, pady=5)

            ChannelWidget(
                Frame,
                label_text="G 通道",
                radio_var=self.G,
                radio_config=raido_conifg,
            ).pack(side="top", fill="both", padx=5, pady=5)

            ChannelWidget(
                Frame,
                label_text="B 通道",
                radio_var=self.B,
                radio_config=raido_conifg,
            ).pack(side="top", fill="both", padx=5, pady=5)

            ChannelWidget(
                Frame,
                label_text="A 通道",
                radio_var=self.A,
                radio_config=raido_conifg,
            ).pack(side="top", fill="both", padx=5, pady=5)

        self.image_extension = tk.StringVar(self, "png")

        with TKLabelFrame(
            frame={"text": "输出配置"},
            pack=pack_config,
        ) as Frame:
            # NOTE 配置 输出的图片 通道
            config = {
                "label_text": "输出格式",
                "path_text": self.image_extension,
            }
            TextWidget(Frame, **config).pack(side="top", fill="both", padx=5, pady=5)

        with TKFrame(**pack_config) as Frame:
            gen_btn = tk.Button(Frame, text="合并贴图", command=self.img_combine)
            gen_btn.pack(side="top", fill="x", padx=5)

    def choose_directory(self, var):
        directory = filedialog.askdirectory()
        if not directory:
            return
        elif not os.path.exists(directory):
            messagebox.showwarning("警告", "选择的路径不存在")
            return
        var.set(directory)

    @error_log
    def img_combine(self):
        output_path = self.output_path.get()
        input_path_1 = self.input_path_1.get()
        input_path_2 = self.input_path_2.get()
        if not os.path.exists(output_path):
            self.output_path.set("")
            messagebox.showwarning("警告", "输出路径不存在")
            return
        elif not os.path.exists(input_path_1):
            self.self.input_path_1.set("")
            messagebox.showwarning("警告", "第一种贴图路径不存在")
            return
        elif not os.path.exists(input_path_2):
            self.input_path_2.set("")
            messagebox.showwarning("警告", "第二种贴图路径不存在")
            return

        # NOTE 匹配图片命名序号
        regx = re.compile(r".*?(\d+)\..*?$")
        # .*? 匹配任意数量的任意字符，但尽可能少的匹配
            # . 匹配单个字符
            # * 匹配 前面 字符任意次（包括0次）
            # ? 非贪婪模式，尽可能少的匹配字符
        # (\d+) 匹配一个或多个连续的数组，并且这些数字被捕获到一个组
            # \d 匹配数字0-9
            # + 匹配前面字符一次或多次
            #() 捕获组，用于提取匹配的子字符串
        # \. 匹配一个点字符，反斜杠作为转义字符
        # $ 匹配字符串结尾
        input_path_1_dict = {
            regx.search(f).group(1): os.path.join(input_path_1, f) for f in os.listdir(input_path_1) if regx.search(f)
        }
        for i, img in ProgressDialog.loop(os.listdir(input_path_2)):
            match = regx.search(img)
            if not match:
                continue
            num = match.group(1)

            img_1 = input_path_1_dict.get(num, "")
            img_2 = os.path.join(input_path_2, img)
            if not os.path.exists(img_1):
                continue

            img_1 = Image.open(img_1).convert("RGBA")
            img_2 = Image.open(img_2).convert("RGBA")

            r_1, g_1, b_1, a_1 = img_1.split()
            r_2, g_2, b_2, a_2 = img_2.split()

            R = r_1 if self.R.get() == "1" else r_2
            G = g_1 if self.G.get() == "1" else g_2
            B = b_1 if self.B.get() == "1" else b_2
            A = a_1 if self.A.get() == "1" else a_2

            image = Image.merge("RGBA", [R, G, B, A])

            img = os.path.splitext(img)[0]
            ext = self.image_extension.get()
            image.save(os.path.join(output_path, f"{img}.{ext}"))

        messagebox.showinfo("恭喜您", "合并完成")
        subprocess.Popen(["start", "", output_path], shell=True)


if __name__ == "__main__":
    root = tk.Tk()          # 实例化窗口
    MainApplication(root).pack(side="top", expand=True)
    root.mainloop()         # 窗口刷新
