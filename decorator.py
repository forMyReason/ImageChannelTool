import os
import re
import json

import tkinter as tk

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
# 这个类是一个混入类Mixin，用于自动记录和加载Tkinter变量的配置，类的字符串说明了用途
class ConfigDumperMixin(object):
    """ConfigDumperMixin
    自动记录 Tkinter Variable 配置
    """

    loading = False

    @staticmethod
    # 定义静态方法，不需要访问类实例或者类本身的方法属性，因此不需要self或者cls参数
    # 执行完加载config
    def dumper_auto_load(func):
        def wrapper(self, *args, **kwargs):
            res = func(self, *args, **kwargs)
            self.load_config()
            return res

        return wrapper

    @property
    # 用于将类转为只读属性，允许像访问属性一样访问方法，而不需要显式调用它们
    # 如果被按照module导入，__name__是该模块的名称
    # 如果python文件被直接运行，__name__是'__main__'
    # 这就是为什么执行的时候可以用 if __name__ == '__main__' 作为区分当前脚本是否被作为module导入
    def _dumper_config_path(self):
        base = os.path.splitext(os.path.basename(__file__))[0]
            # __file__ 是 Python 中的一个特殊变量，包含当前文件的路径
            # os.path.basename(__file__) 获取当前文件的文件名
            # os.path.splitext(os.path.basename(__file__))[0] 获取文件名（不包含扩展名）
            # os.path.join(tempfile.gettempdir(), path) 获取临时目录路径
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


class MainApplication(ConfigDumperMixin, tk.Frame):
    @ConfigDumperMixin.dumper_auto_load
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)

        self.parent = parent
        parent.title("贴图通道合并工具")

        self.input_path_1 = tk.StringVar()
        self.input_path_1.trace("w", self.dump_config)      # trace用于监视变量的变化，接收两个参数：监视写操作+变量值发生变化时的回调函数
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










if __name__ == "__main__":
    root = tk.Tk()          # 实例化窗口
    MainApplication(root).pack(side="top", expand=True)
    root.mainloop()         # 窗口刷新